"""Foreground execution for one configured pipeline.

This module is the low-latency counterpart to the local HTTP control plane.  It
uses the same config, application compiler, frozen deployment, and interpreter,
but invokes effects in the caller's process.  There is no PostgreSQL, Temporal,
HTTP control-plane hop, release lifecycle, or durable retry boundary.
"""

from __future__ import annotations

import asyncio
import inspect
import math
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Literal, Mapping, Optional, cast

from .app import Application, CompiledPipeline, PipelineSpec
from .dotctx import Reasoner
from .errors import JulepError
from .execution.effects import LlmCaller, RunPrincipal, WorkerContext
from .execution.llm_result import LlmCallMeta, LlmResult, LlmUsage
from .projection import InMemoryProjection, ProjectionSink
from .ir import (
    EMIT_TOOL,
    HUMAN_GATE_TOOL,
    RECV_TOOL,
    SLEEP_TOOL,
    Ann,
    CallStep,
    McpTool,
    NativeTool,
    SubStep,
    ThinkStep,
)
from .kinds import ContextScope, Op
from .model_slugs import normalize_model_slug
from .prompt import rendered_reasoner_for
from .qos import QoSTier, ReasonerDispatch
from .registry import DEFAULT_REGISTRY
from .resilience import AttemptRecord, classify_error

if TYPE_CHECKING:
    from .cli.config import JulepConfig


_JULEP_META_KEY = "__julep_meta__"
_LOCAL_UNSUPPORTED_NATIVE_TOOLS = frozenset(
    {HUMAN_GATE_TOOL, SLEEP_TOOL, RECV_TOOL, EMIT_TOOL}
)


class LocalPipelineError(JulepError):
    """Base error for configured foreground execution."""


class LocalPipelineNotFound(LocalPipelineError):
    """The selected environment or pipeline does not exist."""

    def __init__(self, kind: str, name: str, available: list[str]) -> None:
        self.kind = kind
        self.name = name
        self.available = tuple(available)
        choices = ", ".join(available) if available else "none"
        super().__init__(f"unknown {kind} {name!r}; configured {kind}s: {choices}")


class LocalExecutionConfigurationError(LocalPipelineError):
    """Foreground execution is missing an explicitly injected effect."""


class LocalExecutionUnsupported(LocalPipelineError):
    """A durable/session-only operator was selected for foreground execution."""


ReasonerHandler = Callable[[Any], Awaitable[Any]]
EmbeddedCostStatus = Literal["reported", "derived", "mixed", "unknown"]


@dataclass(frozen=True)
class EmbeddedRun:
    """One embedded execution with aggregate LLM usage and price metadata."""

    value: Any
    projection: InMemoryProjection
    artifact_hash: str
    usage: LlmUsage = LlmUsage()
    usage_complete: bool = False
    total_cost: Optional[float] = None
    cost_status: EmbeddedCostStatus = "unknown"
    cost_complete: bool = False


