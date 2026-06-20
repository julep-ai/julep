"""The DBOS execution backend: frozen IR on dbos-transact durable workflows.

Mirrors :mod:`composable_agents.execution.harness` for DBOS. One workflow
(``flow_workflow``) interprets a frozen flow; every effect leaf is a
``@DBOS.step`` delegating to the backend-neutral :mod:`.effects` layer, so a
worker configured via :func:`composable_agents.execution.effects.configure`
serves both backends identically.

Backend-specific contracts (the deltas vs Temporal -- see docs/deploy-dbos.md):

* **No race/hedge/quorum**. DBOS cannot cancel an in-flight step, so racing
  semantics would lie. :func:`assert_dbos_executable` rejects these at
  dispatch; the compiled output of an ``eval_plan`` is re-scanned too.
* **App (agent-loop) nodes are supported** via a dedicated ``ca_agent``
  workflow: one DBOS workflow per history segment (ids ``{base}``,
  ``{base}-seg1``, ...), state crossing segments in the continuation envelope.
  Standalone dispatch goes through :func:`run_agent_dbos`; ``Op.APP`` nodes in
  a flow reach the same chain through :meth:`DbosEnv.run_agent`. The
  session-store (``use_session_store``/``state_cursor``) path is Temporal-only.
* **Brain steps never retry.** LLM resilience belongs to the injected
  ``LlmCaller`` (the consumer's retry/fallback stack), not to a second,
  blind retry layer here. Hands are routed by the retry algebra: contracts gate
  retry eligibility, non-retryable calls use a no-retry step, and retryable
  calls use the predeclared idempotent DBOS step because DBOS fixes retry
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
from ..contracts import contract_allows_retry, manifest_from_json
from ..errors import (
    CapabilityDenied,
    ComposableAgentsError,
    POLICY_ERRORS,
    UnsupportedShapeError,
)
from ..ir import Node
from ..kinds import Op
from ..projection import InMemoryProjection, ProjectionEmitter, ProjectionSink, TeeStore
from ..trajectory import ProjectionTrajectorySink
from ..turn import Halt, controller_turn, make_finalize, pre_round
from . import effects
from .effects import (
    CallHandInput,
    CompilePlanInput,
    InvokeBrainInput,
    PutBlobInput,
    RunSubInput,
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

_POLICY_ERROR_KEY = "__ca_policy_error__"
_POLICY_ERROR_TYPES = {e.__name__: e for e in POLICY_ERRORS}


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
    """Reject IR the DBOS backend cannot run (race family)."""
    for n in flow.walk():
        if n.op == Op.PAR and n.merge is not None and n.merge.kind in {"race", "hedge", "quorum"}:
            raise UnsupportedShapeError(
                f"node {n.id!r}: merge kind {n.merge.kind!r} (race family) needs branch "
                "cancellation, which DBOS does not provide; run this flow on the "
                "Temporal backend or restructure with par/alt"
            )


# --------------------------------------------------------------------------- #
# Projection sink (process-global, like effects.configure).
# --------------------------------------------------------------------------- #
_PROJECTION_SINK: Optional[ProjectionSink] = None


def set_projection_sink(sink: Optional[ProjectionSink]) -> None:
    """Install a process-wide sink that receives every projection event."""
    global _PROJECTION_SINK
    _PROJECTION_SINK = sink


def _make_projection_emitter(
    node_ops: dict[str, str],
    *,
    run_id: str,
    root_run_id: str,
    segment_seq: int,
) -> ProjectionEmitter:
    store = InMemoryProjection()
    sinks: list[ProjectionSink] = []
    if _PROJECTION_SINK is not None:
        sinks.append(_PROJECTION_SINK)
    if effects._TRAJECTORY_SINK is not None:
        # Temporal sources structural trajectory steps through a history
        # interceptor, not an in-workflow projection sink.
        sinks.append(
            ProjectionTrajectorySink(
                effects._TRAJECTORY_SINK,
                run_id=run_id,
                root_run_id=root_run_id,
                segment_seq=segment_seq,
                node_ops=node_ops,
            )
        )
    return ProjectionEmitter(TeeStore(store, *sinks) if sinks else store)


# --------------------------------------------------------------------------- #
# Effect steps. Names are stable identifiers in DBOS's workflow_status table.
# --------------------------------------------------------------------------- #
@DBOS.step(retries_allowed=True, max_attempts=5)
async def callHandIdempotent(inp: dict) -> Any:
    try:
        return await effects.callHand(_call_hand_input(inp))
    except POLICY_ERRORS as exc:
        return encode_policy_error(exc)


# The persisted name stays "callHandWrite" — the step's name before the retry
# algebra landed. DBOS records step names per function_id and recovery raises
# DBOSUnexpectedStepError on mismatch, so renaming the durable identity would
# break replay of in-flight workflows that recorded the old name. The Python
# name describes today's semantics; the wire name is frozen. (Known residue:
# a retryable *write* recorded as callHandWrite now routes to
# callHandIdempotent — a deliberate identity change of the retry algebra;
# drain in-flight workflows across that upgrade.)
@DBOS.step(retries_allowed=False, name="callHandWrite")
async def callHandNoRetry(inp: dict) -> Any:
    try:
        return await effects.callHand(_call_hand_input(inp))
    except POLICY_ERRORS as exc:
        return encode_policy_error(exc)


@DBOS.step(retries_allowed=False)
async def invokeBrainStep(inp: dict) -> Any:
    try:
        return await effects.invokeBrain(
            InvokeBrainInput(
                brain=inp["brain"], value=inp["value"], cid=inp["cid"],
                principal=inp.get("principal"),
                transcript=inp.get("transcript"),
                ctx=inp.get("ctx"),
                summarizer=inp.get("summarizer"),
                summary=inp.get("summary"),
                run_id=inp.get("run_id"),
                root_run_id=inp.get("root_run_id"),
                segment_seq=inp.get("segment_seq"),
                node_id=inp.get("node_id"),
                op=inp.get("op"),
                kind=inp.get("kind"),
                causes=tuple(inp.get("causes") or ()),
            )
        )
    except POLICY_ERRORS as exc:
        return encode_policy_error(exc)


@DBOS.step(retries_allowed=False)
async def compilePlanStep(inp: dict) -> Any:
    try:
        return await effects.compilePlan(
            CompilePlanInput(
                planner=inp["planner"], value=inp["value"], cid=inp["cid"],
                manifest=inp.get("manifest"), principal=inp.get("principal"),
            )
        )
    except POLICY_ERRORS as exc:
        return encode_policy_error(exc)


@DBOS.step(retries_allowed=False)
async def verifyPuresStep(pinned: dict) -> Any:
    try:
        await effects.verifyPures(pinned)
        return None
    except POLICY_ERRORS as exc:
        return encode_policy_error(exc)


@DBOS.step(retries_allowed=True, max_attempts=3)
async def resolveSubflowStep(ref: str) -> dict:
    return await effects.resolveSubflow(ref)


@DBOS.step(retries_allowed=False)
async def resolveRuntimeCapabilitiesStep() -> dict:
    return await effects.resolveRuntimeCapabilities()


@DBOS.step(retries_allowed=True, max_attempts=3)
async def resolveAgentSpecStep(controller: str) -> dict:
    return await effects.resolveAgentSpec(controller)


@DBOS.step(retries_allowed=True, max_attempts=3)
async def putBlobStep(inp: dict) -> str:
    return await effects.putBlob(PutBlobInput(tenant=inp["tenant"], value=inp["value"]))


@DBOS.step(retries_allowed=False)
async def finishTrajectoryStep(inp: dict) -> None:
    import time

    from .. import trajectory as _traj
    from . import effects as _effects

    sink = _effects._TRAJECTORY_SINK
    if sink is None:
        return
    run_id = inp.get("runId")
    root_run_id = inp.get("rootRunId") or run_id
    status = inp.get("status", "completed")
    _traj._best_effort(lambda: sink.finish_run(run_id, status, time.time()))
    await _effects.record_marker_step(
        kind="final",
        run_id=run_id,
        root_run_id=root_run_id,
        segment_seq=inp.get("segmentSeq"),
        value=inp.get("finalValue"),
        cid=f"{run_id}:final",
        value_kind="output",
    )


@DBOS.step(retries_allowed=False)
async def startTrajectoryStep(inp: dict) -> None:
    from .. import trajectory as _traj
    from . import effects as _effects

    try:
        await _effects.record_marker_step(
            kind="root",
            run_id=inp.get("runId"),
            root_run_id=inp.get("rootRunId"),
            segment_seq=inp.get("segmentSeq"),
            value=inp.get("input"),
            cid=inp["cid"],
            value_kind="input",
        )
    except Exception as exc:
        def _reraise(e: BaseException = exc) -> None:
            raise e

        _traj._best_effort(_reraise)


@DBOS.step(retries_allowed=False)
async def runSubCaptureStep(inp: dict) -> None:
    from .. import trajectory as _traj

    try:
        await effects.runSub(
            RunSubInput(
                ref=inp["ref"],
                value=inp["value"],
                cid=inp["cid"],
                principal=inp.get("principal"),
                run_id=inp.get("run_id"),
                root_run_id=inp.get("root_run_id"),
                segment_seq=inp.get("segment_seq"),
                node_id=inp.get("node_id"),
                op=inp.get("op"),
                kind=inp.get("kind"),
                causes=tuple(inp.get("causes") or ()),
            ),
            inp.get("output"),
        )
    except Exception as exc:
        def _reraise(e: BaseException = exc) -> None:
            raise e

        _traj._best_effort(_reraise)


def _call_hand_input(inp: dict) -> CallHandInput:
    return CallHandInput(
        tool_ref=inp["tool_ref"], value=inp["value"], cid=inp["cid"],
        cache=inp.get("cache"), principal=inp.get("principal"),
        run_id=inp.get("run_id"),
        root_run_id=inp.get("root_run_id"),
        segment_seq=inp.get("segment_seq"),
        node_id=inp.get("node_id"),
        op=inp.get("op"),
        kind=inp.get("kind"),
        causes=tuple(inp.get("causes") or ()),
    )


# --------------------------------------------------------------------------- #
# Inline sub-flow execution, shared by DbosEnv.run_sub and the agent loop.
# --------------------------------------------------------------------------- #
async def _run_subflow_inline(
    ref: str,
    value: Any,
    *,
    session_id: str,
    emitter: ProjectionEmitter,
    policy: ExecutionPolicy,
    max_call_limits: dict[str, int],
    call_counts: dict[str, int],
    principal: Optional[dict[str, Any]] = None,
    root_run_id: Optional[str] = None,
    segment_seq: int = 0,
    node_ops: Optional[dict[str, str]] = None,
) -> Any:
    """Resolve ``ref`` and interpret the frozen child flow inline.

    The child's steps checkpoint into the calling workflow's history;
    ``session_id`` prefixes the child's cids so Idempotency-Keys stay distinct.
    Child call counts are seeded from the caller but NOT merged back. The child
    inherits the caller's principal unchanged.
    """
    resolved = await resolveSubflowStep(ref)
    child = Node.from_json(resolved["flowJson"])
    if node_ops is not None:
        node_ops.update({n.id: n.op.value for n in child.walk()})
    assert_dbos_executable(child)
    pinned = resolved.get("pinnedPures")
    if pinned:
        decode_policy_error(await verifyPuresStep(pinned))
    child_env = DbosEnv(
        manifest=manifest_from_json(resolved.get("manifestJson") or {}),
        emitter=emitter,
        session_id=session_id,
        manifest_json=resolved.get("manifestJson") or {},
        policy=policy,
        max_call_limits=max_call_limits,
        call_counts=call_counts,
        principal=principal,
        root_run_id=root_run_id,
        segment_seq=segment_seq,
        node_ops=node_ops,
    )
    r: Result = await interpret(child, value, child_env)
    return r.value


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
        principal: Optional[dict[str, Any]] = None,
        root_run_id: Optional[str] = None,
        segment_seq: int = 0,
        node_ops: Optional[dict[str, str]] = None,
    ) -> None:
        self.manifest = manifest
        self.emitter = emitter
        self.native_call_retries = True
        self.principal = principal
        self.root_run_id = root_run_id
        self.segment_seq = segment_seq
        self._node_ops = node_ops
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
        if contract_allows_retry(contract):
            attempts = node.ann.max_attempts if node.ann and node.ann.max_attempts is not None else (
                al.retry_max_attempts_for_contract(
                    contract,
                    idempotent_max_attempts=self._policy.idempotent_max_attempts,
                    write_max_attempts=self._policy.write_max_attempts,
                )
            )
        else:
            attempts = 1
        step = callHandIdempotent if max(1, attempts) > 1 else callHandNoRetry
        cache = node.ann.cache.to_json() if node.ann and node.ann.cache is not None else None
        out = await step({
            "tool_ref": toolref_json_from_key(ref_key),
            "value": value, "cid": cid, "cache": cache,
            "principal": self.principal,
            "run_id": self._session,
            "root_run_id": self.root_run_id,
            "segment_seq": self.segment_seq,
            "node_id": node.id,
            "op": "call",
            "kind": "hand",
        })
        return decode_policy_error(out)

    async def invoke_brain(
        self, brain: str, value: Any, cid: str, timeout_s: Optional[int],
    ) -> Any:
        out = await invokeBrainStep({
            "brain": brain, "value": value, "cid": cid,
            "principal": self.principal,
            "run_id": self._session,
            "root_run_id": self.root_run_id,
            "segment_seq": self.segment_seq,
            "op": "think",
            "kind": "brain",
        })
        return decode_policy_error(out)

    async def compile_plan(self, planner: str, value: Any, cid: str) -> Node:
        out = await compilePlanStep({
            "planner": planner, "value": value, "cid": cid,
            "manifest": self._manifest_json,
            "principal": self.principal,
        })
        plan = Node.from_json(decode_policy_error(out))
        assert_dbos_executable(plan)  # a compiled plan must obey backend limits too
        return plan

    async def run_sub(
        self,
        ref: str,
        contract,
        value: Any,
        cid: str,
        node_id: Optional[str] = None,
    ) -> Any:
        # DBOS inline sub-flows do not emit a per-child final marker (deferred); only the top-level chain driver finishes the run.
        result = await _run_subflow_inline(
            ref,
            value,
            session_id=f"{self._session}-sub-{cid}",
            emitter=self.emitter,
            policy=self._policy,
            max_call_limits=self._max_call_limits,
            call_counts=dict(self._call_counts),
            principal=self.principal,
            root_run_id=self.root_run_id,
            segment_seq=self.segment_seq,
            node_ops=self._node_ops,
        )
        try:
            await runSubCaptureStep({
                "ref": ref,
                "value": value,
                "cid": cid,
                "principal": self.principal,
                "run_id": self._session,
                "root_run_id": self.root_run_id,
                "segment_seq": self.segment_seq,
                "node_id": node_id,
                "op": "sub",
                "kind": "flow",
                "causes": (),
                "output": result,
            })
        except Exception as exc:
            from .. import trajectory as _traj

            def _reraise(e: BaseException = exc) -> None:
                raise e

            _traj._best_effort(_reraise)
        return result

    async def run_agent(
        self, controller: str, value: Any, cid: str,
        app_config: Optional[dict[str, Any]] = None,
    ) -> Any:
        # Inline app grants attenuate exactly like the Temporal env
        # (harness._TemporalEnv.run_agent): node config supplies budget/rounds
        # and the tool/subflow allow-lists; contracts come from the parent's
        # frozen manifest filtered to the grant.
        config: Optional[dict[str, Any]] = None
        granted_tools: Optional[list[str]] = None
        granted_subflows: Optional[list[str]] = None
        granted_contracts: Optional[dict[str, dict[str, Any]]] = None
        granted_tools_unconstrained = False

        if app_config is not None:
            config = {}
            if "budget" in app_config:
                config["budget"] = app_config["budget"]
            if "maxRounds" in app_config:
                config["maxRounds"] = app_config["maxRounds"]
            if "ctx" in app_config:
                config["ctx"] = app_config["ctx"]
            if "summarizer" in app_config:
                config["summarizer"] = app_config["summarizer"]

            tools = app_config.get("tools") if "tools" in app_config else None
            granted_tools = None if tools is None else list(tools)
            subflows = app_config.get("subflows") if "subflows" in app_config else None
            granted_subflows = None if subflows is None else list(subflows)
            if tools is not None:
                granted_contracts = al.manifest_contracts_for_agent(
                    self.manifest,
                    granted_tools,
                    self._max_call_limits,
                )

        # Parity with run_sub: parent call counts seed the child agent so an
        # app node cannot reset an already-consumed maxCalls budget. Counts
        # flow one-way; the child's counts are not merged back.
        state_json = (
            al.AgentState(last=value, call_counts=dict(self._call_counts)).to_json()
            if self._call_counts
            else None
        )

        base_id = f"{self._session}-agent-{cid}"
        payload = {
            "controller": controller,
            "sessionId": base_id,
            "input": value,
            "config": config,
            "grantedTools": granted_tools,
            "grantedToolsUnconstrained": granted_tools_unconstrained,
            "grantedSubflows": granted_subflows,
            "grantedContracts": granted_contracts,
            "state": state_json,
            "policy": self._policy.to_json(),
            "resolveSpec": True,
            "principal": self.principal,
            "rootRunId": self.root_run_id,
            "segmentSeq": 0,
        }
        return await _run_agent_chain(payload, base_id=base_id)

    async def human_gate(self, value: Any, cid: str, timeout_s: Optional[int]) -> Any:
        payload = await DBOS.recv_async(
            topic=f"gate:{cid}",
            timeout_seconds=float(timeout_s) if timeout_s else float(_GATE_DEFAULT_TIMEOUT_S),
        )
        if payload is None:
            return {"approved": False, "reason": "timeout", "input": value}
        return payload

    async def sleep(self, seconds: float, cid: str) -> None:
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

    node_ops = {n.id: n.op.value for n in flow.walk()}
    run_id = inp["sessionId"]
    root_run_id = inp.get("rootRunId") or run_id
    segment_seq = int(inp.get("segmentSeq") or 0)
    emitter = _make_projection_emitter(
        node_ops,
        run_id=run_id,
        root_run_id=root_run_id,
        segment_seq=segment_seq,
    )

    env = DbosEnv(
        manifest=manifest_from_json(manifest_json),
        emitter=emitter,
        session_id=run_id,
        manifest_json=manifest_json,
        policy=policy,
        max_call_limits=max_call_limits,
        call_counts=inp.get("callCounts"),
        principal=inp.get("principal"),
        root_run_id=root_run_id,
        segment_seq=segment_seq,
        node_ops=node_ops,
    )
    result: Result = await interpret(flow, inp.get("input"), env)

    if is_continuation(result.value):
        # Enrich the sentinel so the runner can carry budgets into the next segment.
        return {
            CONTINUATION_KEY: continuation_value(result.value),
            "callCounts": env.call_counts_snapshot(),
        }
    return result.value


# --------------------------------------------------------------------------- #
# The agent workflow: one chain segment of one agent loop (Op.APP).
# --------------------------------------------------------------------------- #
@DBOS.workflow(name="ca_agent")
async def agent_workflow(inp: dict) -> Any:
    """Run one history segment of the bounded agent loop.

    ``inp`` is a plain JSON dict (camelCase keys mirroring
    :class:`~composable_agents.execution.harness.AgentInput`, minus the
    Temporal-only session-store fields): ``controller``, ``sessionId``,
    ``input``, ``config``, ``grantedTools``, ``grantedToolsUnconstrained``,
    ``grantedSubflows``, ``grantedContracts``, ``state``, ``policy``,
    ``resolveSpec``. ``sessionId`` is the BASE session id — constant across
    segments — so cids match Temporal's ``{session_id}-round-{n}`` scheme.

    When :func:`~composable_agents.agent_loop.should_continue_as_new` fires
    after a completed action, the segment returns a continuation envelope whose
    value is the entire next-segment payload (state in ``state``, resolved
    config/grants/contracts carried forward, ``resolveSpec`` false).
    """
    policy = ExecutionPolicy.from_json(inp.get("policy"))

    # Resolve config + grant metadata once; later segments arrive with
    # resolveSpec=False and the already-merged values (mirrors AgentWorkflow.run).
    config = dict(inp.get("config") or {})
    granted = inp.get("grantedTools")
    granted_subflows = inp.get("grantedSubflows")
    contracts = dict(inp.get("grantedContracts") or {})
    grants_supplied = (
        inp.get("grantedTools") is not None or bool(inp.get("grantedToolsUnconstrained"))
    )
    subflows_supplied = inp.get("grantedSubflows") is not None

    if inp.get("resolveSpec", True):
        spec = await resolveAgentSpecStep(inp["controller"])
        merged_config = dict(spec.get("config") or {})
        merged_config.update(config)
        config = merged_config
        spec_granted = spec.get("grantedTools")
        if grants_supplied:
            capability_tools = spec.get("capabilityTools")
            if (
                not inp.get("grantedToolsUnconstrained")
                and granted is not None
                and capability_tools is not None
            ):
                granted = sorted(set(granted) & set(capability_tools))
        else:
            granted = spec_granted
        merged_contracts = dict(spec.get("grantedContracts") or {})
        merged_contracts.update(contracts)
        contracts = merged_contracts
        spec_subflows = spec.get("grantedSubflows")
        if subflows_supplied:
            capability_subflows = spec.get("capabilitySubflows")
            if granted_subflows is not None and capability_subflows is not None:
                granted_subflows = sorted(set(granted_subflows) & set(capability_subflows))
        else:
            granted_subflows = spec_subflows

    cfg = al.AgentConfig.from_json(config or {})
    unconstrained = bool(inp.get("grantedToolsUnconstrained")) or granted is None
    granted_set = set(granted or [])
    state = (
        al.AgentState.from_json(inp["state"]) if inp.get("state")
        else al.AgentState(last=inp.get("input"))
    )
    # Per-segment continue-as-new cadence: carried state keeps the cumulative
    # round count, so truncation is measured from this segment's entry round,
    # not from zero (parity with the Temporal AgentWorkflow).
    baseline_round = state.round

    # Emitter only serves inline sub-flow interpretation; the agent loop itself
    # emits no per-round projection events (parity with Temporal's AgentWorkflow,
    # where the parent flow's Op.APP node carries the Planned/Did pair).
    session = inp["sessionId"]
    principal = inp.get("principal")
    root_run_id = inp.get("rootRunId") or session
    segment_seq = int(inp.get("segmentSeq") or 0)
    node_ops: dict[str, str] = {}
    emitter = _make_projection_emitter(
        node_ops,
        run_id=session,
        root_run_id=root_run_id,
        segment_seq=segment_seq,
    )

    # controller_turn mutates `state` in place and returns the same object, so
    # these cid closures read state.round live: one deterministic cid per round.
    # controller_turn attaches the transcript plan beside the controller value
    # for transcript-scoped rounds; split those keys onto the step input.
    _transcript_keys = ("transcript", "ctx", "summarizer", "summary")

    async def _invoke(payload: dict) -> Any:
        value = {k: v for k, v in payload.items() if k not in _transcript_keys}
        out = await invokeBrainStep({
            "brain": inp["controller"], "value": value,
            "cid": f"{session}-round-{state.round}",
            "principal": principal,
            "transcript": payload.get("transcript"),
            "ctx": payload.get("ctx"),
            "summarizer": payload.get("summarizer"),
            "summary": payload.get("summary"),
            "run_id": session,
            "root_run_id": root_run_id,
            "segment_seq": segment_seq,
            "op": "think",
            "kind": "brain",
        })
        return decode_policy_error(out)

    async def _call(tool: str, value: Any) -> Any:
        contract = al.contract_for_tool(tool, contracts)
        attempts = (
            al.retry_max_attempts_for_contract(
                contract,
                idempotent_max_attempts=policy.idempotent_max_attempts,
                write_max_attempts=policy.write_max_attempts,
            )
            if contract_allows_retry(contract)
            else 1
        )
        step = callHandIdempotent if max(1, attempts) > 1 else callHandNoRetry
        out = await step({
            "tool_ref": toolref_json_from_key(tool), "value": value,
            "cid": f"{session}-call-{state.round}", "cache": None,
            "principal": principal,
            "run_id": session,
            "root_run_id": root_run_id,
            "segment_seq": segment_seq,
            "op": "call",
            "kind": "hand",
        })
        return decode_policy_error(out)

    async def _sub(ref: str, value: Any) -> Any:
        return await _run_subflow_inline(
            ref,
            value,
            session_id=f"{session}-sub-{state.round}",
            emitter=emitter,
            policy=policy,
            max_call_limits=al.max_call_limits_from_contracts(contracts) or {},
            call_counts=dict(state.call_counts),
            principal=principal,
            root_run_id=root_run_id,
            segment_seq=segment_seq,
            node_ops=node_ops,
        )

    prod_gap: list[str] = []
    step = controller_turn(
        cfg=cfg,
        invoke_controller=_invoke,
        call_tool=_call,
        run_subflow=_sub,
        granted=None if unconstrained else granted_set,
        granted_subflows=None if granted_subflows is None else set(granted_subflows),
        contracts=contracts,
        mode=cfg.mode,
        prod_gap=prod_gap,
        run_input=inp.get("input"),
    )
    halt = pre_round(cfg)
    finalize = make_finalize(prod_gap)

    while True:
        pre = halt(state)
        if pre is not None:
            return finalize(
                al.terminal_result(pre.status, state, output=pre.output, reason=pre.reason)
            )
        result = await step(state)
        if isinstance(result, Halt):
            return finalize(
                al.terminal_result(result.status, state, output=result.output, reason=result.reason)
            )
        state = result
        if policy.trace_content_refs and state.trace:
            state.trace[-1].output_ref = await putBlobStep(
                {"tenant": session, "value": state.last}
            )
        # §6 seam, POST-action exactly like the Temporal harness: a top-of-loop
        # check would re-fire forever once round >= continueAsNewAfter.
        if al.should_continue_as_new(state, cfg, baseline_round=baseline_round):
            return {CONTINUATION_KEY: {
                "controller": inp["controller"],
                "sessionId": session,
                "input": inp.get("input"),
                "config": config,
                "grantedTools": None if unconstrained else sorted(granted_set),
                "grantedToolsUnconstrained": unconstrained,
                "grantedSubflows": granted_subflows,
                "grantedContracts": contracts,
                "state": state.to_json(),
                "policy": policy.to_json(),
                "resolveSpec": False,
                "principal": principal,
                "rootRunId": root_run_id,
                "segmentSeq": segment_seq + 1,
            }}


# --------------------------------------------------------------------------- #
# Client helpers.
# --------------------------------------------------------------------------- #
async def run_flow_dbos(
    flow_json: dict[str, Any],
    manifest_json: dict[str, Any],
    *,
    session_id: str,
    input: Any = None,
    policy: Optional[ExecutionPolicy] = None,
    pinned_pures: Optional[dict[str, str]] = None,
    max_call_limits: Optional[dict[str, int]] = None,
    queue: Optional[Queue] = None,
    max_segments: int = 1000,
    principal: Optional[dict[str, Any]] = None,
    root_run_id: Optional[str] = None,
) -> Any:
    """Run a frozen flow to settlement, following continuation segments.

    Segment ``i`` runs as workflow id ``session_id`` (i=0) /
    ``f"{session_id}-seg{i}"``, so a re-submission with the same session id is
    deduplicated by DBOS's one-execution-per-workflow-id guarantee, and a chain
    is inspectable in ``workflow_status`` by id prefix. Call this from inside a
    DBOS workflow for durable chaining (each enqueue checkpoints); from plain
    code, a crash between segments stalls the chain -- the same contract as any
    other dispatch your process performs.
    """
    assert_dbos_executable(Node.from_json(flow_json))
    seg_input = input
    call_counts: Optional[dict[str, int]] = None
    effective_root_run_id = root_run_id or session_id
    if effective_root_run_id == session_id:
        try:
            await startTrajectoryStep({
                "runId": session_id,
                "rootRunId": effective_root_run_id,
                "segmentSeq": 0,
                "input": input,
                "cid": f"{effective_root_run_id}:root",
            })
        except Exception as exc:
            from .. import trajectory as _traj

            def _reraise(e: BaseException = exc) -> None:
                raise e

            _traj._best_effort(_reraise)
    for seg in range(max_segments):
        wfid = session_id if seg == 0 else f"{session_id}-seg{seg}"
        seg_payload = {
            "sessionId": wfid,
            "input": seg_input,
            "flowJson": flow_json,
            "manifestJson": manifest_json,
            "pinnedPures": pinned_pures,
            "maxCallLimits": max_call_limits,
            "callCounts": call_counts,
            "policy": (policy or ExecutionPolicy()).to_json(),
            # Every segment of the chain keeps the run's tenant identity.
            "principal": principal,
            "rootRunId": effective_root_run_id,
            "segmentSeq": seg,
        }
        with SetWorkflowID(wfid):
            if queue is not None:
                handle = await queue.enqueue_async(flow_workflow, seg_payload)
            else:
                handle = await DBOS.start_workflow_async(flow_workflow, seg_payload)
        out = await handle.get_result()
        if not is_continuation(out):
            try:
                await finishTrajectoryStep({
                    "runId": effective_root_run_id,
                    "rootRunId": effective_root_run_id,
                    "status": "completed",
                    "finalValue": out,
                    "segmentSeq": seg,
                })
            except Exception as exc:
                from .. import trajectory as _traj

                def _reraise(e: BaseException = exc) -> None:
                    raise e

                _traj._best_effort(_reraise)
            return out
        call_counts = out.get("callCounts") if isinstance(out, dict) else None
        seg_input = continuation_value(out)
    raise ComposableAgentsError(
        f"flow {session_id!r} did not settle within {max_segments} segments"
    )


async def _run_agent_chain(
    payload: dict,
    *,
    base_id: str,
    queue: Optional[Queue] = None,
    max_segments: int = 1000,
) -> Any:
    """Drive ``ca_agent`` segments to settlement (shared by
    :func:`run_agent_dbos` and :meth:`DbosEnv.run_agent`).

    Segment ``i`` runs as workflow id ``base_id`` (i=0) / ``f"{base_id}-seg{i}"``;
    the next segment's full payload rides in the continuation envelope.
    """
    root_run_id = payload.get("rootRunId") or base_id
    if int(payload.get("segmentSeq") or 0) == 0 and root_run_id == base_id:
        try:
            await startTrajectoryStep({
                "runId": base_id,
                "rootRunId": root_run_id,
                "segmentSeq": 0,
                "input": payload.get("input"),
                "cid": f"{root_run_id}:root",
            })
        except Exception as exc:
            from .. import trajectory as _traj

            def _reraise(e: BaseException = exc) -> None:
                raise e

            _traj._best_effort(_reraise)
    for seg in range(max_segments):
        wfid = base_id if seg == 0 else f"{base_id}-seg{seg}"
        with SetWorkflowID(wfid):
            if queue is not None:
                handle = await queue.enqueue_async(agent_workflow, payload)
            else:
                handle = await DBOS.start_workflow_async(agent_workflow, payload)
        out = await handle.get_result()
        if not is_continuation(out):
            try:
                # F1: an agent chain finishes ITS OWN run (base_id), stitched to
                # the root via rootRunId -- never the root run. A child Op.APP
                # agent inherits rootRunId from its parent, so targeting the root
                # here would overwrite the root's final with the child's result.
                await finishTrajectoryStep({
                    "runId": base_id,
                    "rootRunId": payload.get("rootRunId") or base_id,
                    "status": "completed",
                    "finalValue": out,
                    "segmentSeq": int(payload.get("segmentSeq") or seg),
                })
            except Exception as exc:
                from .. import trajectory as _traj

                def _reraise(e: BaseException = exc) -> None:
                    raise e

                _traj._best_effort(_reraise)
            return out
        payload = continuation_value(out)
    raise ComposableAgentsError(
        f"agent {base_id!r} did not settle within {max_segments} segments"
    )


async def run_agent_dbos(
    controller: str,
    *,
    session_id: str,
    input: Any = None,
    config: Optional[dict[str, Any]] = None,
    granted_tools: Optional[list[str]] = None,
    granted_tools_unconstrained: bool = False,
    granted_subflows: Optional[list[str]] = None,
    granted_contracts: Optional[dict[str, dict[str, Any]]] = None,
    policy: Optional[ExecutionPolicy] = None,
    queue: Optional[Queue] = None,
    max_segments: int = 1000,
    resolve_spec: bool = True,
    principal: Optional[dict[str, Any]] = None,
    root_run_id: Optional[str] = None,
) -> dict[str, Any]:
    """Run an agent loop to settlement, following continuation segments.

    The DBOS counterpart of dispatching Temporal's ``AgentWorkflow`` directly.
    Segment ``i`` runs as workflow id ``session_id`` (i=0) /
    ``f"{session_id}-seg{i}"``, so a re-submission with the same session id is
    deduplicated by DBOS's one-execution-per-workflow-id guarantee. Returns the
    agent's terminal result dict (``status``, ``output``, ``rounds``, ``cost``,
    ``trace``).
    """
    payload = {
        "controller": controller,
        "sessionId": session_id,
        "input": input,
        "config": config,
        "grantedTools": granted_tools,
        "grantedToolsUnconstrained": granted_tools_unconstrained,
        "grantedSubflows": granted_subflows,
        "grantedContracts": granted_contracts,
        "state": None,
        "policy": (policy or ExecutionPolicy()).to_json(),
        "resolveSpec": resolve_spec,
        "principal": principal,
        "rootRunId": root_run_id or session_id,
        "segmentSeq": 0,
    }
    return await _run_agent_chain(
        payload, base_id=session_id, queue=queue, max_segments=max_segments
    )


async def submit_human_dbos(workflow_id: str, cid: str, value: Any) -> None:
    """Release a parked human gate in a running ``ca_flow`` or ``ca_agent`` workflow.

    ``cid`` is the gate's activation id; with the DBOS env's session-prefixed
    cids, the first gate of a root flow is ``f"{workflow_id}/{gate_node_id}@1"``.
    For a gate inside an agent-invoked sub-flow, ``workflow_id`` is the agent
    segment's workflow id and the cid prefix is ``f"{session}-sub-{round}"``.
    """
    await DBOS.send_async(workflow_id, value, topic=f"gate:{cid}")
