"""Service-free control-plane application and execution gateway.

Local mode intentionally preserves the HTTP release/run lifecycle while replacing
PostgreSQL and Temporal with process-local implementations.  It is a development
surface, not a durability backend.
"""

from __future__ import annotations

import asyncio
import inspect
import ipaddress
import os
import secrets as _secrets
import threading
import time
import uuid
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from fastapi import FastAPI

from ..app_deploy import PipelineRelease
from ..artifact_store import LocalDirArtifactStore
from ..continuation import continuation_value, is_continuation
from ..contracts import manifest_from_json
from ..execution import effects
from ..execution.effects import (
    CallToolInput,
    CompilePlanInput,
    InvokeReasonerInput,
    VerifyPuresInput,
    WorkerContext,
    toolref_json_from_key,
)
from ..execution.harness import preflightMcp
from ..execution.interpreter import InMemoryEnv, Result, call_ref_key, interpret
from ..execution.policy import ExecutionPolicy
from ..execution.projection_store import (
    ExecutionStore,
    InMemoryExecutionStore,
    _capture_value,
    _normalise_event,
    _redact_projection_metadata,
)
from ..ir import CallStep, EMIT_TOOL, NativeTool, Node, RECV_TOOL, SubStep, toolref_key
from ..kinds import Op
from ..projection import (
    EventType,
    InMemoryProjection,
    ProjectionEmitter,
    ProjectionEvent,
    ProjectionSink,
    TeeStore,
)
from ..registry import DEFAULT_REGISTRY, Registry
from ..secrets import VaultCipher
from .app import create_app
from .auth import ApiKey, KeyRing
from .settings import ServerSettings

ContextFactory = str | Callable[[], WorkerContext | Any]


_PROCESS_STATE_LOCK = threading.Lock()
_PROCESS_STATE_OWNER: object | None = None


def _claim_process_state(owner: object) -> None:
    """Reserve the process-wide effect and artifact configuration for one app."""

    global _PROCESS_STATE_OWNER
    with _PROCESS_STATE_LOCK:
        if _PROCESS_STATE_OWNER is not None:
            raise RuntimeError(
                "only one local Julep app lifespan may run in a process at a time"
            )
        _PROCESS_STATE_OWNER = owner


def _release_process_state(owner: object) -> None:
    global _PROCESS_STATE_OWNER
    with _PROCESS_STATE_LOCK:
        if _PROCESS_STATE_OWNER is owner:
            _PROCESS_STATE_OWNER = None


class _ExecutionProjectionSink(ProjectionSink):
    """Persist interpreter events immediately through the control-plane store."""

    def __init__(
        self,
        store: ExecutionStore,
        projection: InMemoryProjection,
        *,
        run_id: str,
        workflow_id: str,
        segment_seq: int,
        secrets: Optional[Mapping[str, str]],
    ) -> None:
        self._store = store
        self._projection = projection
        self._run_id = run_id
        self._workflow_id = workflow_id
        self._segment_seq = segment_seq
        self._secrets = secrets

    def append(self, event: ProjectionEvent) -> None:
        candidate = event.to_json()
        captured = None
        if event.value_ref is not None:
            captured = _capture_value(
                self._projection.values.get(event.value_ref), self._secrets
            )
        candidate = _redact_projection_metadata(candidate, self._secrets)
        persisted_ref = None if captured is None else captured.value_ref
        if captured is not None:
            self._store.put_value(
                captured.value_ref,
                captured.payload,
                captured.byte_len,
                captured.oversize,
            )
        self._store.insert_events(
            [
                _normalise_event(
                    candidate,
                    run_id=self._run_id,
                    workflow_id=self._workflow_id,
                    segment_seq=self._segment_seq,
                    value_ref=persisted_ref,
                )
            ]
        )


@dataclass
class _LocalRun:
    run_id: str
    workflow_id: str
    local_run_id: str
    task: Optional[asyncio.Task[None]] = None
    stop_status: Optional[str] = None
    status: str = "running"
    segment_seq: int = 0
    projection: Optional[InMemoryProjection] = None

    def __post_init__(self) -> None:
        self.open_gates: dict[str, asyncio.Future[Any]] = {}
        self.early_signals: dict[str, Any] = {}


def _echo_tools(flow: Node) -> dict[str, Callable[[Any], Any]]:
    return {toolref_key(ref): lambda value: value for ref in flow.tool_refs()}


