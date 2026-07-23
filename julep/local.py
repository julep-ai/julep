"""Foreground execution for one configured pipeline.

This module is the low-latency counterpart to the local HTTP control plane.  It
uses the same config, application compiler, frozen deployment, and interpreter,
but invokes effects in the caller's process.  There is no PostgreSQL, Temporal,
HTTP control-plane hop, release lifecycle, or durable retry boundary.
"""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Mapping, Optional, cast

from .app import Application, CompiledPipeline
from .dotctx import Reasoner
from .errors import JulepError
from .execution.effects import LlmCaller, RunPrincipal, WorkerContext
from .execution.llm_result import LlmResult
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
from .prompt import rendered_reasoner_for
from .qos import QoSTier, ReasonerDispatch
from .registry import DEFAULT_REGISTRY

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


@dataclass(frozen=True)
class LocalPipeline:
    """One compiled configured pipeline reusable across foreground calls."""

    name: str
    environment: str
    compiled: CompiledPipeline[Any, Any]
    reasoners: Mapping[str, Reasoner]

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
    ) -> Any:
        """Execute in-process and return the interpreter's unwrapped value."""

        worker = context or WorkerContext()
        caller = llm or worker.llm
        if self.reasoners and caller is None:
            raise LocalExecutionConfigurationError(
                f"pipeline {self.name!r} invokes a reasoner; pass llm= or "
                "WorkerContext(llm=...)"
            )

        deployment = self.compiled.deployment
        deployment.assert_artifact_integrity()
        _assert_foreground_supported(deployment.flow)

        reasoner_handlers = _reasoner_handlers(
            deployment.flow,
            self.reasoners,
            caller=caller,
            context=worker,
            principal=principal,
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
        result = await local_deployment.adry_run(
            input,
            mcp_call=worker.mcp_call,
            reasoners=reasoner_handlers,
            principal=principal,
            registry=worker.registry,
            max_parallel=None if policy is None else policy.max_parallel,
        )
        return result.value

    def run(
        self,
        input: Any = None,
        *,
        llm: Optional[LlmCaller] = None,
        context: Optional[WorkerContext] = None,
        principal: Optional[RunPrincipal] = None,
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
            self.arun(input, llm=llm, context=context, principal=principal)
        )


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
    selected = Application(application.name, (matches[0],))
    compiled_application = selected.compile_live(
        env_vars={**env_config.vars, **env_config.worker_environment}
    )
    compiled = compiled_application.pipelines[0]
    reasoners = _resolve_pipeline_reasoners(compiled)
    return LocalPipeline(
        name=pipeline,
        environment=env,
        compiled=compiled,
        reasoners=MappingProxyType(dict(reasoners)),
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
) -> Any:
    """Compile and execute one configured pipeline in the current event loop."""

    prepared = prepare_local_pipeline(
        pipeline,
        project_root=project_root,
        config=config,
        env=env,
    )
    return await prepared.arun(input, llm=llm, context=context, principal=principal)


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
) -> Any:
    """Compile and synchronously execute one configured pipeline in-process."""

    prepared = prepare_local_pipeline(
        pipeline,
        project_root=project_root,
        config=config,
        env=env,
    )
    return prepared.run(input, llm=llm, context=context, principal=principal)


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


def _reasoner_handlers(
    flow: Any,
    prepared_reasoners: Mapping[str, Reasoner],
    *,
    caller: Optional[LlmCaller],
    context: WorkerContext,
    principal: Optional[RunPrincipal],
) -> dict[str, ReasonerHandler]:
    if caller is None:
        return {}

    reasoners = dict(prepared_reasoners)
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
        if tool_defs:
            if not _accepts_keyword(caller, "tools"):
                raise LocalExecutionConfigurationError(
                    f"pipeline reasoner {name!r} uses native tool calling, but its "
                    "LlmCaller does not accept the optional tools= keyword extension"
                )
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
    "arun_local_pipeline",
    "prepare_local_pipeline",
    "run_local_pipeline",
]