def _token(value: Any) -> Optional[int]:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _price(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    price = float(value)
    return price if math.isfinite(price) and price >= 0 else None


def _embedded_llm_totals(
    calls: list[LlmCallMeta],
) -> tuple[LlmUsage, bool, Optional[float], EmbeddedCostStatus, bool]:
    """Aggregate model-call metadata observed by one embedded invocation."""

    if not calls:
        return LlmUsage(), False, None, "unknown", False

    prompt: list[Optional[int]] = []
    completion: list[Optional[int]] = []
    total: list[Optional[int]] = []
    cache_read: list[Optional[int]] = []
    cache_creation: list[Optional[int]] = []
    costs: list[Optional[float]] = []
    statuses: list[Literal["reported", "derived", "unknown"]] = []
    for meta in calls:
        usage = meta.resolved_usage()
        leg_prompt = _token(usage.prompt_tokens)
        leg_completion = _token(usage.completion_tokens)
        leg_total = _token(usage.total_tokens)
        if leg_total is None and leg_prompt is not None and leg_completion is not None:
            leg_total = leg_prompt + leg_completion
        prompt.append(leg_prompt)
        completion.append(leg_completion)
        total.append(leg_total)

        cache_read.append(_token(usage.cache_read_tokens))
        cache_creation.append(_token(usage.cache_creation_tokens))

        statuses.append(meta.resolved_cost_status())
        costs.append(_price(meta.cost))

    def complete_sum(values: list[Optional[int]]) -> Optional[int]:
        return (
            sum(cast(int, value) for value in values)
            if all(value is not None for value in values)
            else None
        )

    aggregate_usage = LlmUsage(
        prompt_tokens=complete_sum(prompt),
        completion_tokens=complete_sum(completion),
        total_tokens=complete_sum(total),
        cache_read_tokens=complete_sum(cache_read),
        cache_creation_tokens=complete_sum(cache_creation),
    )
    usage_complete = all(
        value is not None for values in (prompt, completion, total) for value in values
    )
    cost_complete = all(
        status != "unknown" and cost is not None
        for status, cost in zip(statuses, costs, strict=True)
    )
    if len(set(statuses)) == 1:
        cost_status: EmbeddedCostStatus = statuses[0]
    else:
        cost_status = "mixed"
    total_cost = sum(cast(float, cost) for cost in costs) if cost_complete else None
    return aggregate_usage, usage_complete, total_cost, cost_status, cost_complete


@dataclass(frozen=True)
class LocalPipeline:
    """One compiled configured pipeline reusable across foreground calls."""

    name: str
    environment: str
    compiled: CompiledPipeline[Any, Any]
    reasoners: Mapping[str, Reasoner]
    configured_llm: Optional[LlmCaller] = None

    @property
    def artifact_hash(self) -> str:
        """The frozen deployment identity used by every call on this object."""

        return self.compiled.deployment.artifact_hash

    async def arun(
        self,
        input: Any = None,
        *,
        llm: Optional[LlmCaller] = None,
        context: Optional[WorkerContext] = None,
        principal: Optional[RunPrincipal] = None,
        sink: Optional[ProjectionSink] = None,
        run_id: Optional[str] = None,
    ) -> Any:
        """Execute in-process and return the interpreter's unwrapped value."""

        return (await self.arun_detailed(
            input,
            llm=llm,
            context=context,
            principal=principal,
            sink=sink,
            run_id=run_id,
        )).value

    async def arun_detailed(
        self,
        input: Any = None,
        *,
        llm: Optional[LlmCaller] = None,
        context: Optional[WorkerContext] = None,
        principal: Optional[RunPrincipal] = None,
        sink: Optional[ProjectionSink] = None,
        projection: Optional[InMemoryProjection] = None,
        run_id: Optional[str] = None,
    ) -> EmbeddedRun:
        """Execute in-process and return its value, projection, and artifact hash.

        Pass a caller-owned ``projection`` to retain failure events when execution
        raises. A synchronous ``sink`` receives live events and fails loudly.
        """

        worker = context if context is not None else WorkerContext()
        caller = llm if llm is not None else worker.llm
        if caller is None:
            caller = self.configured_llm
        if self.reasoners and caller is None:
            raise LocalExecutionConfigurationError(
                f"pipeline {self.name!r} invokes a reasoner; pass llm= or "
                "WorkerContext(llm=...), or configure [tool.julep] llm_caller"
            )

        deployment = self.compiled.deployment
        deployment.assert_artifact_integrity()
        _assert_foreground_supported(deployment.flow)

        llm_calls: list[LlmCallMeta] = []
        reasoner_handlers = _reasoner_handlers(
            deployment.flow,
            self.reasoners,
            caller=caller,
            context=worker,
            principal=principal,
            observed_calls=llm_calls,
        )
        mcp_backed = any(
            isinstance(tool.ref, McpTool) for tool in deployment.manifest.values()
        )
        if mcp_backed and worker.mcp_call is None:
            raise LocalExecutionConfigurationError(
                f"pipeline {self.name!r} invokes MCP tools; pass "
                "WorkerContext(mcp_call=...)"
            )

        # Snapshot-only deployments intentionally require a native-tool binding
        # for the legacy ``Deployment.dry_run`` API.  A configured reasoner-only
        # pipeline has no native calls to bind, so make that empty binding
        # explicit on a copy without mutating the frozen deployment.
        has_native_tool = any(
            isinstance(tool.ref, NativeTool) for tool in deployment.manifest.values()
        )
        local_deployment = (
            deployment
            if deployment._tools is not None or mcp_backed or has_native_tool
            else replace(deployment, _tools=())
        )
        policy = self.compiled.spec.execution_policy
        run_projection = projection if projection is not None else InMemoryProjection()
        result = await local_deployment.adry_run(
            input,
            mcp_call=worker.mcp_call,
            reasoners=reasoner_handlers,
            principal=principal,
            registry=worker.registry,
            max_parallel=None if policy is None else policy.max_parallel,
            projection=run_projection,
            sink=sink,
            run_id=run_id,
            trajectory_sink=worker.trajectory_sink,
            trajectory_blob_store=worker.trajectory_blob_store or worker.blob_store,
            redactor=worker.redactor,
        )
        usage, usage_complete, total_cost, cost_status, cost_complete = _embedded_llm_totals(
            llm_calls
        )
        return EmbeddedRun(
            result.value,
            run_projection,
            self.artifact_hash,
            usage=usage,
            usage_complete=usage_complete,
            total_cost=total_cost,
            cost_status=cost_status,
            cost_complete=cost_complete,
        )

    def run(
        self,
        input: Any = None,
        *,
        llm: Optional[LlmCaller] = None,
        context: Optional[WorkerContext] = None,
        principal: Optional[RunPrincipal] = None,
        sink: Optional[ProjectionSink] = None,
        run_id: Optional[str] = None,
    ) -> Any:
        """Synchronous foreground execution; use :meth:`arun` in an event loop."""

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            raise LocalExecutionConfigurationError(
                "LocalPipeline.run() cannot run inside an active event loop; "
                "await LocalPipeline.arun() instead"
            )
        return asyncio.run(
            self.arun(
                input,
                llm=llm,
                context=context,
                principal=principal,
                sink=sink,
                run_id=run_id,
            )
        )

    def run_detailed(
        self,
        input: Any = None,
        *,
        llm: Optional[LlmCaller] = None,
        context: Optional[WorkerContext] = None,
        principal: Optional[RunPrincipal] = None,
        sink: Optional[ProjectionSink] = None,
        projection: Optional[InMemoryProjection] = None,
        run_id: Optional[str] = None,
    ) -> EmbeddedRun:
        """Synchronous mirror of :meth:`arun_detailed`."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            raise LocalExecutionConfigurationError(
                "LocalPipeline.run_detailed() cannot run inside an active event loop; "
                "await LocalPipeline.arun_detailed() instead"
            )
        return asyncio.run(self.arun_detailed(
            input, llm=llm, context=context, principal=principal,
            sink=sink, projection=projection, run_id=run_id,
        ))


def prepare_local_pipeline(
    pipeline: str,
    *,
    project_root: str | Path = ".",
    config: Optional[JulepConfig] = None,
    env: str = "local",
) -> LocalPipeline:
    """Load and compile one configured pipeline for repeated foreground calls."""

    from .cli.application import resolve_application
    from .cli.config import load_config

    cfg = config or load_config(project_root)
    if env not in cfg.envs:
        raise LocalPipelineNotFound("environment", env, sorted(cfg.envs))
    env_config = cfg.envs[env]
    application = resolve_application(cfg, env_config)
    matches = [spec for spec in application.pipelines if spec.name == pipeline]
    if not matches:
        raise LocalPipelineNotFound(
            "pipeline",
            pipeline,
            sorted(spec.name for spec in application.pipelines),
        )

    # Compile only the selected pipeline.  This preserves its normal application
    # compilation gates while keeping unrelated MCP surfaces off the foreground
    # startup path.
    configured_llm = None
    if cfg.llm_caller is not None:
        from ._specload import resolve_spec

        configured_llm = cast(LlmCaller, resolve_spec(cfg.llm_caller, what="llm caller"))
    return _local_pipeline_from_spec(
        matches[0], application_name=application.name, environment=env,
        env_vars={**env_config.vars, **env_config.worker_environment},
        configured_llm=configured_llm,
    )


def _local_pipeline_from_spec(
    spec: PipelineSpec[Any, Any],
    *,
    application_name: str,
    environment: str,
    env_vars: Mapping[str, str],
    configured_llm: Optional[LlmCaller] = None,
) -> LocalPipeline:
    """Compile one selected spec into the shared embedded execution surface."""
    selected = Application(application_name, (spec,))
    compiled_application = selected.compile_live(env_vars=env_vars)
    compiled = compiled_application.pipelines[0]
    reasoners = _resolve_pipeline_reasoners(compiled)
    return LocalPipeline(
        name=spec.name,
        environment=environment,
        compiled=compiled,
        reasoners=MappingProxyType(dict(reasoners)),
        configured_llm=configured_llm,
    )


async def arun_local_pipeline(
    pipeline: str,
    input: Any = None,
    *,
    project_root: str | Path = ".",
    config: Optional[JulepConfig] = None,
    env: str = "local",
    llm: Optional[LlmCaller] = None,
    context: Optional[WorkerContext] = None,
    principal: Optional[RunPrincipal] = None,
    run_id: Optional[str] = None,
) -> Any:
    """Compile and execute one configured pipeline in the current event loop."""

    prepared = prepare_local_pipeline(
        pipeline,
        project_root=project_root,
        config=config,
        env=env,
    )
    return await prepared.arun(
        input, llm=llm, context=context, principal=principal, run_id=run_id
    )


def run_local_pipeline(
    pipeline: str,
    input: Any = None,
    *,
    project_root: str | Path = ".",
    config: Optional[JulepConfig] = None,
    env: str = "local",
    llm: Optional[LlmCaller] = None,
    context: Optional[WorkerContext] = None,
    principal: Optional[RunPrincipal] = None,
    run_id: Optional[str] = None,
) -> Any:
    """Compile and synchronously execute one configured pipeline in-process."""

    prepared = prepare_local_pipeline(
        pipeline,
        project_root=project_root,
        config=config,
        env=env,
    )
    return prepared.run(
        input, llm=llm, context=context, principal=principal, run_id=run_id
    )


def _resolve_pipeline_reasoners(
    compiled: CompiledPipeline[Any, Any],
) -> dict[str, Reasoner]:
    inline = {
        declaration.name: declaration
        for declaration in compiled.spec.reasoners
        if isinstance(declaration, Reasoner)
    }
    names = set(compiled.spec.reasoner_names)
    for node in compiled.deployment.flow.walk():
        if isinstance(node.step, ThinkStep):
            names.add(node.step.reasoner)
        if node.controller is not None:
            names.add(node.controller)
        if node.summarizer is not None:
            names.add(node.summarizer)

    resolved: dict[str, Reasoner] = {}
    for name in sorted(names):
        reasoner = inline.get(name)
        if reasoner is None:
            reasoner = DEFAULT_REGISTRY.reasoners.get(name)
        if reasoner is None:
            raise LocalExecutionConfigurationError(
                f"pipeline {compiled.spec.name!r} references unknown reasoner {name!r}"
            )
        resolved[name] = reasoner
    return resolved


def _assert_foreground_supported(flow: Any) -> None:
    for node in flow.walk():
        if node.op is Op.LOOP:
            raise LocalExecutionUnsupported(
                "foreground execution does not support session LOOP flows; "
                "use the local API or a durable worker"
            )
        if node.op is Op.EVAL_PLAN:
            raise LocalExecutionUnsupported(
                "foreground execution does not support staged plans; use the local API"
            )
        if (
            node.op is Op.APP
            and node.ctx is not None
            and node.ctx.scope in {ContextScope.WHOLE_SESSION, ContextScope.SUMMARY}
        ):
            raise LocalExecutionUnsupported(
                "foreground execution does not support transcript-scoped agents; "
                "use the local API or a durable worker"
            )
        if node.op is Op.APP and node.subflows:
            raise LocalExecutionUnsupported(
                "foreground execution does not resolve agent subflows; use the "
                "local API or a durable worker"
            )
        if isinstance(node.step, SubStep):
            raise LocalExecutionUnsupported(
                "foreground execution does not resolve subflows; use the local API "
                "or a durable worker"
            )
        if (
            isinstance(node.step, CallStep)
            and isinstance(node.step.tool, NativeTool)
            and node.step.tool.name in _LOCAL_UNSUPPORTED_NATIVE_TOOLS
        ):
            raise LocalExecutionUnsupported(
                f"foreground execution does not support reserved effect "
                f"{node.step.tool.name!r}; use the local API or a durable worker"
            )


def _foreground_attempt(
    reasoner: Reasoner,
    *,
    outcome: str,
    dispatch: ReasonerDispatch,
    detail: str = "",
) -> AttemptRecord:
    normalized = normalize_model_slug(reasoner.model).model
    provider, separator, _ = normalized.partition(":")
    return AttemptRecord(
        model=normalized,
        provider=provider if separator else "",
        outcome=outcome,
        detail=detail,
        tier=dispatch.qos.value,
        batch_id=dispatch.batch_id,
    )


def _notify_foreground_attempts(
    context: WorkerContext,
    reasoner: Reasoner,
    raw: Any,
    dispatch: ReasonerDispatch,
) -> None:
    notify = context.on_attempt
    if notify is None:
        return
    if isinstance(raw, LlmResult) and raw.meta.attempts:
        for attempt in raw.meta.attempts:
            notify(
                AttemptRecord(
                    model=attempt.model,
                    provider=attempt.provider,
                    outcome=attempt.outcome,
                    tier=dispatch.qos.value,
                    batch_id=dispatch.batch_id,
                )
            )
        return
    notify(_foreground_attempt(reasoner, outcome="ok", dispatch=dispatch))


def _reasoner_handlers(
    flow: Any,
    prepared_reasoners: Mapping[str, Reasoner],
    *,
    caller: Optional[LlmCaller],
    context: WorkerContext,
    principal: Optional[RunPrincipal],
    observed_calls: list[LlmCallMeta],
) -> dict[str, ReasonerHandler]:
    if caller is None:
        return {}

    reasoners = dict(prepared_reasoners)
    caller_attempt_sink = getattr(caller, "__julep_on_attempt__", None)
    caller_owns_attempts = caller_attempt_sink is not None and (
        caller_attempt_sink is context.on_attempt
        or caller_attempt_sink == context.on_attempt
    )
    if context.registry is not None:
        for name, reasoner in reasoners.items():
            override = context.registry.reasoners.get(name)
            if override is not None and override != reasoner:
                raise LocalExecutionConfigurationError(
                    f"WorkerContext reasoner {name!r} differs from the configured "
                    "pipeline's compiled declaration"
                )

    ordinary_reasoners = {
        node.step.reasoner
        for node in flow.walk()
        if isinstance(node.step, ThinkStep)
    }
    controller_tools: dict[str, tuple[dict[str, Any], ...]] = {}
    for node in flow.walk():
        if node.op is not Op.APP or node.controller is None:
            continue
        definitions = (
            tuple(dict(definition) for definition in (node.tool_defs or ()))
            if node.native_tools
            else ()
        )
        previous = controller_tools.get(node.controller)
        if node.controller in controller_tools and previous != definitions:
            raise LocalExecutionConfigurationError(
                f"reasoner {node.controller!r} is used by foreground agents with "
                "different frozen tool surfaces"
            )
        controller_tools[node.controller] = definitions

    for name in sorted(ordinary_reasoners & controller_tools.keys()):
        if controller_tools[name]:
            raise LocalExecutionConfigurationError(
                f"reasoner {name!r} is used by both ordinary foreground reasoning "
                "and a native-tool agent; use separate reasoner names"
            )

    async def invoke_named(
        name: str,
        value: Any,
        *,
        tool_defs: tuple[dict[str, Any], ...] = (),
    ) -> Any:
        reasoner = reasoners.get(name)
        if reasoner is None:
            raise LocalExecutionConfigurationError(
                f"foreground pipeline references unknown reasoner {name!r}"
            )
        rendered = rendered_reasoner_for(reasoner, value)
        dispatch = _foreground_dispatch(rendered, context, principal)
        if tool_defs and not _accepts_keyword(caller, "tools"):
            raise LocalExecutionConfigurationError(
                f"pipeline reasoner {name!r} uses native tool calling, but its "
                "LlmCaller does not accept the optional tools= keyword extension"
            )
        try:
            if tool_defs:
                raw = await cast(Any, caller)(
                    rendered,
                    value,
                    principal,
                    None,
                    dispatch,
                    tools=list(tool_defs),
                )
            else:
                raw = await caller(rendered, value, principal, None, dispatch)
        except Exception as exc:
            if context.on_attempt is not None and not caller_owns_attempts:
                context.on_attempt(
                    _foreground_attempt(
                        rendered,
                        outcome=classify_error(exc).value,
                        detail=str(exc),
                        dispatch=dispatch,
                    )
                )
            raise
        if isinstance(raw, LlmResult):
            observed_calls.append(raw.meta)
        if not caller_owns_attempts:
            _notify_foreground_attempts(context, rendered, raw, dispatch)
        return _pack_reasoner_result(raw)

    handlers: dict[str, ReasonerHandler] = {}
    for name in reasoners:
        tools = controller_tools.get(name, ())

        async def handler(
            value: Any,
            *,
            _name: str = name,
            _tools: tuple[dict[str, Any], ...] = tools,
        ) -> Any:
            return await invoke_named(_name, value, tool_defs=_tools)

        handlers[name] = handler
    return handlers


def _foreground_dispatch(
    reasoner: Reasoner,
    context: WorkerContext,
    principal: Optional[RunPrincipal],
) -> ReasonerDispatch:
    tier = QoSTier(context.resolve_qos(reasoner, Ann(batchable=False), principal))
    # BATCH needs a durable submit/wait boundary.  Foreground calls use the same
    # non-batchable clamp as the durable resolver.
    if tier is QoSTier.BATCH:
        tier = QoSTier.FLEX
    return ReasonerDispatch(qos=tier)


def _accepts_keyword(fn: Callable[..., Any], keyword: str) -> bool:
    try:
        signature = inspect.signature(fn)
    except (TypeError, ValueError):
        return True
    if any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    ):
        return True
    parameter = signature.parameters.get(keyword)
    return parameter is not None and parameter.kind in {
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.KEYWORD_ONLY,
    }


def _pack_reasoner_result(raw: Any) -> Any:
    if not isinstance(raw, LlmResult):
        return raw
    attrs = raw.meta.to_attrs()
    if not attrs:
        return raw.reply
    return {"reply": raw.reply, _JULEP_META_KEY: attrs}


__all__ = [
    "LocalExecutionConfigurationError",
    "LocalExecutionUnsupported",
    "LocalPipeline",
    "LocalPipelineError",
    "LocalPipelineNotFound",
    "EmbeddedRun",
    "arun_local_pipeline",
    "prepare_local_pipeline",
    "run_local_pipeline",
]