def _echo_reasoners(flow: Node) -> dict[str, Callable[[Any], Any]]:
    names: set[str] = set()
    for node in flow.walk():
        reasoner = getattr(node.step, "reasoner", None)
        if isinstance(reasoner, str):
            names.add(reasoner)
        if node.op in {Op.APP, Op.EVAL_PLAN} and node.controller is not None:
            names.add(node.controller)
    return {name: lambda value: value for name in names}


def _echo_subs(flow: Node) -> dict[str, Callable[[Any], Any]]:
    refs = {
        node.step.ref
        for node in flow.walk()
        if isinstance(node.step, SubStep)
    }
    return {ref: lambda value: value for ref in refs}


def _echo_agents(flow: Node) -> dict[str, Callable[[Any], Any]]:
    controllers = {
        node.controller
        for node in flow.walk()
        if node.op is Op.APP and node.controller is not None
    }
    return {controller: lambda value: value for controller in controllers}


class _LocalEffectsEnv(InMemoryEnv):
    """Interpreter environment that invokes the configured worker effects directly."""

    def __init__(
        self,
        manifest: Any,
        emitter: ProjectionEmitter,
        *,
        session_id: str,
        manifest_json: dict[str, Any],
        policy: ExecutionPolicy,
        gate: Callable[[Any, str, Optional[int]], Any],
        max_calls: Mapping[str, int],
        principal: Optional[dict[str, Any]],
        secrets: Optional[dict[str, str]],
        runtime_declarations_ref: Optional[dict[str, Any]],
        root_run_id: str,
        segment_seq: int,
        call_counts: dict[str, int],
    ) -> None:
        super().__init__(
            manifest,
            emitter,
            max_parallel=policy.max_parallel,
            max_calls=dict(max_calls),
            principal=principal,
            root_run_id=root_run_id,
            segment_seq=segment_seq,
        )
        self._session_id = session_id
        self._manifest_json = manifest_json
        self._policy = policy
        self._gate_waiter = gate
        self._secrets = secrets
        self._runtime_declarations_ref = runtime_declarations_ref
        # Share one mutable counter map across continuation segments and inline
        # subflows so a local execution cannot reset release-scoped maxCalls.
        self.call_counts = call_counts

    def next_cid(self, node_id: str) -> str:
        return f"{self._session_id}/{super().next_cid(node_id)}"

    def get_pure(self, name: str) -> Callable[..., Any]:
        registry = effects._hydrate_runtime_declarations(
            self._runtime_declarations_ref
        )
        return registry.get_pure(name)

    async def run_call(self, node: Node, value: Any, cid: str) -> Any:
        key = call_ref_key(node, self.manifest)
        step = node.step
        frozen_input_schema = (
            self.manifest[step.frozen_hash].input_schema
            if isinstance(step, CallStep) and step.frozen_hash is not None
            else None
        )
        cache = (
            node.ann.cache.to_json()
            if node.ann is not None and node.ann.cache is not None
            else None
        )
        return await effects.callTool(
            CallToolInput(
                tool_ref=toolref_json_from_key(key),
                value=value,
                cid=cid,
                cache=cache,
                principal=self.principal,
                run_id=self._session_id,
                root_run_id=self.root_run_id,
                segment_seq=self.segment_seq,
                node_id=node.id,
                op="call",
                kind="tool",
                secrets=self._secrets,
                frozen_input_schema=frozen_input_schema,
            )
        )

    async def invoke_reasoner(
        self,
        reasoner: str,
        value: Any,
        cid: str,
        timeout_s: Optional[int],
        batchable: bool = False,
    ) -> Any:
        del timeout_s, batchable
        return await effects.invokeReasoner(
            InvokeReasonerInput(
                reasoner=reasoner,
                value=value,
                cid=cid,
                principal=self.principal,
                run_id=self._session_id,
                root_run_id=self.root_run_id,
                segment_seq=self.segment_seq,
                op="think",
                kind="reasoner",
                runtime_declarations_ref=self._runtime_declarations_ref,
                secrets=self._secrets,
            )
        )

    async def compile_plan(self, planner: str, value: Any, cid: str) -> Node:
        plan = await effects.compilePlan(
            CompilePlanInput(
                planner=planner,
                value=value,
                cid=cid,
                manifest=self._manifest_json,
                principal=self.principal,
                runtime_declarations_ref=self._runtime_declarations_ref,
            )
        )
        compiled = Node.from_json(plan)
        _validate_finite_flow(compiled)
        return compiled

    async def run_sub(
        self,
        ref: str,
        contract: Any,
        value: Any,
        cid: str,
        node_id: Optional[str] = None,
    ) -> Any:
        del contract, node_id
        spec = await effects.resolveSubflow(ref)
        child_json = dict(spec["flowJson"])
        child = Node.from_json(child_json)
        _validate_finite_flow(child)
        await effects.verifyPures(
            VerifyPuresInput(
                pinned=dict(spec.get("pinnedPures") or {}),
                bundle=spec.get("bundle"),
                flow_json=child_json,
            )
        )
        child_manifest_json = dict(spec.get("manifestJson") or {})
        child_env = _LocalEffectsEnv(
            manifest_from_json(child_manifest_json),
            self.emitter,
            session_id=f"{self._session_id}-sub-{cid}",
            manifest_json=child_manifest_json,
            policy=self._policy,
            gate=self._gate_waiter,
            max_calls=self._max_calls,
            principal=self.principal,
            secrets=self._secrets,
            runtime_declarations_ref=(
                spec.get("runtimeDeclarationsRef")
                or self._runtime_declarations_ref
            ),
            root_run_id=self.root_run_id or self._session_id,
            segment_seq=self.segment_seq,
            call_counts=self.call_counts,
        )
        child_value = value
        for _ in range(1000):
            result = await interpret(child, child_value, child_env)
            if not is_continuation(result.value):
                return result.value
            child_value = continuation_value(result.value)
        raise RuntimeError(f"local subflow {ref!r} did not settle within 1000 segments")

    async def run_agent(
        self,
        controller: str,
        value: Any,
        cid: str,
        app_config: Optional[dict[str, Any]] = None,
    ) -> Any:
        from ..agent_loop import (
            AgentConfig,
            AgentState,
            drive_agent_loop,
            tool_input_schemas,
        )

        resolved = await effects.resolveAgentSpec(
            effects.ResolveAgentSpecInput(
                controller=controller,
                runtime_declarations_ref=self._runtime_declarations_ref,
            )
        )
        authored = {**dict(resolved.get("config") or {}), **dict(app_config or {})}
        cfg = AgentConfig.from_json(authored)
        raw_grants = (
            app_config.get("tools")
            if app_config is not None and "tools" in app_config
            else resolved.get("grantedTools")
        )
        grants = (
            None if raw_grants is None else set(str(name) for name in raw_grants)
        )
        raw_subflows = (
            app_config.get("subflows")
            if app_config is not None and "subflows" in app_config
            else resolved.get("grantedSubflows")
        )
        granted_subflows = (
            None
            if raw_subflows is None
            else set(str(name) for name in raw_subflows)
        )
        aliases = {
            str(alias): str(wire)
            for alias, wire in {
                **dict(resolved.get("toolAliases") or {}),
                **dict((app_config or {}).get("toolAliases") or {}),
            }.items()
        }
        contracts = {
            str(alias): dict(contract)
            for alias, contract in dict(resolved.get("grantedContracts") or {}).items()
        }
        contracts.update(
            {
                str(alias): dict(contract)
                for alias, contract in dict(
                    (app_config or {}).get("toolContracts") or {}
                ).items()
            }
        )
        for alias in set(contracts) | (grants or set()):
            wire = aliases.get(alias, alias)
            limit = self._max_calls.get(wire)
            if limit is None:
                continue
            contract = contracts.setdefault(alias, {})
            authored_limit = contract.get("maxCalls", contract.get("max_calls"))
            contract["maxCalls"] = (
                int(limit)
                if authored_limit is None
                else min(int(limit), int(authored_limit))
            )
        tool_defs = (app_config or {}).get("toolDefs", resolved.get("toolDefs"))
        schemas = tool_input_schemas(tool_defs) if tool_defs is not None else None

        async def invoke_controller(payload: dict[str, Any]) -> Any:
            return await self.invoke_reasoner(
                controller,
                payload,
                self.next_cid(f"agent:{controller}:reason"),
                None,
            )

        async def call_tool(
            name: str, value: Any, *, call_index: Optional[int] = None
        ) -> Any:
            del call_index
            alias = name
            args = value
            wire = aliases.get(alias, alias)
            return await effects.callTool(
                CallToolInput(
                    tool_ref=toolref_json_from_key(wire),
                    value=args,
                    cid=self.next_cid(f"agent:{controller}:{alias}"),
                    principal=self.principal,
                    run_id=self._session_id,
                    root_run_id=self.root_run_id,
                    segment_seq=self.segment_seq,
                    secrets=self._secrets,
                    frozen_input_schema=(None if schemas is None else schemas.get(alias)),
                )
            )

        async def run_subflow(ref: str, sub_input: Any) -> Any:
            return await self.run_sub(
                ref,
                None,
                sub_input,
                self.next_cid(f"agent:{controller}:sub:{ref}"),
            )

        result = await drive_agent_loop(
            input=value,
            cfg=cfg,
            invoke_controller=invoke_controller,
            call_tool=call_tool,
            run_subflow=run_subflow,
            granted=grants,
            granted_subflows=granted_subflows,
            contracts=contracts,
            tool_count_keys=aliases,
            tool_schemas=schemas,
            state=AgentState(last=value, call_counts=dict(self.call_counts)),
            get_pure=self.get_pure,
        )
        carried_counts = result.get("callCounts")
        if isinstance(carried_counts, Mapping):
            for tool, raw_count in carried_counts.items():
                key = str(tool)
                self.call_counts[key] = max(
                    self.call_counts.get(key, 0),
                    int(raw_count),
                )
        return result

    async def human_gate(self, value: Any, cid: str, timeout_s: Optional[int]) -> Any:
        return await self._gate_waiter(value, cid, timeout_s)


