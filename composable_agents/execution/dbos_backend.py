"""The DBOS execution backend: frozen IR on dbos-transact durable workflows.

Mirrors :mod:`composable_agents.execution.harness` for DBOS. One workflow
(``flow_workflow``) interprets a frozen flow; every effect leaf is a
``@DBOS.step`` delegating to the backend-neutral :mod:`.effects` layer, so a
worker configured via :func:`composable_agents.execution.effects.configure`
serves both backends identically.

Backend-specific contracts (the deltas vs Temporal -- see docs/deploy-dbos.md):

* **No race/hedge/quorum, no app nodes** (v1). DBOS cannot cancel an in-flight
  step, so racing semantics would lie. :func:`assert_dbos_executable` rejects
  these at dispatch; the compiled output of an ``eval_plan`` is re-scanned too.
* **Brain steps never retry.** LLM resilience belongs to the injected
  ``LlmCaller`` (the consumer's retry/fallback stack), not to a second,
  blind retry layer here. Hands keep contract-derived retries, quantized to
  two variants (idempotent: 5 attempts, write: 3) because DBOS fixes retry
  config at decoration time.
* **Policy errors are never retried.** A settled decision (CapabilityDenied,
  PlanRejected, ValidationError, FreezeError, PureDriftError) is returned from
  the step as an envelope and re-raised by the env.
* **Sub-flows run inline** in the parent workflow (their steps checkpoint into
  the parent's history). Temporal uses child workflows; DBOS v1 trades that
  isolation for simplicity.
* **Chaining** = one DBOS workflow per segment (see run_flow_dbos, Task 8);
  ``maxCalls`` budgets carry across segments via the continuation envelope.

Triggering (schedules, debounce, dedup ids, queue routing) stays OUTSIDE the
IR -- that is the dispatch boundary (docs/dispatch-boundary.md). This module
deliberately exposes ``queue=`` pass-throughs and nothing more.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

from dbos import DBOS, Queue, SetWorkflowID  # noqa: F401 (Queue re-exported for callers)

from .. import agent_loop as al
from ..continuation import CONTINUATION_KEY, continuation_value, is_continuation
from ..contracts import manifest_from_json
from ..errors import (
    CapabilityDenied,
    ComposableAgentsError,
    FreezeError,
    PlanRejected,
    PureDriftError,
    UnsupportedShapeError,
    ValidationError,
)
from ..ir import Node
from ..kinds import Op
from ..projection import InMemoryProjection, ProjectionEmitter, ProjectionSink, TeeStore
from . import effects
from .effects import (
    CallHandInput,
    CompilePlanInput,
    InvokeBrainInput,
    toolref_json_from_key,
)
from .interpreter import (
    BranchThunk,
    Result,
    call_contract,
    call_ref_key,
    gather_bounded,
    interpret,
)
from .policy import ExecutionPolicy

# recv() needs *some* timeout; a week is "effectively forever" for a gate while
# still letting an abandoned workflow drain. Override per node via ann.timeout.
_GATE_DEFAULT_TIMEOUT_S = 7 * 24 * 3600

_POLICY_ERRORS = (CapabilityDenied, PlanRejected, ValidationError, FreezeError, PureDriftError)
_POLICY_ERROR_KEY = "__ca_policy_error__"
_POLICY_ERROR_TYPES = {e.__name__: e for e in _POLICY_ERRORS}


# --------------------------------------------------------------------------- #
# Policy-error envelope: settled decisions must cross the step boundary as
# values so DBOS's retry machinery never sees them as failures.
# --------------------------------------------------------------------------- #
def encode_policy_error(exc: Exception) -> dict[str, Any]:
    return {_POLICY_ERROR_KEY: {"type": type(exc).__name__, "message": str(exc)}}


def decode_policy_error(out: Any) -> Any:
    if isinstance(out, dict) and _POLICY_ERROR_KEY in out:
        payload = out[_POLICY_ERROR_KEY]
        exc_type = _POLICY_ERROR_TYPES.get(payload.get("type"), ComposableAgentsError)
        message = payload.get("message", "policy error")
        exc = exc_type.__new__(exc_type)
        Exception.__init__(exc, message)
        raise exc
    return out


# --------------------------------------------------------------------------- #
# Pre-dispatch shape scan.
# --------------------------------------------------------------------------- #
def assert_dbos_executable(flow: Node) -> None:
    """Reject IR the DBOS backend cannot run (race family, app nodes)."""
    for n in flow.walk():
        if n.op == Op.PAR and n.merge is not None and n.merge.kind in {"race", "hedge", "quorum"}:
            raise UnsupportedShapeError(
                f"node {n.id!r}: merge kind {n.merge.kind!r} (race family) needs branch "
                "cancellation, which DBOS does not provide; run this flow on the "
                "Temporal backend or restructure with par/alt"
            )
        if n.op == Op.APP:
            raise UnsupportedShapeError(
                f"node {n.id!r}: app (agent-loop) nodes are not yet supported on the "
                "DBOS backend; run this flow on the Temporal backend"
            )


# --------------------------------------------------------------------------- #
# Projection sink (process-global, like effects.configure).
# --------------------------------------------------------------------------- #
_PROJECTION_SINK: Optional[ProjectionSink] = None


def set_projection_sink(sink: Optional[ProjectionSink]) -> None:
    """Install a process-wide sink that receives every projection event."""
    global _PROJECTION_SINK
    _PROJECTION_SINK = sink


# --------------------------------------------------------------------------- #
# Effect steps. Names are stable identifiers in DBOS's workflow_status table.
# --------------------------------------------------------------------------- #
@DBOS.step(retries_allowed=True, max_attempts=5)
async def callHandIdempotent(inp: dict) -> Any:
    try:
        return await effects.callHand(_call_hand_input(inp))
    except _POLICY_ERRORS as exc:
        return encode_policy_error(exc)


@DBOS.step(retries_allowed=True, max_attempts=3)
async def callHandWrite(inp: dict) -> Any:
    try:
        return await effects.callHand(_call_hand_input(inp))
    except _POLICY_ERRORS as exc:
        return encode_policy_error(exc)


@DBOS.step(retries_allowed=False)
async def invokeBrainStep(inp: dict) -> Any:
    try:
        return await effects.invokeBrain(
            InvokeBrainInput(brain=inp["brain"], value=inp["value"], cid=inp["cid"])
        )
    except _POLICY_ERRORS as exc:
        return encode_policy_error(exc)


@DBOS.step(retries_allowed=False)
async def compilePlanStep(inp: dict) -> Any:
    try:
        return await effects.compilePlan(
            CompilePlanInput(
                planner=inp["planner"], value=inp["value"], cid=inp["cid"],
                manifest=inp.get("manifest"),
            )
        )
    except _POLICY_ERRORS as exc:
        return encode_policy_error(exc)


@DBOS.step(retries_allowed=False)
async def verifyPuresStep(pinned: dict) -> Any:
    try:
        await effects.verifyPures(pinned)
        return None
    except _POLICY_ERRORS as exc:
        return encode_policy_error(exc)


@DBOS.step(retries_allowed=True, max_attempts=3)
async def resolveSubflowStep(ref: str) -> dict:
    return await effects.resolveSubflow(ref)


@DBOS.step(retries_allowed=False)
async def resolveRuntimeCapabilitiesStep() -> dict:
    return await effects.resolveRuntimeCapabilities()


def _call_hand_input(inp: dict) -> CallHandInput:
    return CallHandInput(
        tool_ref=inp["tool_ref"], value=inp["value"], cid=inp["cid"],
        cache=inp.get("cache"),
    )


# --------------------------------------------------------------------------- #
# The Env.
# --------------------------------------------------------------------------- #
class DbosEnv:
    """An :class:`~composable_agents.execution.interpreter.Env` whose effects
    are DBOS steps. Lives entirely inside one ``flow_workflow`` execution."""

    def __init__(
        self,
        manifest,
        emitter: ProjectionEmitter,
        *,
        session_id: str,
        manifest_json: Optional[dict[str, Any]],
        policy: ExecutionPolicy,
        max_call_limits: Optional[dict[str, int]] = None,
        call_counts: Optional[dict[str, int]] = None,
    ) -> None:
        self.manifest = manifest
        self.emitter = emitter
        self._session = session_id
        self._manifest_json = manifest_json
        self._policy = policy
        self._max_call_limits = dict(max_call_limits or {})
        self._call_counts: dict[str, int] = dict(call_counts or {})
        self._cid = 0

    # --- identity / pures --- #
    def next_cid(self, node_id: str) -> str:
        self._cid += 1
        # Session-prefixed (unlike Temporal) because inline sub-flows share one
        # workflow: the prefix keeps Idempotency-Keys distinct across parent/child.
        return f"{self._session}/{node_id}@{self._cid}"

    def get_pure(self, name: str):
        from ..purity import get_pure as _gp

        return _gp(name)

    def charge_call(self, tool_key: str) -> None:
        limit = self._max_call_limits.get(tool_key)
        if limit is None:
            return
        count = self._call_counts.get(tool_key, 0)
        if count >= limit:
            raise CapabilityDenied(f"tool {tool_key!r} exceeded maxCalls={limit}")
        self._call_counts[tool_key] = count + 1

    def call_counts_snapshot(self) -> dict[str, int]:
        return dict(self._call_counts)

    # --- effect handlers --- #
    async def call_hand(self, node: Node, value: Any, cid: str) -> Any:
        ref_key = call_ref_key(node, self.manifest)
        contract = call_contract(node, self.manifest)
        attempts = al.retry_max_attempts_for_contract(
            contract,
            idempotent_max_attempts=self._policy.idempotent_max_attempts,
            write_max_attempts=self._policy.write_max_attempts,
        )
        step = callHandIdempotent if attempts >= self._policy.idempotent_max_attempts else callHandWrite
        cache = node.ann.cache.to_json() if node.ann and node.ann.cache is not None else None
        out = await step({
            "tool_ref": toolref_json_from_key(ref_key),
            "value": value, "cid": cid, "cache": cache,
        })
        return decode_policy_error(out)

    async def invoke_brain(
        self, brain: str, value: Any, cid: str, timeout_s: Optional[int],
    ) -> Any:
        out = await invokeBrainStep({"brain": brain, "value": value, "cid": cid})
        return decode_policy_error(out)

    async def compile_plan(self, planner: str, value: Any, cid: str) -> Node:
        out = await compilePlanStep({
            "planner": planner, "value": value, "cid": cid,
            "manifest": self._manifest_json,
        })
        plan = Node.from_json(decode_policy_error(out))
        assert_dbos_executable(plan)  # a compiled plan must obey backend limits too
        return plan

    async def run_sub(self, ref: str, contract, value: Any, cid: str) -> Any:
        resolved = await resolveSubflowStep(ref)
        child = Node.from_json(resolved["flowJson"])
        assert_dbos_executable(child)
        pinned = resolved.get("pinnedPures")
        if pinned:
            decode_policy_error(await verifyPuresStep(pinned))
        child_env = DbosEnv(
            manifest=manifest_from_json(resolved.get("manifestJson") or {}),
            emitter=self.emitter,
            session_id=f"{self._session}-sub-{cid}",
            manifest_json=resolved.get("manifestJson") or {},
            policy=self._policy,
            max_call_limits=self._max_call_limits,
            call_counts=dict(self._call_counts),
        )
        r: Result = await interpret(child, value, child_env)
        return r.value

    async def run_agent(
        self, controller: str, value: Any, cid: str,
        app_config: Optional[dict[str, Any]] = None,
    ) -> Any:
        raise UnsupportedShapeError(
            "app (agent-loop) nodes are not yet supported on the DBOS backend"
        )

    async def human_gate(self, value: Any, cid: str, timeout_s: Optional[int]) -> Any:
        payload = await DBOS.recv_async(
            topic=f"gate:{cid}",
            timeout_seconds=float(timeout_s) if timeout_s else float(_GATE_DEFAULT_TIMEOUT_S),
        )
        if payload is None:
            return {"approved": False, "reason": "timeout", "input": value}
        return payload

    async def sleep(self, seconds: int, cid: str) -> None:
        await DBOS.sleep_async(float(seconds))

    # --- concurrency --- #
    async def gather(self, coros: Sequence[Any]) -> list[Any]:
        return await gather_bounded(coros, max_parallel=self._policy.max_parallel)

    async def race_first(
        self, branches: Sequence[BranchThunk], *, kind: str, m: int, hedge_ms: Optional[int],
    ) -> Any:
        raise UnsupportedShapeError(
            f"merge kind {kind!r} (race family) is not supported on the DBOS backend"
        )


# --------------------------------------------------------------------------- #
# The workflow: one chain segment of one frozen flow.
# --------------------------------------------------------------------------- #
@DBOS.workflow(name="ca_flow")
async def flow_workflow(inp: dict) -> Any:
    """Interpret one segment. ``inp`` is a plain JSON dict (camelCase keys
    mirroring :class:`~composable_agents.execution.harness.FlowInput`)."""
    policy = ExecutionPolicy.from_json(inp.get("policy"))
    flow_json = inp.get("flowJson")
    manifest_json = inp.get("manifestJson") or {}

    if flow_json is None:
        if not inp.get("ref"):
            raise ValueError("flow_workflow input needs either flowJson or ref")
        resolved = await resolveSubflowStep(inp["ref"])
        flow_json = resolved["flowJson"]
        manifest_json = resolved.get("manifestJson") or {}
        if inp.get("pinnedPures") is None:
            inp = {**inp, "pinnedPures": resolved.get("pinnedPures")}
        if inp.get("maxCallLimits") is None:
            inp = {**inp, "maxCallLimits": resolved.get("maxCalls")}

    pinned = inp.get("pinnedPures")
    if pinned is not None:
        decode_policy_error(await verifyPuresStep(pinned))

    max_call_limits = inp.get("maxCallLimits")
    if max_call_limits is None:
        caps = await resolveRuntimeCapabilitiesStep()
        max_call_limits = caps.get("maxCalls", {})

    flow = Node.from_json(flow_json)
    assert_dbos_executable(flow)

    store = InMemoryProjection()
    sink = _PROJECTION_SINK
    emitter = ProjectionEmitter(TeeStore(store, sink) if sink is not None else store)

    env = DbosEnv(
        manifest=manifest_from_json(manifest_json),
        emitter=emitter,
        session_id=inp["sessionId"],
        manifest_json=manifest_json,
        policy=policy,
        max_call_limits=max_call_limits,
        call_counts=inp.get("callCounts"),
    )
    result: Result = await interpret(flow, inp.get("input"), env)

    if is_continuation(result.value):
        # Enrich the sentinel so the runner can carry budgets into the next segment.
        return {
            CONTINUATION_KEY: continuation_value(result.value),
            "callCounts": env.call_counts_snapshot(),
        }
    return result.value