def _validate_finite_flow(flow: Node) -> None:
    for node in flow.walk():
        if node.op is Op.LOOP:
            raise ValueError("local flow execution cannot run session LOOP artifacts")
        step = node.step
        if (
            isinstance(step, CallStep)
            and isinstance(step.tool, NativeTool)
            and step.tool.name in {RECV_TOOL, EMIT_TOOL}
        ):
            raise ValueError("local flow execution cannot run session channel operations")


class LocalExecutionGateway:
    """A process-local implementation of the control-plane gateway protocol."""

    accepts_secrets: bool

    def __init__(
        self,
        store: ExecutionStore,
        *,
        context_factory: Optional[ContextFactory] = None,
        artifact_store_url: Optional[str] = None,
    ) -> None:
        self._store = store
        self._context_factory = context_factory
        self._context: Optional[WorkerContext] = None
        self._previous_context: Optional[WorkerContext] = None
        self._artifact_store_url = artifact_store_url
        self._previous_artifact_store_url: Optional[str] = None
        self._process_state_owner = object()
        self._owns_process_state = False
        self._started = False
        self._effects_lock = asyncio.Lock()
        self._runs: dict[str, _LocalRun] = {}
        self.accepts_secrets = context_factory is not None

    async def start(self) -> None:
        if self._started:
            return
        _claim_process_state(self._process_state_owner)
        self._owns_process_state = True
        self._started = True
        try:
            if self._artifact_store_url is not None:
                self._previous_artifact_store_url = os.environ.get(
                    "JULEP_ARTIFACT_STORE_URL"
                )
                os.environ["JULEP_ARTIFACT_STORE_URL"] = self._artifact_store_url
            if self._context_factory is None:
                return
            factory: Callable[[], Any]
            if isinstance(self._context_factory, str):
                from ..execution.serve import load_context_factory

                factory = load_context_factory(self._context_factory)
            else:
                factory = self._context_factory
            context = factory()
            if inspect.isawaitable(context):
                context = await context
            if not isinstance(context, WorkerContext):
                raise TypeError("local context factory must return a WorkerContext")
            self._previous_context = effects._CTX
            effects.configure(context)
            self._context = context
        except BaseException:
            self._restore_process_state()
            raise

    def _restore_process_state(self) -> None:
        try:
            if self._artifact_store_url is not None:
                if self._previous_artifact_store_url is None:
                    os.environ.pop("JULEP_ARTIFACT_STORE_URL", None)
                else:
                    os.environ["JULEP_ARTIFACT_STORE_URL"] = (
                        self._previous_artifact_store_url
                    )
            if self._previous_context is not None:
                effects.configure(self._previous_context)
        finally:
            self._context = None
            self._previous_context = None
            self._previous_artifact_store_url = None
            self._started = False
            if self._owns_process_state:
                _release_process_state(self._process_state_owner)
                self._owns_process_state = False

    async def ready(self) -> bool:
        return True

    async def start_flow(
        self,
        pipeline: PipelineRelease,
        *,
        workflow_id: str,
        run_id: str,
        input: Any,
        principal: dict[str, Any],
        queue_lanes: Optional[dict[str, str]],
        secrets: Optional[dict[str, str]],
    ) -> str:
        del queue_lanes
        if secrets and not self.accepts_secrets:
            raise ValueError("local echo execution does not accept run secrets")
        local_run_id = f"local-{uuid.uuid4()}"
        record = _LocalRun(run_id, workflow_id, local_run_id)
        self._runs[workflow_id] = record
        record.task = asyncio.create_task(
            self._execute(record, pipeline, input, principal, secrets),
            name=f"julep-local-{run_id}",
        )
        return local_run_id

    async def _execute(
        self,
        record: _LocalRun,
        pipeline: PipelineRelease,
        input: Any,
        principal: dict[str, Any],
        secrets: Optional[dict[str, str]],
    ) -> None:
        value = input
        result: Any = None
        last_event_id: Optional[str] = None
        call_counts: dict[str, int] = {}
        try:
            flow_json = dict(pipeline.flow_json)
            manifest_json = dict(pipeline.manifest_json)
            flow = Node.from_json(flow_json)
            _validate_finite_flow(flow)

            if self._context is not None:
                await preflightMcp(
                    {
                        "workflowId": record.workflow_id,
                        "flowJson": flow_json,
                        "manifestJson": manifest_json,
                        "policy": pipeline.mcp_preflight_policy or "off",
                        "principal": principal,
                        **({"secrets": secrets} if secrets else {}),
                    }
                )
                await effects.verifyPures(
                    VerifyPuresInput(
                        pinned=dict(pipeline.pinned_pures),
                        bundle=pipeline.bundle_ref,
                        flow_json=flow_json,
                        artifact_hash=pipeline.artifact_hash,
                    )
                )
                echo_registry: Optional[Registry] = None
            else:
                echo_registry = (
                    DEFAULT_REGISTRY
                    if pipeline.runtime_declarations_ref is None
                    else effects._hydrate_runtime_declarations(
                        pipeline.runtime_declarations_ref
                    )
                )
                # Bundle resolution and pin verification are implemented by the
                # backend-neutral effect. Temporarily point it at this release's
                # registry, then restore the process context before execution.
                async with self._effects_lock:
                    previous_context = effects._CTX
                    try:
                        effects.configure(WorkerContext(registry=echo_registry))
                        await effects.verifyPures(
                            VerifyPuresInput(
                                pinned=dict(pipeline.pinned_pures),
                                bundle=pipeline.bundle_ref,
                                flow_json=flow_json,
                                artifact_hash=pipeline.artifact_hash,
                            )
                        )
                    finally:
                        effects.configure(previous_context)

            for segment_seq in range(1000):
                record.segment_seq = segment_seq
                projection = InMemoryProjection()
                record.projection = projection
                sink = _ExecutionProjectionSink(
                    self._store,
                    projection,
                    run_id=record.run_id,
                    workflow_id=record.workflow_id,
                    segment_seq=segment_seq,
                    secrets=secrets,
                )
                emitter = ProjectionEmitter(TeeStore(projection, sink))
                gate = lambda gate_value, cid, timeout_s: self._await_human(  # noqa: E731
                    record, gate_value, cid, timeout_s
                )
                if self._context is None:
                    env: Any = InMemoryEnv(
                        manifest_from_json(manifest_json),
                        emitter,
                        tools=_echo_tools(flow),
                        reasoners=_echo_reasoners(flow),
                        subs=_echo_subs(flow),
                        agents=_echo_agents(flow),
                        gate=lambda _value: None,
                        max_calls=dict(pipeline.max_call_limits),
                        max_parallel=(
                            pipeline.execution_policy.max_parallel
                            if pipeline.execution_policy is not None
                            else None
                        ),
                        principal=principal,
                        root_run_id=record.run_id,
                        segment_seq=segment_seq,
                        registry=echo_registry,
                    )
                    env.call_counts = call_counts

                    async def echo_gate(
                        gate_value: Any, cid: str, timeout_s: Optional[int]
                    ) -> Any:
                        return await self._await_human(
                            record, gate_value, cid, timeout_s
                        )

                    env.human_gate = echo_gate
                else:
                    env = _LocalEffectsEnv(
                        manifest_from_json(manifest_json),
                        emitter,
                        session_id=record.workflow_id,
                        manifest_json=manifest_json,
                        policy=pipeline.execution_policy or ExecutionPolicy(),
                        gate=gate,
                        max_calls=pipeline.max_call_limits,
                        principal=principal,
                        secrets=secrets,
                        runtime_declarations_ref=pipeline.runtime_declarations_ref,
                        root_run_id=record.run_id,
                        segment_seq=segment_seq,
                        call_counts=call_counts,
                    )
                segment: Result = await interpret(flow, value, env)
                result = segment.value
                last_event_id = segment.event_id
                if not is_continuation(result):
                    break
                value = continuation_value(result)
            else:
                raise RuntimeError("local flow did not settle within 1000 segments")
        except asyncio.CancelledError:
            status = record.stop_status or "canceled"
            record.status = status
            self._finalize(
                record,
                status=status,
                result=None,
                cause=last_event_id,
                secrets=secrets,
            )
            return
        except Exception as exc:  # noqa: BLE001 - persist a terminal local run
            record.status = "failed"
            self._finalize(
                record,
                status="failed",
                result=None,
                error=f"{type(exc).__name__}: {exc}",
                cause=last_event_id,
                secrets=secrets,
            )
            return

        record.status = "completed"
        self._finalize(
            record,
            status="completed",
            result=result,
            cause=last_event_id,
            secrets=secrets,
        )

    async def _await_human(
        self,
        record: _LocalRun,
        value: Any,
        cid: str,
        timeout_s: Optional[int],
    ) -> Any:
        if cid in record.early_signals:
            return record.early_signals.pop(cid)
        future = asyncio.get_running_loop().create_future()
        record.open_gates[cid] = future
        try:
            if timeout_s is None:
                return await future
            try:
                return await asyncio.wait_for(future, float(timeout_s))
            except asyncio.TimeoutError:
                return {"approved": False, "reason": "timeout", "input": value}
        finally:
            record.open_gates.pop(cid, None)

    def _finalize(
        self,
        record: _LocalRun,
        *,
        status: str,
        result: Any,
        error: Optional[str] = None,
        cause: Optional[str] = None,
        secrets: Optional[Mapping[str, str]] = None,
    ) -> None:
        captured = _capture_value(result, secrets) if status == "completed" else None
        event: dict[str, Any] = {
            "eventId": "__terminal__",
            "type": EventType.DID.value if status == "completed" else EventType.FAILED.value,
            "node": "__run__",
            "cid": f"{record.run_id}:terminal",
            "ts": time.time(),
            "causes": [] if cause is None else [cause],
            "attrs": {"terminal": True, "status": status, "local": True},
        }
        if error is not None:
            event["error"] = error
        event = _redact_projection_metadata(event, secrets)
        safe_error = event.get("error")
        terminal = _normalise_event(
            event,
            run_id=record.run_id,
            workflow_id=record.workflow_id,
            segment_seq=record.segment_seq,
            value_ref=None if captured is None else captured.value_ref,
        )
        try:
            self._store.finalize_run(
                run_id=record.run_id,
                workflow_id=record.workflow_id,
                segment_seq=record.segment_seq,
                status=status,
                terminal_event=terminal,
                result_payload=None if captured is None else captured.payload,
                result_byte_len=0 if captured is None else captured.byte_len,
                result_oversize=False if captured is None else captured.oversize,
                error=None if safe_error is None else str(safe_error),
                finished_at=time.time(),
            )
        finally:
            self._scrub_live_projection(record, secrets)

    @staticmethod
    def _scrub_live_projection(
        record: _LocalRun,
        secrets: Optional[Mapping[str, str]],
    ) -> None:
        """Retain queryable event metadata without retaining raw interpreter values."""

        raw_projection = record.projection
        # Fail closed: detach the raw value store before attempting any redaction.
        record.projection = None
        if raw_projection is None:
            return
        safe_projection = InMemoryProjection()
        for event in raw_projection.events():
            candidate = _redact_projection_metadata(event.to_json(), secrets)
            if candidate.get("attrs") is None:
                candidate.pop("attrs", None)
            # The interpreter reference hashes the raw value. Persisted projection
            # refs are independently derived from the redacted value, so the live
            # query view must not retain or expose the raw reference.
            candidate.pop("valueRef", None)
            safe_projection.append(ProjectionEvent.from_json(candidate))
        record.projection = safe_projection

    async def cancel(self, workflow_id: str) -> None:
        await self._stop(workflow_id, "canceled")

    async def terminate(self, workflow_id: str) -> None:
        await self._stop(workflow_id, "terminated")

    async def _stop(self, workflow_id: str, status: str) -> None:
        record = self._runs.get(workflow_id)
        if record is None:
            raise KeyError(workflow_id)
        record.stop_status = status
        if record.task is not None and not record.task.done():
            record.task.cancel()
            try:
                await record.task
            except asyncio.CancelledError:
                pass

    async def describe(self, workflow_id: str) -> str:
        record = self._runs.get(workflow_id)
        return "not_found" if record is None else record.status

    async def signal(self, workflow_id: str, name: str, arg: Any) -> None:
        if name != "submitHuman":
            raise ValueError(f"unsupported local signal {name!r}")
        record = self._runs.get(workflow_id)
        if record is None:
            raise KeyError(workflow_id)
        if not isinstance(arg, Mapping) or not isinstance(arg.get("cid"), str):
            raise ValueError("submitHuman needs a string cid")
        cid = str(arg["cid"])
        value = arg.get("value")
        future = record.open_gates.get(cid)
        if future is None:
            record.early_signals[cid] = value
        elif not future.done():
            future.set_result(value)

    async def query(self, workflow_id: str, name: str) -> Any:
        record = self._runs.get(workflow_id)
        if record is None:
            raise KeyError(workflow_id)
        if name == "openGates":
            return sorted(record.open_gates)
        if name == "projection":
            projection = record.projection
            return [] if projection is None else [event.to_json() for event in projection.events()]
        raise ValueError(f"unsupported local query {name!r}")

    async def close(self) -> None:
        if not self._started:
            return
        tasks: list[asyncio.Task[None]] = []
        try:
            for record in self._runs.values():
                task = record.task
                if task is not None and not task.done():
                    record.stop_status = "canceled"
                    task.cancel()
                    tasks.append(task)
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            self._restore_process_state()


def create_local_app(
    project_root: str | Path = ".",
    host: str = "127.0.0.1",
    context_factory: Optional[ContextFactory] = None,
) -> FastAPI:
    """Build a zero-daemon API server with process-local execution state."""

    root = Path(project_root).resolve()
    env = dict(os.environ)
    # Parse ordinary API-key/project configuration without imposing Temporal's
    # payload-codec prerequisite on a server that never connects to Temporal.
    env["TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED"] = "false"
    settings = ServerSettings.from_env(env, root=root)
    api_keys = settings.api_keys
    if not api_keys:
        if context_factory is not None:
            raise ValueError(
                "local configured-context execution requires explicitly configured API keys"
            )
        try:
            loopback = ipaddress.ip_address(host).is_loopback
        except ValueError:
            loopback = host.strip().lower() == "localhost"
        if not loopback:
            raise ValueError(
                "local mode needs configured API keys when binding a non-loopback host"
            )
        api_keys = (ApiKey("local-dev", "local-dev", role="admin"),)

    artifact_root = root / ".julep" / "artifacts"
    settings = replace(
        settings,
        api_keys=api_keys,
        host=host,
        execution_store_dsn=None,
        artifact_store_url=artifact_root.as_uri(),
        payload_encryption_required=context_factory is not None,
        helm_chart=None,
        reconcile_interval_s=0.0,
    )
    store = InMemoryExecutionStore()
    gateway = LocalExecutionGateway(
        store,
        context_factory=context_factory,
        artifact_store_url=artifact_root.as_uri(),
    )
    app = create_app(
        settings=settings,
        store=store,
        gateway=gateway,
        artifacts=LocalDirArtifactStore(artifact_root),
        reconciler=None,
        enable_reconciler=False,
        keyring=KeyRing(api_keys, reload_source=lambda: api_keys),
        vault_cipher=VaultCipher(
            {"local-ephemeral": _secrets.token_bytes(32)},
            active_key_id="local-ephemeral",
        ),
    )
    app.state.local_mode = True
    app.state.local_echo_mode = context_factory is None
    return app


__all__ = ["LocalExecutionGateway", "create_local_app"]
