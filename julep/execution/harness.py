"""The durable harness (blueprint §2): Temporal workflows that run frozen IR.

This is the only module that binds the framework to Temporal. It supplies an
:class:`~julep.execution.interpreter.Env` whose effect handlers are
``workflow.execute_activity`` / child-workflow calls, and whose concurrency
primitives are the deterministic ``asyncio`` the Temporal sandbox provides. The
interpreter itself is unchanged between this and the in-memory test env — that
separation is the whole point of the §2 design.

What Temporal provides, mapped to the blueprint:

* **Durability / recovery** = workflow history + replay. Leases, heartbeats and
  retries are activity-level concerns expressed as timeouts and a
  per-tool :class:`RetryPolicy` derived from each frozen contract
  (:func:`_retry_policy_for`): a read or natively-idempotent tool retries
  liberally; a non-idempotent write retries cautiously and only behind the
  ``Idempotency-Key`` the ``callTool`` activity sends.
* **Tools / Reasoners** = activities (``callTool`` / ``invokeReasoner``), which run
  outside the sandbox and hold all IO and non-determinism.
* **Sub** (``run_sub``) = a child :class:`FlowWorkflow`. The Joined firewall is
  structural — :func:`~julep.shapes.surface_shape` already makes a
  Sub opaque (Pipeline) at the surface — so the child's value crosses while its
  internal shape does not leak into the parent's projection.
* **Agent** (``run_agent``) = a child :class:`AgentWorkflow`, deliberately *its
  own* workflow so its ``continue_as_new`` truncates only the agent's history,
  not the parent flow's.
* **Projection** is built by a *derived* path, not here: the in-workflow
  :class:`~julep.projection.ProjectionEmitter` exists only to thread
  causal ids deterministically and is exposed read-only via a query; the durable
  observability sink (Postgres / OTel) is fed by an interceptor over history
  (see :mod:`julep.execution.otel`). The workflow performs no
  projection IO, which keeps replay deterministic.

Human gates become a signal + ``wait_condition`` (durable wait, optional
timeout). Everything in :func:`FlowWorkflow.run` and :func:`AgentWorkflow.run`
must stay deterministic: no wall-clock, no RNG, no ambient IO — all of that is
behind the activity boundary.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, AsyncIterator, Awaitable, Callable, Mapping, Optional, Sequence

from temporalio import activity, workflow
from temporalio.common import RetryPolicy
from temporalio.client import WorkflowFailureError, WorkflowUpdateFailedError
from temporalio.exceptions import ActivityError, ApplicationError

# Best-effort swallow paths log via stdlib logging: it never raises, works
# outside a live workflow runtime (so the helpers stay unit-testable by direct
# call), and does not mutate the trajectory best-effort counter on replay, unlike
# workflow.logger (which requires a workflow context) or trajectory._best_effort
# (which would inflate the counter every time workflow code re-executes).
_LOG = logging.getLogger(__name__)


if not getattr(WorkflowUpdateFailedError, "_julep_repr_includes_cause", False):
    def _workflow_update_failed_repr(self: WorkflowUpdateFailedError) -> str:
        cause = getattr(self, "__cause__", None)
        if cause is None:
            return f"{type(self).__name__}({self.args[0]!r})"
        return f"{type(self).__name__}({self.args[0]!r}, cause={cause!r})"

    WorkflowUpdateFailedError.__repr__ = _workflow_update_failed_repr  # type: ignore[method-assign]
    WorkflowUpdateFailedError._julep_repr_includes_cause = True  # type: ignore[attr-defined]


def _batch_error_reason(result: Any) -> Optional[str]:
    if not isinstance(result, dict) or not result.get("__batch_error__"):
        return None
    reason = result.get("reason")
    return reason if isinstance(reason, str) else None


def _batch_signal_error_reason(reason: Any) -> str:
    if not isinstance(reason, str) or not reason:
        return "batch_error"
    if reason == "expired" or reason.startswith("batch entry "):
        return "batch_error"
    return reason


# Import the pure pieces through the sandbox-safe import pass so Temporal's
# workflow sandbox does not trip over disallowed modules at definition time.
with workflow.unsafe.imports_passed_through():
    from .. import agent_loop as al
    from ..capabilities import Budget
    from ..continuation import continuation_value, is_continuation
    from ..contracts import ToolContract, contract_allows_retry, manifest_from_json
    from ..errors import JulepError, SessionTurnError
    from ..ir import Ann, CallStep, EMIT_TOOL, NativeTool, Node, RECV_TOOL
    from ..kinds import Effect, Op
    from ..projection import EventType, InMemoryProjection, ProjectionEmitter
    from ..purity import executor_of as _executor_of_from_registry
    from ..purity import get_pure as _get_pure_from_registry
    from ..qos import QoSTier
    from ..transcript import (
        TRANSCRIPT_SCOPES,
        split_summary_reply,
        transcript_for,
        unwrap_reply_meta,
    )
    from .policy import ExecutionPolicy
    from .effects import toolref_json_from_key as _toolref_json_from_key
    from .session_store import value_fingerprint
    from .projection_store import finalize_projection_run, persist_projection_batch
    from .timeouts import activity_timeout
    from .interpreter import (
        BranchThunk,
        Result,
        SessionClosed,
        call_contract,
        call_ref_key,
        gather_bounded,
        interpret,
        race_first_from_thunks,
    )
    from .activities import (
        CallToolInput,
        CommitStateInput,
        CommitValueInput,
        CompilePlanInput,
        InvokeReasonerInput,
        LoadStateInput,
        LoadValueInput,
        PutBlobInput,
        ResolveQoSInput,
        RunSubInput,
        VerifyPuresInput,
        callTool,
        commitState,
        commitValue,
        compilePlan,
        invokeReasoner,
        loadState,
        loadValue,
        putBlob,
        resolveAgentSpec,
        resolveQoS,
        resolveRuntimeCapabilities,
        resolveSubflow,
        verifyPures,
    )
    from ..validate import blocking, validate
    from ..session import SessionEvent


# Errors that represent a settled policy decision must never be retried.
_NON_RETRYABLE = [
    "CapabilityDenied",
    "PlanRejected",
    "ValidationError",
    "FreezeError",
    "PureDriftError",
    "PrincipalRequired",
]


def _reserved_channel_tool_name(node: Node) -> Optional[str]:
    step = node.step
    if (
        node.op == Op.PRIM
        and isinstance(step, CallStep)
        and isinstance(step.tool, NativeTool)
        and step.tool.name in (RECV_TOOL, EMIT_TOOL)
    ):
        return step.tool.name
    return None


@activity.defn(name="finishTrajectory")
async def finishTrajectory(inp: dict[str, Any]) -> None:
    import time

    from .. import trajectory as _traj
    from . import effects as _effects

    sink = _effects._TRAJECTORY_SINK
    if sink is None:
        return
    run_id = inp.get("runId")
    root_run_id = inp.get("rootRunId") or run_id
    status = inp.get("status", "completed")
    await _effects.record_marker_step(
        kind="final",
        run_id=run_id,
        root_run_id=root_run_id,
        segment_seq=inp.get("segmentSeq"),
        value=inp.get("result"),
        cid=f"{run_id}:final",
        value_kind="output",
    )
    _traj._best_effort(lambda: sink.finish_run(run_id, status, time.time()))


@activity.defn(name="startTrajectory")
async def startTrajectory(inp: dict[str, Any]) -> None:
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


@activity.defn(name="flushStructural")
async def flushStructural(inp: dict[str, Any]) -> None:
    from .. import trajectory as _traj
    from ..projection import ProjectionEvent
    from . import effects as _effects

    sink = _effects._TRAJECTORY_SINK
    if sink is None:
        return
    run_id = inp.get("runId")
    root_run_id = inp.get("rootRunId") or run_id
    segment_seq = int(inp.get("segmentSeq") or 0)
    node_ops = dict(inp.get("nodeOps") or {})
    events = inp.get("events") or []
    structural = _traj.ProjectionTrajectorySink(
        sink,
        run_id=run_id,
        root_run_id=root_run_id,
        segment_seq=segment_seq,
        node_ops=node_ops,
    )
    for raw in events:
        def _feed(raw: dict[str, Any] = raw) -> None:
            structural.append(ProjectionEvent.from_json(raw))

        _traj._best_effort(_feed)


@activity.defn(name="runSubCapture")
async def runSubCapture(inp: dict[str, Any], output: Any) -> None:
    from .. import trajectory as _traj
    from . import effects as _effects

    try:
        await _effects.runSub(
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
            output,
        )
    except Exception as exc:
        def _reraise(e: BaseException = exc) -> None:
            raise e

        _traj._best_effort(_reraise)


def _bundle_ref_child_input_enabled() -> bool:
    try:
        return workflow.patched("bundle-ref-child-input-v1")
    except Exception:
        # Unit tests sometimes exercise Env methods outside a workflow runtime.
        return False


def _bundle_aware_verify_pures_enabled() -> bool:
    try:
        return workflow.patched("bundle-aware-verify-pures-v1")
    except Exception:
        return False


def _bundle_bound_verify_pures_enabled() -> bool:
    try:
        return workflow.patched("bundle-bound-verify-pures-v1")
    except Exception:
        return False


async def _verify_pures_for_flow(
    *,
    flow_json: dict[str, Any],
    pinned_pures: Optional[dict[str, str]],
    bundle: Optional[list[dict[str, str]]],
) -> None:
    bundle_bound_verify = bundle is not None and _bundle_bound_verify_pures_enabled()
    if pinned_pures is None and not bundle_bound_verify:
        return
    verify_pures_input: Any = pinned_pures or {}
    if bundle_bound_verify:
        verify_pures_input = VerifyPuresInput(
            pinned=pinned_pures or {},
            bundle=bundle,
            flow_json=flow_json,
        )
    elif bundle is not None and _bundle_aware_verify_pures_enabled():
        verify_pures_input = VerifyPuresInput(pinned=pinned_pures or {}, bundle=bundle)
    await workflow.execute_activity(
        verifyPures,
        verify_pures_input,
        start_to_close_timeout=timedelta(seconds=10),
        retry_policy=RetryPolicy(
            maximum_attempts=1,
            non_retryable_error_types=_NON_RETRYABLE,
        ),
    )


def _retry_policy_for(
    contract: ToolContract,
    policy: ExecutionPolicy,
    ann: Optional[Ann] = None,
) -> RetryPolicy:
    """Per-tool retry policy: liberal for idempotent reads, cautious otherwise."""
    attempts = 1
    if contract_allows_retry(contract):
        attempts = ann.max_attempts if ann is not None and ann.max_attempts is not None else (
            al.retry_max_attempts_for_contract(
                contract,
                idempotent_max_attempts=policy.idempotent_max_attempts,
                write_max_attempts=policy.write_max_attempts,
            )
        )
        attempts = max(1, attempts)
    initial_interval_s = max(0.0, float(
        ann.retry_interval_s
        if ann is not None and ann.retry_interval_s is not None
        else policy.initial_retry_s
    ))
    backoff = max(1.0, float(
        ann.backoff_rate
        if ann is not None and ann.backoff_rate is not None
        else policy.retry_backoff
    ))
    return RetryPolicy(
        initial_interval=timedelta(seconds=initial_interval_s),
        backoff_coefficient=backoff,
        maximum_interval=timedelta(seconds=policy.max_retry_interval_s),
        maximum_attempts=attempts,
        non_retryable_error_types=_NON_RETRYABLE,
    )


def _reasoner_retry(policy: ExecutionPolicy) -> RetryPolicy:
    """Engine retries for reasoner/plan activities (``reasoner_max_attempts``).

    Workers whose ``LlmCaller`` owns resilience (fallback chains, breakers —
    ``make_resilient_llm_caller``) should run with ``reasoner_max_attempts=1`` so
    these blind retries don't multiply the caller's ladder.
    """
    return RetryPolicy(
        initial_interval=timedelta(seconds=1),
        backoff_coefficient=2.0,
        maximum_interval=timedelta(seconds=60),
        maximum_attempts=policy.reasoner_max_attempts,
        non_retryable_error_types=_NON_RETRYABLE,
    )


# --------------------------------------------------------------------------- #
# Workflow inputs (Temporal serializes these via the data converter).
# --------------------------------------------------------------------------- #
@dataclass
class FlowInput:
    """Run a frozen flow. Supply ``flow_json`` directly, or a ``ref`` to resolve."""

    session_id: str
    input: Any = None
    flow_json: Optional[dict[str, Any]] = None
    manifest_json: Optional[dict[str, Any]] = None
    pinned_pures: Optional[dict[str, str]] = None
    max_call_limits: Optional[dict[str, int]] = None
    call_counts: Optional[dict[str, int]] = None
    ref: Optional[str] = None
    policy: Optional[dict[str, Any]] = None
    # Run principal: opaque tenant/credential reference (never a secret),
    # workflow input so it is replay-stable and absent from the frozen artifact.
    principal: Optional[dict[str, Any]] = None
    # Signed CAS bundle pointers for custom pures referenced by this flow.
    # Worker-side STORE_URL and JULEP_BUNDLE_ALLOWED_SIGNERS remain authoritative.
    bundle: Optional[list[dict[str, str]]] = None
    runtime_declarations_ref: Optional[dict[str, Any]] = None
    # Trajectory identity: root_run_id is root session_id; segment_seq bumps on continue_as_new.
    root_run_id: Optional[str] = None
    segment_seq: int = 0
    queue_lanes: Optional[dict[str, str]] = None
    # Durable projection egress is opt-in so old workflow histories replay with
    # precisely the same command sequence. ``run_id`` is the API-facing id;
    # the Temporal workflow id remains the persisted event-stream identity.
    run_id: Optional[str] = None
    emit_projection: bool = False
    projection_batch_size: int = 20
    projection_batch_interval_s: float = 2.0


@dataclass
class SessionInput:
    """Run a long-lived root ``Op.LOOP`` session."""

    session_id: str
    flow_json: dict[str, Any]
    manifest_json: Optional[dict[str, Any]]
    init: Any
    max_call_limits: Optional[dict[str, int]] = None
    call_counts: Optional[dict[str, int]] = None
    pinned_pures: Optional[dict[str, str]] = None
    budget: Optional[dict[str, Any]] = None
    spent: float = 0.0
    bundle: Optional[list[dict[str, str]]] = None
    runtime_declarations_ref: Optional[dict[str, Any]] = None
    in_channel: str = "in"
    out_channel: str = "out"
    policy: Optional[dict[str, Any]] = None
    principal: Optional[dict[str, Any]] = None
    root_run_id: Optional[str] = None
    segment_seq: int = 0
    history_threshold: Optional[int] = None
    channel_capacity: Optional[int] = None
    state_cursor: Optional[int] = None
    has_carrier: bool = False
    carrier: Any = None
    inbox: Optional[dict[str, list[dict[str, Any]]]] = None
    out_buffers: Optional[dict[str, list[dict[str, Any]]]] = None
    ack_cursors: Optional[dict[str, int]] = None
    seq_cursors: Optional[dict[str, int]] = None
    closed: bool = False
    close_reason: Optional[str] = None
    idempotency_index: Optional[dict[str, dict[str, int]]] = None
    idempotency_fp: Optional[dict[str, dict[str, str]]] = None
    event_log: Optional[list[dict[str, Any]]] = None
    event_seq: int = 0
    event_ack: int = 0
    queue_lanes: Optional[dict[str, str]] = None


@dataclass
class AgentInput:
    controller: str
    session_id: str
    input: Any = None
    config: Optional[dict[str, Any]] = None
    granted_tools: Optional[list[str]] = None
    granted_tools_unconstrained: bool = False
    granted_subflows: Optional[list[str]] = None
    granted_contracts: Optional[dict[str, dict[str, Any]]] = None
    tool_defs: Optional[list[dict[str, Any]]] = None
    state: Optional[dict[str, Any]] = None      # set on continue-as-new
    state_cursor: Optional[int] = None          # set on continue-as-new under the store path
    use_session_store: bool = False             # opt-in: route state through loadState/commitState
    policy: Optional[dict[str, Any]] = None
    resolve_spec: bool = True
    principal: Optional[dict[str, Any]] = None  # run principal (see FlowInput.principal)
    runtime_declarations_ref: Optional[dict[str, Any]] = None
    # Trajectory identity: root_run_id is root session_id; segment_seq bumps on continue_as_new.
    root_run_id: Optional[str] = None
    segment_seq: int = 0
    queue_lanes: Optional[dict[str, str]] = None
    subflow_queues: Optional[dict[str, str]] = None


def _resolve_child_queue(
    sub_queue: Optional[str], lanes: Optional[dict[str, str]]
) -> Optional[str]:
    """Resolve a subflow's authored queue against the env lane map.

    None -> None (inherit parent task queue, byte-for-byte). Present + known
    lane -> mapped concrete queue. Present + unknown -> the raw string.

    mem-mcp role lanes map to one worker Deployment + KEDA ScaledObject per
    lane. Interactive (RECORD plan/execute, checkin/recall) vs background
    (sweeps, rollups, clustering, dream) is the two-lane starter, not the
    ceiling.
    """
    if not sub_queue:
        return None
    if lanes and sub_queue in lanes:
        return lanes[sub_queue]
    return sub_queue




# --------------------------------------------------------------------------- #
# Temporal-backed Env.
# --------------------------------------------------------------------------- #
class _TemporalEnv:
    """An :class:`Env` whose effects are Temporal activities / child workflows."""

    def __init__(
        self,
        manifest,
        emitter: ProjectionEmitter,
        *,
        session_id: str,
        manifest_json: Optional[dict[str, Any]],
        policy: ExecutionPolicy,
        gate_waiter: Callable[[Any, str, Optional[int]], Awaitable[Any]],
        recv_waiter: Optional[Callable[[str, str, Optional[int]], Awaitable[Any]]] = None,
        emit_sink: Optional[Callable[[str, Any, str], Awaitable[None]]] = None,
        batch_waiter: Optional[Callable[[str, Optional[int]], Awaitable[Any]]] = None,
        workflow_id: Optional[str] = None,
        max_call_limits: Optional[dict[str, int]] = None,
        call_counts: Optional[dict[str, int]] = None,
        principal: Optional[dict[str, Any]] = None,
        root_run_id: Optional[str] = None,
        segment_seq: int = 0,
        queue_lanes: Optional[dict[str, str]] = None,
        runtime_declarations_ref: Optional[dict[str, Any]] = None,
    ) -> None:
        self.manifest = manifest
        self.emitter = emitter
        self.native_call_retries = True
        self.principal = principal
        self.root_run_id = root_run_id
        self.segment_seq = segment_seq
        self._queue_lanes = queue_lanes
        self._runtime_declarations_ref = runtime_declarations_ref
        self._session = session_id
        self._manifest_json = manifest_json
        self._policy = policy
        self._gate_waiter = gate_waiter
        self._recv_waiter = recv_waiter
        self._emit_sink = emit_sink
        self._batch_waiter = batch_waiter
        self._workflow_id = workflow_id
        self._max_call_limits = dict(max_call_limits or {})
        self._call_counts: dict[str, int] = dict(call_counts or {})
        self._cid = 0
        self._child = 0

    # --- identity / pures --- #
    def next_cid(self, node_id: str) -> str:
        self._cid += 1
        return f"{node_id}@{self._cid}"

    def get_pure(self, name: str):
        # Pure functions are resolved from the real worker-process registry via
        # a passthrough import. Importing lazily inside the workflow sandbox
        # would create an isolated registry copy and hide worker-registered
        # pures. Registered pures must be deterministic by contract (see
        # purity.py), so the lookup remains replay-safe.
        executor = _executor_of_from_registry(name)
        # FIXME(P5-3): this rejects a native-tier pure LATE (mid-workflow, at pure-call
        # time) rather than at bundle resolution. Reject native bundle pures on the
        # Temporal worker at resolve_and_register so it fails fast, not mid-flow. See TODOS.md.
        if executor == "native_venv":
            raise JulepError(
                f"pure {name!r} is native-tier (native_venv): native-dependency pures "
                "cannot execute inside the durable workflow interpreter, which forbids "
                "subprocess/IO and requires determinism. Native pures are not supported "
                "on the Temporal harness in P5; run them on the in-memory/dry-run path "
                "or keep them off the durable flow."
            )
        return _get_pure_from_registry(name)

    def charge_call(self, tool_key: str) -> None:
        limit = self._max_call_limits.get(tool_key)
        if limit is None:
            return
        count = self._call_counts.get(tool_key, 0)
        if count >= limit:
            from ..errors import CapabilityDenied

            raise CapabilityDenied(f"tool {tool_key!r} exceeded maxCalls={limit}")
        self._call_counts[tool_key] = count + 1

    def call_counts_snapshot(self) -> dict[str, int]:
        return dict(self._call_counts)

    def _child_id(self, kind: str, cid: str) -> str:
        self._child += 1
        return f"{self._session}-{kind}-{self._child}-{cid}"

    # --- effect handlers --- #
    async def run_call(self, node: Node, value: Any, cid: str) -> Any:
        # Frozen calls resolve through the manifest; a staged plan's calls are
        # admitted but unfrozen, so late-bind by tool ref (and use a conservative
        # contract for retry shaping).
        ref_key = call_ref_key(node, self.manifest)
        contract = call_contract(node, self.manifest)
        timeout_s = node.ann.timeout if node.ann else None
        cache = node.ann.cache.to_json() if node.ann and node.ann.cache is not None else None
        return await workflow.execute_activity(
            callTool,
            CallToolInput(
                tool_ref=_toolref_json_from_key(ref_key),
                value=value,
                cid=cid,
                cache=cache,
                principal=self.principal,
                run_id=self._session,
                root_run_id=self.root_run_id,
                segment_seq=self.segment_seq,
                node_id=node.id,
                op="call",
                kind="tool",
            ),
            start_to_close_timeout=activity_timeout(timeout_s, self._policy.tool_timeout_s),
            retry_policy=_retry_policy_for(contract, self._policy, node.ann),
        )

    async def invoke_reasoner(
        self,
        reasoner: str,
        value: Any,
        cid: str,
        timeout_s: Optional[int],
        batchable: bool = False,
    ) -> Any:
        # Resolve + RECORD the QoS tier once, in an activity, so replay reads the
        # same tier from history and takes the same (async-or-not) branch. A
        # genuine activity failure propagates (retries/fails the workflow loudly);
        # only an unrecognized tier value falls back to the STANDARD default.
        resolved = await workflow.execute_activity(
            resolveQoS,
            ResolveQoSInput(
                reasoner=reasoner,
                node_batchable=batchable,
                principal=self.principal,
                cid=cid,
                run_id=self._session,
                root_run_id=self.root_run_id,
                segment_seq=self.segment_seq,
                timeout_s=timeout_s,
                runtime_declarations_ref=self._runtime_declarations_ref,
            ),
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                non_retryable_error_types=_NON_RETRYABLE,
            ),
        )
        try:
            tier = QoSTier(resolved)
        except (TypeError, ValueError):
            tier = QoSTier.STANDARD
        if tier is QoSTier.BATCH and self._batch_waiter is not None:
            from .reasoner_batch import (
                ReasonerCall as _ReasonerCall,
                provider_safe_custom_id as _provider_safe_custom_id,
                SubmitReasonerBatchInput as _SubmitReasonerBatchInput,
            )

            custom_id = _provider_safe_custom_id(
                f"{self._session}:{self.segment_seq}:{cid}"
            )
            await workflow.execute_activity(
                "submitReasonerBatch",
                _SubmitReasonerBatchInput(
                    provider="",
                    qos=tier.value,
                    principal_key="",
                    call=_ReasonerCall(
                        reasoner=reasoner,
                        value=value,
                        principal=self.principal,
                        transcript=None,
                        cid=cid,
                        reply_to=self._workflow_id or self._session,
                        custom_id=custom_id,
                        runtime_declarations_ref=self._runtime_declarations_ref,
                    ),
                ),
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    non_retryable_error_types=_NON_RETRYABLE,
                ),
            )
            try:
                result = await self._batch_waiter(custom_id, timeout_s)
            except asyncio.TimeoutError:
                reply = await self._invoke_reasoner_sync(
                    reasoner, value, cid, timeout_s, QoSTier.STANDARD
                )
                return {
                    "__julep_meta__": {
                        "tier": QoSTier.STANDARD.value,
                        "promoted": True,
                        "reason": "batch_timeout",
                    },
                    "reply": unwrap_reply_meta(reply),
                }
            err_reason = _batch_error_reason(result)
            if err_reason is not None:
                reply = await self._invoke_reasoner_sync(
                    reasoner, value, cid, timeout_s, QoSTier.STANDARD
                )
                return {
                    "__julep_meta__": {
                        "tier": QoSTier.STANDARD.value,
                        "promoted": True,
                        "reason": err_reason,
                    },
                    "reply": unwrap_reply_meta(reply),
                }
            return result

        return await self._invoke_reasoner_sync(reasoner, value, cid, timeout_s, tier)

    async def _invoke_reasoner_sync(
        self,
        reasoner: str,
        value: Any,
        cid: str,
        timeout_s: Optional[int],
        tier: QoSTier,
    ) -> Any:
        return await workflow.execute_activity(
            invokeReasoner,
            InvokeReasonerInput(
                reasoner=reasoner,
                value=value,
                cid=cid,
                principal=self.principal,
                run_id=self._session,
                root_run_id=self.root_run_id,
                segment_seq=self.segment_seq,
                op="think",
                kind="reasoner",
                qos=tier.value,
                runtime_declarations_ref=self._runtime_declarations_ref,
            ),
            start_to_close_timeout=activity_timeout(timeout_s, self._policy.reasoner_timeout_s),
            retry_policy=_reasoner_retry(self._policy),
        )

    async def compile_plan(self, planner: str, value: Any, cid: str) -> Node:
        plan_json = await workflow.execute_activity(
            compilePlan,
            CompilePlanInput(
                planner=planner,
                value=value,
                cid=cid,
                manifest=self._manifest_json,
                principal=self.principal,
                runtime_declarations_ref=self._runtime_declarations_ref,
            ),
            start_to_close_timeout=timedelta(seconds=self._policy.plan_timeout_s),
            retry_policy=_reasoner_retry(self._policy),
        )
        return Node.from_json(plan_json)

    async def run_sub(
        self,
        ref: str,
        contract,
        value: Any,
        cid: str,
        node_id: Optional[str] = None,
    ) -> Any:
        # A Sub is a child flow; the firewall is structural (surface shape is
        # already opaque), so the child's value crosses unchanged. The child
        # inherits the parent's principal unchanged (no substitution API).
        child_id = self._child_id("sub", cid)
        bundle = await self._bundle_for_ref_child(ref)
        sub_queue = getattr(contract, "queue", None)
        resolved = _resolve_child_queue(sub_queue, self._queue_lanes)
        start_kwargs: dict[str, Any] = {
            "id": child_id,
            "task_timeout": timedelta(seconds=self._policy.sub_task_timeout_s),
        }
        if resolved is not None:
            start_kwargs["task_queue"] = resolved
        result = await workflow.execute_child_workflow(
            FlowWorkflow.run,
            FlowInput(
                session_id=child_id,
                input=value,
                ref=ref,
                policy=self._policy.to_json(),
                max_call_limits=self._max_call_limits,
                call_counts=dict(self._call_counts),
                principal=self.principal,
                root_run_id=self.root_run_id,
                bundle=bundle,
                queue_lanes=(self._queue_lanes or None),
            ),
            **start_kwargs,
        )
        from .. import trajectory as _traj

        try:
            await workflow.execute_activity(
                runSubCapture,
                args=[
                    {
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
                    },
                    result,
                ],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    maximum_attempts=1,
                    non_retryable_error_types=_NON_RETRYABLE,
                ),
            )
        except Exception as exc:
            def _reraise(e: BaseException = exc) -> None:
                raise e

            _traj._best_effort(_reraise)
        return result

    async def _bundle_for_ref_child(self, ref: str) -> Optional[list[dict[str, str]]]:
        if not _bundle_ref_child_input_enabled():
            return None
        resolved = await workflow.execute_activity(
            resolveSubflow,
            ref,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3, non_retryable_error_types=_NON_RETRYABLE),
        )
        bundle = resolved.get("bundle")
        return bundle if isinstance(bundle, list) else None

    async def run_agent(
        self,
        controller: str,
        value: Any,
        cid: str,
        app_config: Optional[dict[str, Any]] = None,
    ) -> Any:
        child_id = self._child_id("agent", cid)
        config: Optional[dict[str, Any]] = None
        granted_tools: Optional[list[str]] = None
        granted_subflows: Optional[list[str]] = None
        granted_contracts: Optional[dict[str, dict[str, Any]]] = None
        subflow_queues: Optional[dict[str, str]] = None
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
            if "roundNote" in app_config:
                config["roundNote"] = app_config["roundNote"]
            if "nativeTools" in app_config:
                config["nativeTools"] = app_config["nativeTools"]
            if "requireToolCall" in app_config:
                config["requireToolCall"] = app_config["requireToolCall"]

            tools = app_config.get("tools") if "tools" in app_config else None
            granted_tools = None if tools is None else list(tools)
            subflows = app_config.get("subflows") if "subflows" in app_config else None
            granted_subflows = None if subflows is None else list(subflows)
            if "subflowQueues" in app_config:
                subflow_queues = app_config["subflowQueues"]
            if tools is not None:
                granted_contracts = al.manifest_contracts_for_agent(
                    self.manifest,
                    granted_tools,
                    self._max_call_limits,
                )

        # Parity with run_sub: parent call counts seed the child agent so an
        # app node cannot reset an already-consumed maxCalls budget. Terminal
        # child counts merge back below as cumulative high-water marks.
        state_json = (
            al.AgentState(last=value, call_counts=dict(self._call_counts)).to_json()
            if self._call_counts
            else None
        )

        out = await workflow.execute_child_workflow(
            AgentWorkflow.run,
            AgentInput(
                controller=controller,
                session_id=child_id,
                input=value,
                config=config,
                granted_tools=granted_tools,
                granted_tools_unconstrained=granted_tools_unconstrained,
                granted_subflows=granted_subflows,
                granted_contracts=granted_contracts,
                subflow_queues=subflow_queues,
                state=state_json,
                policy=self._policy.to_json(),
                principal=self.principal,
                runtime_declarations_ref=self._runtime_declarations_ref,
                root_run_id=self.root_run_id,
                queue_lanes=(self._queue_lanes or None),
            ),
            id=child_id,
            task_timeout=timedelta(seconds=self._policy.agent_task_timeout_s),
        )
        if isinstance(out, dict) and isinstance(out.get("callCounts"), dict):
            for tool, count in out["callCounts"].items():
                key = str(tool)
                self._call_counts[key] = max(
                    self._call_counts.get(key, 0),
                    int(count),
                )
        return out

    async def human_gate(self, value: Any, cid: str, timeout_s: Optional[int]) -> Any:
        return await self._gate_waiter(value, cid, timeout_s)

    async def recv(self, channel: str, cid: str, timeout_s: Optional[int]) -> Any:
        if self._recv_waiter is None:
            raise SessionClosed(f"session channel {channel!r} is closed")
        return await self._recv_waiter(channel, cid, timeout_s)

    async def emit(self, channel: str, value: Any, cid: str) -> None:
        if self._emit_sink is None:
            return
        await self._emit_sink(channel, value, cid)

    async def sleep(self, seconds: float, cid: str) -> None:
        # asyncio.sleep inside a Temporal workflow is a durable timer.
        await asyncio.sleep(seconds)

    # --- concurrency (deterministic under Temporal's asyncio) --- #
    async def gather(self, coros: Sequence[Awaitable[Any]]) -> list[Any]:
        return await gather_bounded(coros, max_parallel=self._policy.max_parallel)

    async def race_first(
        self, branches: Sequence[BranchThunk], *, kind: str, m: int, hedge_ms: Optional[int]
    ) -> Any:
        async def wait_first(
            waitset: Sequence[Awaitable[Any]],
        ) -> tuple[set[Awaitable[Any]], set[Awaitable[Any]]]:
            done, pending = await workflow.wait(list(waitset), return_when=asyncio.FIRST_COMPLETED)
            return set(done), set(pending)

        return await race_first_from_thunks(
            branches,
            kind=kind,
            m=m,
            hedge_ms=hedge_ms,
            wait_first=wait_first,
        )


def _make_emitter() -> tuple[InMemoryProjection, ProjectionEmitter]:
    """A fresh in-workflow projection used only to thread causal ids.

    Deterministic (logical clock), no IO. The durable projection is built
    out-of-band from history; this one is surfaced read-only via a query.
    """
    store = InMemoryProjection()
    return store, ProjectionEmitter(store)


# --------------------------------------------------------------------------- #
# FlowWorkflow — walks a frozen IR tree to completion.
# --------------------------------------------------------------------------- #
@workflow.defn(name="FlowWorkflow")
class FlowWorkflow:
    def __init__(self) -> None:
        self._human_inbox: dict[str, Any] = {}
        self._reasoner_inbox: dict[str, Any] = {}
        self._resolved_reasoners: set[str] = set()
        self._open_gates: set[str] = set()
        self._store: Optional[InMemoryProjection] = None
        self._egress_cursor = 0
        self._egress_done = False
        self._egress_task: Optional[asyncio.Future[None]] = None

    # ----- human gate plumbing --------------------------------------------- #
    @workflow.signal(name="submitHuman")
    def submit_human(self, payload: dict[str, Any]) -> None:
        """Deliver a human decision keyed by activation id (``cid``)."""
        self._human_inbox[payload["cid"]] = payload.get("value")

    @workflow.signal(name="submitReasonerResult")
    def submit_reasoner_result(self, payload: dict[str, Any]) -> None:
        custom_id = payload["custom_id"]
        if custom_id in self._resolved_reasoners:
            return
        if payload.get("error"):
            self._reasoner_inbox[custom_id] = {
                "__batch_error__": True,
                "reason": _batch_signal_error_reason(payload.get("reason")),
            }
            return
        self._reasoner_inbox[custom_id] = payload.get("reply")

    async def _await_human(self, value: Any, cid: str, timeout_s: Optional[int]) -> Any:
        timeout = timedelta(seconds=timeout_s) if timeout_s else None
        self._open_gates.add(cid)
        try:
            await workflow.wait_condition(lambda: cid in self._human_inbox, timeout=timeout)
        except asyncio.TimeoutError:
            return {"approved": False, "reason": "timeout", "input": value}
        finally:
            self._open_gates.discard(cid)
        return self._human_inbox.pop(cid)

    async def _await_reasoner_result(self, custom_id: str, timeout_s: Optional[int]) -> Any:
        timeout = timedelta(seconds=timeout_s) if timeout_s else None
        try:
            await workflow.wait_condition(
                lambda: custom_id in self._reasoner_inbox, timeout=timeout
            )
        except asyncio.TimeoutError:
            self._resolved_reasoners.add(custom_id)
            raise
        self._resolved_reasoners.add(custom_id)
        return self._reasoner_inbox.pop(custom_id)

    @workflow.query(name="openGates")
    def open_gates(self) -> list[str]:
        """Activation ids (``cid``) currently parked waiting on a human decision.

        A client signals ``submitHuman`` with one of these cids to release the
        corresponding gate. This is the precise list to drive a review UI —
        unlike the projection's ``pending``, it excludes structural activations
        (a ``seq``/``par`` that is merely mid-flight) and names only real gates.
        """
        return sorted(self._open_gates)

    # ----- observability query --------------------------------------------- #
    @workflow.query(name="projection")
    def projection(self) -> dict[str, Any]:
        """Read-only pomset snapshot for a replay UI (derived, not durable)."""
        if self._store is None:
            return {"events": [], "costByShape": {}}
        return {
            "events": [e.to_json() for e in self._store.events()],
            "costByShape": self._store.cost_by_shape(),
            "pending": self._store.pending(),
        }

    def _projection_event_payload(self, event: Any) -> dict[str, Any]:
        """Serialize one event and attach its raw value for activity-side capture."""
        payload = event.to_json()
        store = self._store
        if (
            store is not None
            and event.type == EventType.DID
            and event.value_ref is not None
            and store.values.has(event.value_ref)
        ):
            payload["rawValue"] = store.values.get(event.value_ref)
        return payload

    async def _flush_projection_batch(self, inp: FlowInput) -> None:
        store = self._store
        if store is None:
            return
        events = store.events()
        pending = len(events) - self._egress_cursor
        if pending <= 0:
            return
        size = min(pending, max(1, inp.projection_batch_size))
        batch = events[self._egress_cursor : self._egress_cursor + size]
        await workflow.execute_activity(
            persist_projection_batch,
            {
                "runId": inp.run_id or inp.session_id,
                "workflowId": workflow.info().workflow_id,
                "segmentSeq": inp.segment_seq,
                "events": [self._projection_event_payload(event) for event in batch],
            },
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                backoff_coefficient=2.0,
                maximum_interval=timedelta(seconds=10),
            ),
        )
        # Advance only after the activity succeeds. Activity retries therefore
        # replay the identical batch and rely on the store's conflict key.
        self._egress_cursor += size

    async def _egress_loop(self, inp: FlowInput) -> None:
        store = self._store
        if store is None:
            return
        batch_size = max(1, inp.projection_batch_size)
        interval_s = max(0.0, inp.projection_batch_interval_s)
        while True:
            # An empty buffer owns no timer. This matters for long human gates:
            # the workflow history stays quiet until an event actually arrives.
            await workflow.wait_condition(
                lambda: self._egress_done
                or len(store.events()) > self._egress_cursor
            )
            if self._egress_done and len(store.events()) <= self._egress_cursor:
                return

            deadline = workflow.now() + timedelta(seconds=interval_s)
            while not self._egress_done:
                pending = len(store.events()) - self._egress_cursor
                if pending >= batch_size:
                    break
                remaining = max((deadline - workflow.now()).total_seconds(), 0.0)
                if remaining <= 0:
                    break
                try:
                    await workflow.wait_condition(
                        lambda: self._egress_done
                        or len(store.events()) - self._egress_cursor >= batch_size,
                        timeout=remaining,
                    )
                except asyncio.TimeoutError:
                    pass
            await self._flush_projection_batch(inp)

    async def _drain_projection(self, inp: FlowInput) -> None:
        """Stop and drain the single egress loop; safe to call more than once."""
        if not inp.emit_projection:
            return
        self._egress_done = True
        task = self._egress_task
        if task is not None:
            await task

    def _terminal_projection_event(
        self,
        inp: FlowInput,
        *,
        status: str,
        error: Optional[str],
    ) -> dict[str, Any]:
        events = self._store.events() if self._store is not None else []
        causes = [events[-1].event_id] if events else []
        ts = events[-1].ts + 1.0 if events else 0.0
        event: dict[str, Any] = {
            "eventId": "__terminal__",
            "type": "Did" if status == "completed" else "Failed",
            "node": "__run__",
            "cid": f"{inp.run_id or inp.session_id}:terminal",
            "ts": ts,
            "causes": causes,
            "attrs": {"terminal": True, "status": status},
        }
        if error is not None:
            event["error"] = error
        return event

    async def _finalize_projection(
        self,
        inp: FlowInput,
        *,
        status: str,
        result: Any = None,
        error: Optional[str] = None,
    ) -> None:
        payload: dict[str, Any] = {
            "runId": inp.run_id or inp.session_id,
            "workflowId": workflow.info().workflow_id,
            "segmentSeq": inp.segment_seq,
            "status": status,
            "terminalEvent": self._terminal_projection_event(
                inp, status=status, error=error
            ),
            "error": error,
            "finishedAt": workflow.now().timestamp(),
        }
        if status == "completed":
            payload["rawValue"] = result
        await workflow.execute_activity(
            finalize_projection_run,
            payload,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                backoff_coefficient=2.0,
                maximum_interval=timedelta(seconds=10),
            ),
        )

    async def _start_trajectory(self, inp: FlowInput) -> None:
        from .. import trajectory as _traj

        root_run_id = inp.root_run_id or inp.session_id
        if inp.segment_seq != 0 or root_run_id != inp.session_id:
            return
        try:
            await workflow.execute_activity(
                startTrajectory,
                {
                    "runId": inp.session_id,
                    "rootRunId": root_run_id,
                    "segmentSeq": inp.segment_seq,
                    "input": inp.input,
                    "cid": f"{root_run_id}:root",
                },
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    maximum_attempts=1,
                    non_retryable_error_types=_NON_RETRYABLE,
                ),
            )
        except Exception as exc:
            def _reraise(e: BaseException = exc) -> None:
                raise e

            _traj._best_effort(_reraise)

    async def _finish_trajectory(
        self,
        run_id: str,
        result: Any = None,
        *,
        root_run_id: Optional[str] = None,
        status: str = "completed",
        segment_seq: int = 0,
    ) -> None:
        try:
            await workflow.execute_activity(
                finishTrajectory,
                {
                    "runId": run_id,
                    "rootRunId": root_run_id,
                    "status": status,
                    "result": result,
                    "segmentSeq": segment_seq,
                },
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    maximum_attempts=1,
                    non_retryable_error_types=_NON_RETRYABLE,
                ),
            )
        except Exception as exc:
            _LOG.warning("trajectory dispatch failed (best-effort, swallowed): %s", exc)

    async def _flush_structural(self, inp: FlowInput, node_ops: dict[str, str]) -> None:
        if self._store is None:
            return
        payload = {
            "runId": inp.session_id,
            "rootRunId": (inp.root_run_id or inp.session_id),
            "segmentSeq": inp.segment_seq,
            "nodeOps": node_ops,
            "events": [e.to_json() for e in self._store.events()],
        }
        try:
            await workflow.execute_activity(
                flushStructural,
                payload,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    maximum_attempts=1,
                    non_retryable_error_types=_NON_RETRYABLE,
                ),
            )
        except Exception as exc:
            _LOG.warning("trajectory dispatch failed (best-effort, swallowed): %s", exc)

    # ----- entrypoint ------------------------------------------------------- #
    @workflow.run
    async def run(self, inp: FlowInput) -> Any:
        policy = ExecutionPolicy.from_json(inp.policy)
        flow_json = inp.flow_json
        manifest_json = inp.manifest_json
        pinned_pures = inp.pinned_pures
        max_call_limits = inp.max_call_limits
        call_counts = inp.call_counts
        bundle = inp.bundle
        runtime_declarations_ref = inp.runtime_declarations_ref

        # A ref-only input resolves to its frozen flow + manifest via activity
        # (kept outside the deterministic sandbox).
        if flow_json is None:
            if inp.ref is None:
                raise ValueError("FlowInput needs either flow_json or ref")
            resolved = await workflow.execute_activity(
                resolveSubflow,
                inp.ref,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3, non_retryable_error_types=_NON_RETRYABLE),
            )
            flow_json = resolved["flowJson"]
            manifest_json = resolved.get("manifestJson", {})
            if pinned_pures is None:
                pinned_pures = resolved.get("pinnedPures")
            if max_call_limits is None:
                max_call_limits = resolved.get("maxCalls")
            if bundle is None:
                bundle = resolved.get("bundle")
            if runtime_declarations_ref is None:
                resolved_declarations_ref = resolved.get("runtimeDeclarationsRef")
                if isinstance(resolved_declarations_ref, dict):
                    runtime_declarations_ref = resolved_declarations_ref

        # Pure source lookup reads the worker registry, so it stays in an
        # activity. Each FlowWorkflow verifies the pins supplied with that flow;
        # ref children verify their own pins when the subflow registry carries
        # pureSourceHashes/pinnedPures, without inheriting parent registry state.
        await _verify_pures_for_flow(
            flow_json=flow_json,
            pinned_pures=pinned_pures,
            bundle=bundle,
        )

        if max_call_limits is None:
            runtime_caps = await workflow.execute_activity(
                resolveRuntimeCapabilities,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(
                    maximum_attempts=1,
                    non_retryable_error_types=_NON_RETRYABLE,
                ),
            )
            max_call_limits = runtime_caps.get("maxCalls", {})

        flow = Node.from_json(flow_json)
        nodes = list(flow.walk())
        for node in nodes:
            if node.op == Op.LOOP:
                raise ApplicationError(
                    "FlowWorkflow cannot run a session Op.LOOP; use SessionWorkflow for LOOP artifacts",
                    type="ValidationError",
                    non_retryable=True,
                )
            reserved = _reserved_channel_tool_name(node)
            if reserved is not None:
                raise ApplicationError(
                    f"FlowWorkflow cannot run reserved session channel operation {reserved!r}; "
                    "use SessionWorkflow for recv/emit channel artifacts",
                    type="ValidationError",
                    non_retryable=True,
                )
        node_ops = {n.id: n.op.value for n in nodes}
        manifest = manifest_from_json(manifest_json or {})

        store, emitter = _make_emitter()
        self._store = store
        if inp.emit_projection:
            self._egress_task = asyncio.ensure_future(self._egress_loop(inp))
        env = _TemporalEnv(
            manifest=manifest,
            emitter=emitter,
            session_id=inp.session_id,
            manifest_json=manifest_json,
            policy=policy,
            gate_waiter=self._await_human,
            batch_waiter=self._await_reasoner_result,
            workflow_id=inp.session_id,
            max_call_limits=max_call_limits,
            call_counts=call_counts,
            principal=inp.principal,
            root_run_id=(inp.root_run_id or inp.session_id),
            segment_seq=inp.segment_seq,
            queue_lanes=inp.queue_lanes,
            runtime_declarations_ref=runtime_declarations_ref,
        )
        await self._start_trajectory(inp)

        try:
            result: Result = await interpret(flow, inp.input, env)
        except asyncio.CancelledError:
            if inp.emit_projection:
                try:
                    await self._drain_projection(inp)
                    await self._finalize_projection(inp, status="canceled")
                except (Exception, asyncio.CancelledError) as projection_exc:
                    _LOG.warning(
                        "projection cancellation finalization failed (best-effort): %s",
                        projection_exc,
                    )
            raise
        except JulepError as exc:
            if inp.emit_projection:
                await self._drain_projection(inp)
                await self._finalize_projection(
                    inp,
                    status="failed",
                    error=str(exc),
                )
            raise ApplicationError(
                str(exc),
                type=type(exc).__name__,
                non_retryable=True,
            ) from exc
        except Exception as exc:
            if inp.emit_projection:
                await self._drain_projection(inp)
                await self._finalize_projection(
                    inp,
                    status="failed",
                    error=repr(exc),
                )
            raise ApplicationError(
                repr(exc),
                type=type(exc).__name__,
                non_retryable=True,
            ) from exc
        if is_continuation(result.value):
            if inp.emit_projection:
                await self._drain_projection(inp)
            await self._flush_structural(inp, node_ops)
            # Chain: same frozen flow, new input, cumulative call counts so
            # maxCalls budgets span the whole chain, truncated history. The
            # principal is carried so the run keeps its tenant identity.
            workflow.continue_as_new(
                FlowInput(
                    session_id=inp.session_id,
                    input=continuation_value(result.value),
                    flow_json=flow_json,
                    manifest_json=manifest_json,
                    pinned_pures=pinned_pures,
                    max_call_limits=max_call_limits,
                    call_counts=env.call_counts_snapshot(),
                    policy=inp.policy,
                    principal=inp.principal,
                    root_run_id=(inp.root_run_id or inp.session_id),
                    segment_seq=inp.segment_seq + 1,
                    bundle=bundle,
                    runtime_declarations_ref=runtime_declarations_ref,
                    queue_lanes=inp.queue_lanes,
                    run_id=inp.run_id,
                    emit_projection=inp.emit_projection,
                    projection_batch_size=inp.projection_batch_size,
                    projection_batch_interval_s=inp.projection_batch_interval_s,
                )
            )
        if inp.emit_projection:
            await self._drain_projection(inp)
            await self._finalize_projection(
                inp,
                status="completed",
                result=result.value,
            )
        await self._flush_structural(inp, node_ops)
        await self._finish_trajectory(
            inp.session_id,
            result.value,
            root_run_id=(inp.root_run_id or inp.session_id),
            segment_seq=inp.segment_seq,
        )
        return result.value


# --------------------------------------------------------------------------- #
# SessionWorkflow — a durable root Op.LOOP with channel updates.
# --------------------------------------------------------------------------- #
class RecvTimeout(Exception):
    def __init__(self, channel: str) -> None:
        self.channel = channel
        super().__init__(f"session channel {channel!r} receive timed out")


@workflow.defn(name="SessionWorkflow")
class SessionWorkflow:
    def __init__(self) -> None:
        self._pending: dict[str, list[dict[str, Any]]] = {}
        self._out_buffers: dict[str, list[dict[str, Any]]] = {}
        self._ack_cursors: dict[str, int] = {}
        self._seq_cursors: dict[str, int] = {}
        self._idempotency_index: dict[str, dict[str, int]] = {}
        self._idempotency_fp: dict[str, dict[str, str]] = {}
        self._open_receives: dict[str, int] = {}
        self._closed: bool = False
        self._close_reason: Optional[str] = None
        self._closed_event_sent: bool = False
        self._event_log: list[dict[str, Any]] = []
        self._event_seq: int = 0
        self._event_ack: int = 0
        self._turn_started: bool = False
        self._carrier_current: Any = None
        self._capacity: Optional[int] = None
        self._proj: Optional[InMemoryProjection] = None

    @staticmethod
    def _in_seq_key(channel: str) -> str:
        return f"in:{channel}"

    @staticmethod
    def _out_seq_key(channel: str) -> str:
        return f"out:{channel}"

    @staticmethod
    def _consumed_seq_key(channel: str) -> str:
        return f"consumed:{channel}"

    def _next_seq(self, key: str) -> int:
        seq = self._seq_cursors.get(key, 0) + 1
        self._seq_cursors[key] = seq
        return seq

    def _raise_if_send_rejected(
        self,
        channel: str,
        idempotency_key: Any,
    ) -> None:
        if self._closed:
            raise ApplicationError(
                "session is closed",
                type="ValidationError",
                non_retryable=True,
            )
        if idempotency_key is not None:
            prior = self._idempotency_index.get(channel, {}).get(str(idempotency_key))
            if prior is not None:
                return
        pending = self._pending.get(channel, [])
        if self._capacity is not None and len(pending) >= self._capacity:
            raise ApplicationError(
                f"ChannelFull: channel {channel!r} is full",
                type="ChannelFull",
                non_retryable=True,
            )

    def _evict_acked(self, channel: str) -> None:
        acked = self._ack_cursors.get(channel, 0)
        if acked <= 0:
            return
        self._out_buffers[channel] = [
            item for item in self._out_buffers.get(channel, [])
            if int(item.get("seq", 0)) > acked
        ]

    def _evict_acked_events(self) -> None:
        if self._event_ack <= 0:
            return
        self._event_log = [
            item
            for item in self._event_log
            if int(item.get("eseq", 0)) > self._event_ack
        ]

    def _ack_outputs_through_event_ack(self) -> None:
        if self._event_ack <= 0:
            return
        touched: set[str] = set()
        for item in self._event_log:
            if (
                int(item.get("eseq", 0)) <= self._event_ack
                and item.get("kind") == "emit"
            ):
                channel = str(item.get("channel", "out"))
                seq = int(item.get("seq", 0))
                self._ack_cursors[channel] = max(
                    self._ack_cursors.get(channel, 0),
                    seq,
                )
                touched.add(channel)
        for channel in touched:
            self._evict_acked(channel)

    def _append_event(self, kind: str, **fields: Any) -> None:
        self._event_seq += 1
        record = {"eseq": self._event_seq, "kind": kind, **fields}
        self._event_log.append(record)
        self._evict_acked_events()

    def _append_turn_done_if_started(self) -> None:
        if not self._turn_started:
            return
        self._append_event("turn", turn="done")
        self._turn_started = False

    def _append_closed_once(self) -> None:
        if self._closed_event_sent:
            return
        self._closed_event_sent = True
        self._append_event("closed", reason=self._close_reason)

    def _rehydrate(self, inp: SessionInput) -> None:
        pre_pending = {
            channel: [dict(item) for item in items]
            for channel, items in self._pending.items()
        }
        pre_seq_cursors = dict(self._seq_cursors)
        pre_idempotency_index = {
            channel: dict(entries)
            for channel, entries in self._idempotency_index.items()
        }
        pre_idempotency_fp = {
            channel: dict(entries)
            for channel, entries in self._idempotency_fp.items()
        }
        pre_closed = self._closed
        pre_close_reason = self._close_reason
        self._pending = {
            str(channel): [dict(item) for item in items]
            for channel, items in (inp.inbox or {}).items()
        }
        self._out_buffers = {
            str(channel): [dict(item) for item in items]
            for channel, items in (inp.out_buffers or {}).items()
        }
        self._ack_cursors = {
            str(channel): int(seq) for channel, seq in (inp.ack_cursors or {}).items()
        }
        for channel in list(self._out_buffers):
            self._evict_acked(channel)
        self._seq_cursors = dict(inp.seq_cursors or {})
        for key, seq in pre_seq_cursors.items():
            self._seq_cursors[key] = max(self._seq_cursors.get(key, 0), int(seq))
        self._idempotency_index = {
            str(channel): {str(key): int(seq) for key, seq in entries.items()}
            for channel, entries in (inp.idempotency_index or {}).items()
        }
        self._idempotency_fp = {
            str(channel): {str(key): str(fp) for key, fp in entries.items()}
            for channel, entries in (inp.idempotency_fp or {}).items()
        }
        restamped: dict[str, dict[int, int]] = {}
        for channel, items in pre_pending.items():
            pending = self._pending.setdefault(channel, [])
            channel_map = restamped.setdefault(channel, {})
            carried_high_water = int(
                (inp.seq_cursors or {}).get(self._in_seq_key(channel), 0)
            )
            for raw in items:
                item = dict(raw)
                old_seq = int(item.get("seq", 0))
                if old_seq <= carried_high_water:
                    new_seq = self._next_seq(self._in_seq_key(channel))
                    item["seq"] = new_seq
                    channel_map[old_seq] = new_seq
                else:
                    new_seq = old_seq
                pending.append(item)
                key = item.get("idempotency_key")
                if key is not None:
                    self._idempotency_index.setdefault(channel, {})[str(key)] = new_seq
                    fp = pre_idempotency_fp.get(channel, {}).get(str(key))
                    if fp is not None:
                        self._idempotency_fp.setdefault(channel, {})[str(key)] = str(fp)
        for channel, entries in pre_idempotency_index.items():
            target = self._idempotency_index.setdefault(channel, {})
            for key, seq in entries.items():
                if str(key) not in target:
                    target[str(key)] = restamped.get(channel, {}).get(int(seq), int(seq))
        for channel, entries in pre_idempotency_fp.items():
            target = self._idempotency_fp.setdefault(channel, {})
            for key, fp in entries.items():
                target[str(key)] = str(fp)
        self._closed = bool(inp.closed) or pre_closed
        self._close_reason = pre_close_reason if pre_closed else inp.close_reason
        self._capacity = inp.channel_capacity
        self._event_log = [dict(item) for item in (inp.event_log or [])]
        self._event_seq = int(inp.event_seq)
        for item in self._event_log:
            self._event_seq = max(self._event_seq, int(item.get("eseq", 0)))
        self._event_ack = int(inp.event_ack)
        self._ack_outputs_through_event_ack()
        self._evict_acked_events()

    @workflow.update(name="send")
    def send(self, payload: dict[str, Any]) -> dict[str, Any]:
        channel = str(payload.get("channel", "in"))
        idempotency_key = payload.get("idempotency_key")
        self._raise_if_send_rejected(channel, idempotency_key)
        if idempotency_key is not None:
            key = str(idempotency_key)
            fingerprint = value_fingerprint(payload.get("value"))
            channel_index = self._idempotency_index.setdefault(channel, {})
            prior = channel_index.get(key)
            if prior is not None:
                prior_fingerprint = self._idempotency_fp.get(channel, {}).get(key)
                if (
                    prior_fingerprint is not None
                    and prior_fingerprint != fingerprint
                ):
                    raise ApplicationError(
                        f"idempotency_key {key!r} reused with a different payload "
                        f"on channel {channel!r}",
                        type="ValidationError",
                        non_retryable=True,
                    )
                return {"seq": prior, "channel": channel}

        pending = self._pending.setdefault(channel, [])
        seq = self._next_seq(self._in_seq_key(channel))
        item = {"seq": seq, "value": payload.get("value")}
        if idempotency_key is not None:
            key = str(idempotency_key)
            item["idempotency_key"] = key
            self._idempotency_index.setdefault(channel, {})[key] = seq
            self._idempotency_fp.setdefault(channel, {})[key] = value_fingerprint(
                payload.get("value")
            )
        pending.append(item)
        return {"seq": seq, "channel": channel}

    @send.validator
    def validate_send(self, payload: dict[str, Any]) -> None:
        self._raise_if_send_rejected(
            str(payload.get("channel", "in")),
            payload.get("idempotency_key"),
        )

    @workflow.update(name="close")
    def close(self, payload: dict[str, Any]) -> dict[str, Any]:
        reason = payload.get("reason")
        self._close_reason = (
            reason if reason is None or isinstance(reason, str) else str(reason)
        )
        self._closed = True
        return {"closed": True}

    @workflow.update(name="ack")
    def ack(self, payload: dict[str, Any]) -> dict[str, Any]:
        channel = str(payload["channel"])
        seq = int(payload["seq"])
        acked = max(self._ack_cursors.get(channel, 0), seq)
        self._ack_cursors[channel] = acked
        self._evict_acked(channel)
        return {"channel": channel, "acked": acked}

    @workflow.update(name="ack_events")
    def ack_events(self, payload: dict[str, Any]) -> dict[str, Any]:
        eseq = int(payload["eseq"])
        self._event_ack = max(self._event_ack, eseq)
        self._ack_outputs_through_event_ack()
        self._evict_acked_events()
        return {"acked": self._event_ack}

    @workflow.query(name="events")
    def events(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self._event_log]

    @workflow.query(name="open_receives")
    def open_receives(self) -> list[dict[str, Any]]:
        return [
            {"channel": channel, "seq": seq}
            for channel, seq in sorted(self._open_receives.items())
        ]

    @workflow.query(name="state")
    def state(self) -> dict[str, Any]:
        return {
            "emitted": {
                channel: [dict(item) for item in items]
                for channel, items in sorted(self._out_buffers.items())
            },
            "ack_cursors": dict(self._ack_cursors),
            "capacity": self._capacity,
            "carrier": self._carrier_current,
            "closed": self._closed,
            "close_reason": self._close_reason,
            "pending": {
                channel: len(items)
                for channel, items in sorted(self._pending.items())
            },
        }

    async def _recv_waiter(
        self,
        channel: str,
        cid: str,
        timeout_s: Optional[int],
    ) -> Any:
        del cid
        timeout = timedelta(seconds=timeout_s) if timeout_s is not None else None
        self._open_receives[channel] = (
            self._seq_cursors.get(self._consumed_seq_key(channel), 0) + 1
        )
        try:
            await workflow.wait_condition(
                lambda: bool(self._pending.get(channel)) or self._closed,
                timeout=timeout,
            )
        except asyncio.TimeoutError as exc:
            if self._closed:
                raise SessionClosed(f"session channel {channel!r} is closed") from exc
            raise RecvTimeout(channel) from exc
        finally:
            self._open_receives.pop(channel, None)

        pending = self._pending.setdefault(channel, [])
        if pending:
            item = pending.pop(0)
            seq = int(item.get("seq", 0))
            self._seq_cursors[self._consumed_seq_key(channel)] = seq
            self._turn_started = True
            self._append_event("turn", turn="started")
            return item.get("value")
        raise SessionClosed(f"session channel {channel!r} is closed")

    async def _emit_sink(self, channel: str, value: Any, cid: str) -> None:
        del cid
        if self._capacity is not None:
            await workflow.wait_condition(
                lambda: (
                    len(self._out_buffers.get(channel, [])) < self._capacity
                    or self._closed
                )
            )
        # Capacity is best-effort at close: once closed, append the final emit
        # anyway so close-flush semantics preserve in-flight output.
        seq = self._next_seq(self._out_seq_key(channel))
        self._out_buffers.setdefault(channel, []).append({"seq": seq, "payload": value})
        self._append_event("emit", channel=channel, seq=seq, payload=value)

    async def _load_carrier(self, inp: SessionInput) -> Any:
        if inp.has_carrier:
            return inp.carrier
        if inp.state_cursor is None:
            return inp.init
        return await workflow.execute_activity(
            loadValue,
            LoadValueInput(session_id=inp.session_id, cursor=inp.state_cursor),
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                non_retryable_error_types=_NON_RETRYABLE,
            ),
        )

    async def _commit_carrier(
        self,
        inp: SessionInput,
        *,
        base_cursor: Optional[int],
        carrier: Any,
    ) -> int:
        return await workflow.execute_activity(
            commitValue,
            CommitValueInput(
                session_id=inp.session_id,
                base=base_cursor or 0,
                value=carrier,
                value_hash=value_fingerprint(carrier),
            ),
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                non_retryable_error_types=_NON_RETRYABLE,
            ),
        )

    def _should_continue_as_new(self, inp: SessionInput) -> bool:
        if inp.history_threshold is None:
            return False
        return workflow.info().get_current_history_length() >= inp.history_threshold

    def _continue_as_new(
        self,
        inp: SessionInput,
        *,
        carrier: Any,
        state_cursor: int,
        flow_json: dict[str, Any],
        manifest_json: Optional[dict[str, Any]],
        policy: ExecutionPolicy,
        call_counts: dict[str, int],
        spent: float,
    ) -> None:
        assert not self._turn_started, (
            "continue_as_new must only happen at a turn boundary (quiesce, never mid-body)"
        )
        workflow.continue_as_new(
            SessionInput(
                session_id=inp.session_id,
                flow_json=flow_json,
                manifest_json=manifest_json,
                init=inp.init,
                max_call_limits=inp.max_call_limits,
                call_counts=call_counts,
                pinned_pures=inp.pinned_pures,
                budget=inp.budget,
                spent=spent,
                bundle=inp.bundle,
                runtime_declarations_ref=inp.runtime_declarations_ref,
                in_channel=inp.in_channel,
                out_channel=inp.out_channel,
                policy=policy.to_json(),
                principal=inp.principal,
                root_run_id=(inp.root_run_id or inp.session_id),
                segment_seq=inp.segment_seq + 1,
                history_threshold=inp.history_threshold,
                channel_capacity=inp.channel_capacity,
                state_cursor=state_cursor,
                has_carrier=True,
                carrier=carrier,
                inbox={
                    channel: [dict(item) for item in items]
                    for channel, items in self._pending.items()
                },
                out_buffers={
                    channel: [dict(item) for item in items]
                    for channel, items in self._out_buffers.items()
                },
                ack_cursors=dict(self._ack_cursors),
                seq_cursors=dict(self._seq_cursors),
                closed=self._closed,
                close_reason=self._close_reason,
                idempotency_index={
                    channel: dict(entries)
                    for channel, entries in self._idempotency_index.items()
                },
                idempotency_fp={
                    channel: dict(entries)
                    for channel, entries in self._idempotency_fp.items()
                },
                event_log=[dict(item) for item in self._event_log],
                event_seq=self._event_seq,
                event_ack=self._event_ack,
                queue_lanes=inp.queue_lanes,
            )
        )

    async def _post_turn_budget_and_can(
        self,
        inp: SessionInput,
        store: InMemoryProjection,
        env: _TemporalEnv,
        budget: Optional[Budget],
        *,
        carrier: Any,
        state_cursor: Optional[int],
        flow_json: dict[str, Any],
        manifest_json: Optional[dict[str, Any]],
        policy: ExecutionPolicy,
    ) -> tuple[bool, Optional[int]]:
        segment_spent = sum(store.cost_by_shape().values())
        total_spent = inp.spent + segment_spent
        if al.would_exceed_budget(
            al.AgentState(spent=inp.spent),
            segment_spent,
            budget,
        ):
            self._close_reason = "over_budget"
            self._closed = True
            return True, state_cursor

        want_can = self._should_continue_as_new(inp)
        if want_can:
            cursor = await self._commit_carrier(
                inp,
                base_cursor=state_cursor,
                carrier=carrier,
            )
            state_cursor = cursor
        if want_can and state_cursor is not None:
            self._continue_as_new(
                inp,
                carrier=carrier,
                state_cursor=state_cursor,
                flow_json=flow_json,
                manifest_json=manifest_json,
                policy=policy,
                call_counts=env.call_counts_snapshot(),
                spent=total_spent,
            )
        return False, state_cursor

    @workflow.run
    async def run(self, inp: SessionInput) -> Any:
        if workflow.info().workflow_id != inp.session_id:
            raise ApplicationError(
                f"session store fencing violated: session_id {inp.session_id!r} != workflow id "
                f"{workflow.info().workflow_id!r}; durable sessions delegate mutual exclusion to "
                "Temporal's one-running-execution-per-workflow-id guarantee, so they must be 1:1",
                type="ValidationError",
                non_retryable=True,
            )

        policy = ExecutionPolicy.from_json(inp.policy)
        flow_json = inp.flow_json
        manifest_json = inp.manifest_json
        pinned_pures = inp.pinned_pures
        bundle = inp.bundle
        budget = Budget.from_dict(inp.budget)
        flow = Node.from_json(flow_json)
        manifest = manifest_from_json(manifest_json or {})

        if flow.op != Op.LOOP:
            raise ApplicationError(
                "SessionWorkflow requires a root Op.LOOP",
                type="ValidationError",
                non_retryable=True,
            )
        diagnostics = [
            d
            for d in blocking(validate(flow, manifest, target="session"))
            if d.code != "UNKNOWN_PURE"
        ]
        if diagnostics:
            details = "; ".join(f"{d.code}: {d.message}" for d in diagnostics)
            raise ApplicationError(
                f"invalid session LOOP: {details}",
                type="ValidationError",
                non_retryable=True,
            )
        assert flow.body is not None

        await _verify_pures_for_flow(
            flow_json=flow_json,
            pinned_pures=pinned_pures,
            bundle=bundle,
        )

        self._rehydrate(inp)
        carrier = await self._load_carrier(inp)
        state_cursor = inp.state_cursor
        self._carrier_current = carrier

        store, emitter = _make_emitter()
        self._proj = store
        env = _TemporalEnv(
            manifest=manifest,
            emitter=emitter,
            session_id=inp.session_id,
            manifest_json=manifest_json,
            policy=policy,
            gate_waiter=lambda value, cid, timeout_s: self._recv_waiter(
                "human", cid, timeout_s
            ),
            recv_waiter=self._recv_waiter,
            emit_sink=self._emit_sink,
            workflow_id=inp.session_id,
            max_call_limits=inp.max_call_limits,
            call_counts=inp.call_counts,
            principal=inp.principal,
            root_run_id=(inp.root_run_id or inp.session_id),
            segment_seq=inp.segment_seq,
            queue_lanes=inp.queue_lanes,
            runtime_declarations_ref=inp.runtime_declarations_ref,
        )

        split_result = bool(flow.args and flow.args.get("split") is True)
        try:
            while True:
                try:
                    result: Result = await interpret(flow.body, carrier, env)
                except RecvTimeout as exc:
                    channel = exc.channel
                    self._open_receives[channel] = (
                        self._seq_cursors.get(self._consumed_seq_key(channel), 0)
                        + 1
                    )
                    try:
                        await workflow.wait_condition(
                            lambda channel=channel: bool(self._pending.get(channel)) or self._closed
                        )
                    finally:
                        self._open_receives.pop(channel, None)
                    continue
                except SessionClosed:
                    break
                except SessionTurnError as exc:
                    if exc.fatal:
                        raise
                    self._append_event("error", reason=str(exc), fatal=False)
                    self._append_turn_done_if_started()
                    should_break, state_cursor = await self._post_turn_budget_and_can(
                        inp,
                        store,
                        env,
                        budget,
                        carrier=carrier,
                        state_cursor=state_cursor,
                        flow_json=flow_json,
                        manifest_json=manifest_json,
                        policy=policy,
                    )
                    if should_break:
                        break
                    continue

                if (
                    split_result
                    and isinstance(result.value, tuple)
                    and len(result.value) == 2
                ):
                    carrier, output = result.value
                    await self._emit_sink(inp.out_channel, output, f"{flow.id}:out")
                else:
                    carrier = result.value
                self._carrier_current = carrier
                self._append_turn_done_if_started()

                should_break, state_cursor = await self._post_turn_budget_and_can(
                    inp,
                    store,
                    env,
                    budget,
                    carrier=carrier,
                    state_cursor=state_cursor,
                    flow_json=flow_json,
                    manifest_json=manifest_json,
                    policy=policy,
                )
                if should_break:
                    break
        except JulepError as exc:
            self._append_event("error", reason=str(exc), fatal=True)
            self._closed = True
            self._close_reason = str(exc)
            self._append_closed_once()
            raise ApplicationError(
                str(exc),
                type=type(exc).__name__,
                non_retryable=True,
            ) from exc
        self._closed = True
        self._append_closed_once()
        return carrier


# --------------------------------------------------------------------------- #
# AgentWorkflow — the App loop (bounded actions, budget guard, continue-as-new).
# --------------------------------------------------------------------------- #
@workflow.defn(name="AgentWorkflow")
class AgentWorkflow:
    def __init__(self) -> None:
        self._human_inbox: dict[str, Any] = {}

    @workflow.signal(name="submitHuman")
    def submit_human(self, payload: dict[str, Any]) -> None:
        self._human_inbox[payload["cid"]] = payload.get("value")

    async def _start_trajectory(self, inp: AgentInput) -> None:
        from .. import trajectory as _traj

        root_run_id = inp.root_run_id or inp.session_id
        if inp.segment_seq != 0 or root_run_id != inp.session_id:
            return
        try:
            await workflow.execute_activity(
                startTrajectory,
                {
                    "runId": inp.session_id,
                    "rootRunId": root_run_id,
                    "segmentSeq": inp.segment_seq,
                    "input": inp.input,
                    "cid": f"{root_run_id}:root",
                },
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    maximum_attempts=1,
                    non_retryable_error_types=_NON_RETRYABLE,
                ),
            )
        except Exception as exc:
            def _reraise(e: BaseException = exc) -> None:
                raise e

            _traj._best_effort(_reraise)

    async def _finish_trajectory(
        self,
        run_id: str,
        result: Any = None,
        *,
        root_run_id: Optional[str] = None,
        status: str = "completed",
        segment_seq: int = 0,
    ) -> None:
        try:
            await workflow.execute_activity(
                finishTrajectory,
                {
                    "runId": run_id,
                    "rootRunId": root_run_id,
                    "status": status,
                    "result": result,
                    "segmentSeq": segment_seq,
                },
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    maximum_attempts=1,
                    non_retryable_error_types=_NON_RETRYABLE,
                ),
            )
        except Exception as exc:
            _LOG.warning("trajectory dispatch failed (best-effort, swallowed): %s", exc)

    @workflow.run
    async def run(self, inp: AgentInput) -> dict[str, Any]:
        # Design invariant 1 (durable-session-store): session_id <-> workflow id
        # must be 1:1 — Temporal's one-running-execution-per-workflow-id is the
        # store's only mutual-exclusion mechanism. Enforce before any effect.
        if inp.use_session_store and workflow.info().workflow_id != inp.session_id:
            raise ApplicationError(
                f"session store fencing violated: session_id {inp.session_id!r} != workflow id "
                f"{workflow.info().workflow_id!r}; the session store delegates mutual exclusion to "
                "Temporal's one-running-execution-per-workflow-id guarantee, so they must be 1:1",
                type="ValidationError",
                non_retryable=True,
            )

        policy = ExecutionPolicy.from_json(inp.policy)

        # Resolve config + grant metadata once, then carry it through
        # continue-as-new. Inline app config can supply grant semantics while
        # still using the resolved agent spec for default loop settings.
        config = dict(inp.config or {})
        granted = inp.granted_tools
        granted_subflows = inp.granted_subflows
        subflow_queues = inp.subflow_queues
        contracts = dict(inp.granted_contracts or {})
        tool_defs = inp.tool_defs
        grants_supplied = inp.granted_tools is not None or inp.granted_tools_unconstrained
        subflows_supplied = inp.granted_subflows is not None

        if inp.resolve_spec:
            spec = await workflow.execute_activity(
                resolveAgentSpec,
                inp.controller,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3, non_retryable_error_types=_NON_RETRYABLE),
            )
            spec_tool_defs = spec.get("toolDefs")
            tool_defs = spec_tool_defs if spec_tool_defs is not None else tool_defs
            merged_config = dict(spec.get("config") or {})
            merged_config.update(config)
            config = merged_config
            spec_granted = spec.get("grantedTools")
            if grants_supplied:
                capability_tools = spec.get("capabilityTools")
                if not inp.granted_tools_unconstrained and granted is not None and capability_tools is not None:
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
            spec_subflow_queues = spec.get("subflowQueues")
            if spec_subflow_queues is not None:
                subflow_queues = dict(spec_subflow_queues)

        cfg = al.AgentConfig.from_json(config or {})
        if cfg.native_tools and not tool_defs:
            raise ApplicationError(
                "native_tools on a durable backend needs provider tool definitions; "
                'supply AgentInput.tool_defs, a spec-level "toolDefs" list, or '
                "registered tool schema expectations for all granted tools.",
                type="ValidationError",
                non_retryable=True,
            )
        unconstrained = inp.granted_tools_unconstrained or granted is None
        granted_set = set(granted or [])

        if inp.use_session_store and inp.state_cursor is not None:
            state_json = await workflow.execute_activity(
                loadState,
                LoadStateInput(session_id=inp.session_id, cursor=inp.state_cursor),
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    maximum_attempts=3, non_retryable_error_types=_NON_RETRYABLE
                ),
            )
            state = al.AgentState.from_json(state_json)
        elif inp.state:
            state = al.AgentState.from_json(inp.state)
        else:
            state = al.AgentState(last=inp.input)

        # Per-segment continue-as-new cadence: carried state keeps the
        # cumulative round count, so truncation is measured from this
        # segment's entry round, not from zero.
        baseline_round = state.round

        await self._start_trajectory(inp)

        note_fn: Optional[Callable[..., Any]] = None
        if cfg.round_note is not None:
            note_fn = _get_pure_from_registry(cfg.round_note)

        while True:
            if state.round >= cfg.max_rounds:
                terminal = al.terminal_result("max_rounds", state)
                await self._finish_trajectory(
                    inp.session_id,
                    terminal,
                    root_run_id=(inp.root_run_id or inp.session_id),
                    segment_seq=inp.segment_seq,
                )
                return terminal

            # 1) Check the controller's own cost before spending on it, then ask
            # the controller what to do and charge the per-round think cost.
            controller_precheck = al.precheck_controller(state, cfg)
            if controller_precheck is not None:
                await self._finish_trajectory(
                    inp.session_id,
                    controller_precheck,
                    root_run_id=(inp.root_run_id or inp.session_id),
                    segment_seq=inp.segment_seq,
                )
                return controller_precheck

            # Transcript plan (agent-transcripts): deterministic, ref-bearing,
            # computed here in workflow code; hydration, the token budget, and
            # summarization are activity work inside invokeReasoner.
            transcript_plan = None
            if cfg.ctx is not None and cfg.ctx.scope in TRANSCRIPT_SCOPES:
                transcript_plan = transcript_for(state, cfg.ctx, input=inp.input)

            controller_value: dict[str, Any] = {
                "input": state.last,
                "trace": [t.to_json() for t in state.trace],
            }
            if note_fn is not None:
                # Fresh each round from loop state only; deterministic under
                # Temporal replay because the function is a registered pure.
                note = al.coerce_round_note(note_fn({
                    "round": state.round,
                    "maxRounds": cfg.max_rounds,
                    "spent": state.spent,
                    "callCounts": dict(state.call_counts),
                }))
                if note is not None:
                    controller_value[al.ROUND_NOTE_KEY] = note

            reply = await workflow.execute_activity(
                invokeReasoner,
                InvokeReasonerInput(
                    reasoner=inp.controller,
                    value=controller_value,
                    cid=f"{inp.session_id}-round-{state.round}",
                    principal=inp.principal,
                    transcript=transcript_plan,
                    ctx=(
                        cfg.ctx.to_json()
                        if transcript_plan is not None and cfg.ctx is not None
                        else None
                    ),
                    summarizer=cfg.summarizer if transcript_plan is not None else None,
                    summary=state.summary if transcript_plan is not None else None,
                    tools=tool_defs if cfg.native_tools else None,
                    run_id=inp.session_id,
                    root_run_id=(inp.root_run_id or inp.session_id),
                    segment_seq=inp.segment_seq,
                    op="think",
                    kind="reasoner",
                    runtime_declarations_ref=inp.runtime_declarations_ref,
                ),
                start_to_close_timeout=timedelta(seconds=policy.reasoner_timeout_s),
                retry_policy=_reasoner_retry(policy),
            )
            if isinstance(reply, dict) and "__julep_meta__" in reply and "reply" in reply:
                meta = reply["__julep_meta__"]
                state.controller_meta = (
                    dict(meta) if isinstance(meta, dict) else {"meta": meta}
                )
            else:
                state.controller_meta = None
            new_summary, reply = split_summary_reply(reply)
            reply = unwrap_reply_meta(reply)
            if new_summary is not None:
                state.summary = new_summary
            state.charge(cfg.think_cost)
            action = al.interpret_reasoner_reply(
                reply,
                strict=not cfg.permissive_controller,
                native_tools=cfg.native_tools,
            )

            # 2) Terminal decisions end the loop.
            if action.decision is al.Decision.FINISH:
                if cfg.require_tool_call and not any(
                    entry.decision == "call" and entry.error is None
                    for entry in state.trace
                ):
                    reasks = sum(1 for entry in state.trace if entry.decision == "reask")
                    if reasks >= 2:
                        terminal = al.terminal_result(
                            "controller_error",
                            state,
                            reason=al.REQUIRE_TOOL_CALL_NEVER_CALLED_REASON,
                        )
                        await self._finish_trajectory(
                            inp.session_id,
                            terminal,
                            root_run_id=(inp.root_run_id or inp.session_id),
                            segment_seq=inp.segment_seq,
                        )
                        return terminal
                    state.last = {
                        "error": al.REQUIRE_TOOL_CALL_REASK_MESSAGE,
                        "reply": action.payload,
                    }
                    state.record(al.TraceEntry(
                        decision="reask",
                        error=al.REQUIRE_TOOL_CALL_REASK_MESSAGE,
                    ))
                    state.round += 1
                    continue
                terminal = al.terminal_result("done", state, output=action.payload)
                await self._finish_trajectory(
                    inp.session_id,
                    terminal,
                    root_run_id=(inp.root_run_id or inp.session_id),
                    segment_seq=inp.segment_seq,
                )
                return terminal
            if action.decision is al.Decision.ESCALATE:
                terminal = al.terminal_result("escalated", state, reason=str(action.payload))
                await self._finish_trajectory(
                    inp.session_id,
                    terminal,
                    root_run_id=(inp.root_run_id or inp.session_id),
                    segment_seq=inp.segment_seq,
                )
                return terminal
            if action.decision is al.Decision.CONTROLLER_ERROR:
                terminal = al.terminal_result(
                    "controller_error", state, reason=str(action.payload)
                )
                await self._finish_trajectory(
                    inp.session_id,
                    terminal,
                    root_run_id=(inp.root_run_id or inp.session_id),
                    segment_seq=inp.segment_seq,
                )
                return terminal

            # 3) Budget guard before doing any work this round.
            cost = al.action_cost(action)
            if al.would_exceed_budget(state, cost, cfg.budget):
                terminal = al.terminal_result("over_budget", state)
                await self._finish_trajectory(
                    inp.session_id,
                    terminal,
                    root_run_id=(inp.root_run_id or inp.session_id),
                    segment_seq=inp.segment_seq,
                )
                return terminal

            # 4) Bounded action: one granted tool call, or one sub-flow. When the
            # controller omits an explicit input, the action operates on the
            # current value (state.last) rather than passing None downstream.
            if action.decision is al.Decision.CALL_MANY:
                calls = list(action.payload)
                for entry in calls:
                    tool = entry["tool"]
                    denial = al.authorize_call(
                        tool,
                        unconstrained=unconstrained,
                        granted_set=granted_set,
                        contracts=contracts,
                    )
                    if denial is not None:
                        terminal = al.terminal_result("denied", state, reason=denial.reason)
                        await self._finish_trajectory(
                            inp.session_id,
                            terminal,
                            root_run_id=(inp.root_run_id or inp.session_id),
                            segment_seq=inp.segment_seq,
                        )
                        return terminal
                for entry in calls:
                    tool = entry["tool"]
                    denial = al.charge_tool_call(state, tool, contracts)
                    if denial is not None:
                        terminal = al.terminal_result("denied", state, reason=denial.reason)
                        await self._finish_trajectory(
                            inp.session_id,
                            terminal,
                            root_run_id=(inp.root_run_id or inp.session_id),
                            segment_seq=inp.segment_seq,
                        )
                        return terminal

                async def execute_entry(
                    index: int,
                    entry: dict[str, Any],
                ) -> tuple[int, dict[str, Any], al.TraceEntry]:
                    tool = entry["tool"]
                    call_input = entry.get("input")
                    if call_input is None:
                        call_input = state.last
                    contract = al.contract_for_tool(tool, contracts)
                    error: Optional[str] = None
                    try:
                        out = await workflow.execute_activity(
                            callTool,
                            CallToolInput(
                                tool_ref=_toolref_json_from_key(tool),
                                value=call_input,
                                cid=f"{inp.session_id}-call-{state.round}-{index}",
                                principal=inp.principal,
                                run_id=inp.session_id,
                                root_run_id=(inp.root_run_id or inp.session_id),
                                segment_seq=inp.segment_seq,
                                op="call",
                                kind="tool",
                            ),
                            start_to_close_timeout=timedelta(seconds=policy.tool_timeout_s),
                            retry_policy=_retry_policy_for(contract, policy),
                        )
                    except ActivityError as exc:
                        error = repr(exc)
                        out = {"error": error, "tool": tool}
                    output_ref: Optional[str] = None
                    if policy.trace_content_refs:
                        output_ref = await workflow.execute_activity(
                            putBlob,
                            PutBlobInput(tenant=inp.session_id, value=out),
                            start_to_close_timeout=timedelta(seconds=30),
                            retry_policy=RetryPolicy(
                                maximum_attempts=3,
                                non_retryable_error_types=_NON_RETRYABLE,
                            ),
                        )
                    return (
                        index,
                        {
                            "id": entry.get("id"),
                            "tool": tool,
                            "output": out,
                        },
                        al.TraceEntry(
                            decision="call",
                            ref=tool,
                            cost=al.DEFAULT_TOOL_COST,
                            call_id=entry.get("id"),
                            output_ref=output_ref,
                            error=error,
                        ),
                    )

                results: list[Optional[tuple[int, dict[str, Any], al.TraceEntry]]] = [
                    None
                ] * len(calls)
                read_items = [
                    (index, entry)
                    for index, entry in enumerate(calls)
                    if al.contract_for_tool(entry["tool"], contracts).effect is Effect.READ
                ]
                if read_items:
                    read_results = await asyncio.gather(
                        *(execute_entry(index, entry) for index, entry in read_items)
                    )
                    for result in read_results:
                        results[result[0]] = result
                for index, entry in enumerate(calls):
                    if results[index] is None:
                        results[index] = await execute_entry(index, entry)

                observations: list[dict[str, Any]] = []
                traces: list[al.TraceEntry] = []
                for maybe_result in results:
                    assert maybe_result is not None
                    _, observation, trace = maybe_result
                    observations.append(observation)
                    traces.append(trace)
                state.charge(cost)
                state.last = observations
                for trace in traces:
                    state.record(trace)

            elif action.decision is al.Decision.CALL:
                tool = action.payload["tool"]
                denial = al.authorize_call(
                    tool,
                    unconstrained=unconstrained,
                    granted_set=granted_set,
                    contracts=contracts,
                )
                if denial is not None:
                    terminal = al.terminal_result("denied", state, reason=denial.reason)
                    await self._finish_trajectory(
                        inp.session_id,
                        terminal,
                        root_run_id=(inp.root_run_id or inp.session_id),
                        segment_seq=inp.segment_seq,
                    )
                    return terminal
                denial = al.charge_tool_call(state, tool, contracts)
                if denial is not None:
                    terminal = al.terminal_result("denied", state, reason=denial.reason)
                    await self._finish_trajectory(
                        inp.session_id,
                        terminal,
                        root_run_id=(inp.root_run_id or inp.session_id),
                        segment_seq=inp.segment_seq,
                    )
                    return terminal
                call_input = action.payload.get("input")
                if call_input is None:
                    call_input = state.last
                contract = al.contract_for_tool(tool, contracts)
                error: Optional[str] = None
                try:
                    out = await workflow.execute_activity(
                        callTool,
                        CallToolInput(
                            tool_ref=_toolref_json_from_key(tool),
                            value=call_input,
                            cid=f"{inp.session_id}-call-{state.round}",
                            principal=inp.principal,
                            run_id=inp.session_id,
                            root_run_id=(inp.root_run_id or inp.session_id),
                            segment_seq=inp.segment_seq,
                            op="call",
                            kind="tool",
                        ),
                        start_to_close_timeout=timedelta(seconds=policy.tool_timeout_s),
                        retry_policy=_retry_policy_for(contract, policy),
                    )
                except ActivityError as exc:
                    error = repr(exc)
                    out = {"error": error, "tool": tool}
                state.charge(cost)
                state.last = out
                output_ref: Optional[str] = None
                if policy.trace_content_refs:
                    output_ref = await workflow.execute_activity(
                        putBlob,
                        PutBlobInput(tenant=inp.session_id, value=out),
                        start_to_close_timeout=timedelta(seconds=30),
                        retry_policy=RetryPolicy(
                            maximum_attempts=3, non_retryable_error_types=_NON_RETRYABLE
                        ),
                    )
                state.record(
                    al.TraceEntry(
                        decision="call",
                        ref=tool,
                        cost=cost,
                        output_ref=output_ref,
                        error=error,
                    )
                )

            else:  # Decision.SUB
                ref = action.payload["ref"]
                denial = al.authorize_subflow(
                    ref,
                    granted_subflows=(
                        None if granted_subflows is None else set(granted_subflows)
                    ),
                )
                if denial is not None:
                    terminal = al.terminal_result("denied", state, reason=denial.reason)
                    await self._finish_trajectory(
                        inp.session_id,
                        terminal,
                        root_run_id=(inp.root_run_id or inp.session_id),
                        segment_seq=inp.segment_seq,
                    )
                    return terminal
                sub_input = action.payload.get("input")
                if sub_input is None:
                    sub_input = state.last
                child_id = f"{inp.session_id}-sub-{state.round}"
                child_bundle: Optional[list[dict[str, str]]] = None
                if _bundle_ref_child_input_enabled():
                    resolved = await workflow.execute_activity(
                        resolveSubflow,
                        ref,
                        start_to_close_timeout=timedelta(seconds=30),
                        retry_policy=RetryPolicy(
                            maximum_attempts=3,
                            non_retryable_error_types=_NON_RETRYABLE,
                        ),
                    )
                    bundle = resolved.get("bundle")
                    if isinstance(bundle, list):
                        child_bundle = bundle
                resolved_queue = _resolve_child_queue(
                    (subflow_queues or {}).get(ref),
                    inp.queue_lanes,
                )
                start_kwargs: dict[str, Any] = {
                    "id": child_id,
                    "task_timeout": timedelta(seconds=policy.sub_task_timeout_s),
                }
                if resolved_queue is not None:
                    start_kwargs["task_queue"] = resolved_queue
                out = await workflow.execute_child_workflow(
                    FlowWorkflow.run,
                    FlowInput(
                        session_id=child_id,
                        input=sub_input,
                        ref=ref,
                        policy=policy.to_json(),
                        max_call_limits=al.max_call_limits_from_contracts(contracts),
                        call_counts=dict(state.call_counts),
                        principal=inp.principal,
                        root_run_id=(inp.root_run_id or inp.session_id),
                        bundle=child_bundle,
                        queue_lanes=(inp.queue_lanes or None),
                    ),
                    **start_kwargs,
                )
                # Trajectory: capture the agent's sub action as a sub/flow step
                # (parity with FlowWorkflow's SubStep and the DBOS backend).
                # Best-effort: never raises into the agent loop.
                from .. import trajectory as _traj

                try:
                    await workflow.execute_activity(
                        runSubCapture,
                        args=[
                            {
                                "ref": ref,
                                "value": sub_input,
                                "cid": child_id,
                                "principal": inp.principal,
                                "run_id": inp.session_id,
                                "root_run_id": (inp.root_run_id or inp.session_id),
                                "segment_seq": inp.segment_seq,
                                "node_id": None,
                                "op": "sub",
                                "kind": "flow",
                                "causes": (),
                            },
                            out,
                        ],
                        start_to_close_timeout=timedelta(seconds=30),
                        retry_policy=RetryPolicy(
                            maximum_attempts=1,
                            non_retryable_error_types=_NON_RETRYABLE,
                        ),
                    )
                except Exception as exc:
                    def _reraise(e: BaseException = exc) -> None:
                        raise e

                    _traj._best_effort(_reraise)
                state.charge(cost)
                state.last = out
                output_ref: Optional[str] = None
                if policy.trace_content_refs:
                    output_ref = await workflow.execute_activity(
                        putBlob,
                        PutBlobInput(tenant=inp.session_id, value=out),
                        start_to_close_timeout=timedelta(seconds=30),
                        retry_policy=RetryPolicy(
                            maximum_attempts=3, non_retryable_error_types=_NON_RETRYABLE
                        ),
                    )
                state.record(
                    al.TraceEntry(
                        decision="sub",
                        ref=ref,
                        shape=action.payload.get("shape"),
                        cost=cost,
                        output_ref=output_ref,
                    )
                )

            state.round += 1

            # 5) §6 seam: truncate history by continuing as new with carried state.
            if al.should_continue_as_new(state, cfg, baseline_round=baseline_round):
                if inp.use_session_store:
                    state_hash = al.state_fingerprint(state)
                    cursor = await workflow.execute_activity(
                        commitState,
                        CommitStateInput(
                            session_id=inp.session_id,
                            base=inp.state_cursor or 0,
                            state=state.to_json(),
                            state_hash=state_hash,
                        ),
                        start_to_close_timeout=timedelta(seconds=30),
                        retry_policy=RetryPolicy(
                            maximum_attempts=3, non_retryable_error_types=_NON_RETRYABLE
                        ),
                    )
                    workflow.continue_as_new(
                        AgentInput(
                            controller=inp.controller,
                            session_id=inp.session_id,
                            input=inp.input,
                            config=config,
                            granted_tools=None if unconstrained else sorted(granted_set),
                            granted_tools_unconstrained=unconstrained,
                            granted_subflows=granted_subflows,
                            granted_contracts=contracts,
                            tool_defs=tool_defs,
                            state=None,
                            state_cursor=cursor,
                            use_session_store=True,
                            policy=policy.to_json(),
                            resolve_spec=False,
                            principal=inp.principal,
                            root_run_id=(inp.root_run_id or inp.session_id),
                            segment_seq=inp.segment_seq + 1,
                            queue_lanes=inp.queue_lanes,
                            subflow_queues=subflow_queues,
                            runtime_declarations_ref=inp.runtime_declarations_ref,
                        )
                    )
                else:
                    workflow.continue_as_new(
                        AgentInput(
                            controller=inp.controller,
                            session_id=inp.session_id,
                            input=inp.input,
                            config=config,
                            granted_tools=None if unconstrained else sorted(granted_set),
                            granted_tools_unconstrained=unconstrained,
                            granted_subflows=granted_subflows,
                            granted_contracts=contracts,
                            tool_defs=tool_defs,
                            state=state.to_json(),
                            policy=policy.to_json(),
                            resolve_spec=False,
                            principal=inp.principal,
                            root_run_id=(inp.root_run_id or inp.session_id),
                            segment_seq=inp.segment_seq + 1,
                            queue_lanes=inp.queue_lanes,
                            subflow_queues=subflow_queues,
                            runtime_declarations_ref=inp.runtime_declarations_ref,
                        )
                    )


# --------------------------------------------------------------------------- #
# Client helper.
# --------------------------------------------------------------------------- #
def build_flow_input(
    *,
    session_id: str,
    input: Any = None,
    flow_json: Optional[dict[str, Any]] = None,
    manifest_json: Optional[dict[str, Any]] = None,
    policy: Optional[ExecutionPolicy | Mapping[str, Any]] = None,
    pinned_pures: Optional[dict[str, str]] = None,
    max_call_limits: Optional[dict[str, int]] = None,
    principal: Optional[dict[str, Any]] = None,
    root_run_id: Optional[str] = None,
    bundle: Optional[list[dict[str, str]]] = None,
    runtime_declarations_ref: Optional[dict[str, Any]] = None,
    queue_lanes: Optional[dict[str, str]] = None,
    run_id: Optional[str] = None,
    emit_projection: bool = False,
    projection_batch_size: int = 20,
    projection_batch_interval_s: float = 2.0,
) -> FlowInput:
    """Single source of truth for deployed-run FlowInput construction.

    Used by run_flow and by Julep CLI ``build_flow_start_args`` consumers
    (julep run / julep schedule) so scheduled and manual runs carry byte-identical args.
    """
    policy_json = (
        policy.to_json()
        if isinstance(policy, ExecutionPolicy)
        else dict(policy) if policy is not None else ExecutionPolicy().to_json()
    )
    return FlowInput(
        session_id=session_id,
        input=input,
        flow_json=flow_json,
        manifest_json=manifest_json,
        pinned_pures=pinned_pures,
        max_call_limits=max_call_limits,
        policy=policy_json,
        principal=principal,
        root_run_id=root_run_id,
        bundle=bundle,
        runtime_declarations_ref=runtime_declarations_ref,
        queue_lanes=queue_lanes,
        run_id=run_id,
        emit_projection=emit_projection,
        projection_batch_size=projection_batch_size,
        projection_batch_interval_s=projection_batch_interval_s,
    )


async def run_flow(
    client,
    flow_json: dict[str, Any],
    manifest_json: dict[str, Any],
    *,
    session_id: str,
    input: Any = None,
    task_queue: str = "julep",
    policy: Optional[ExecutionPolicy] = None,
    pinned_pures: Optional[dict[str, str]] = None,
    max_call_limits: Optional[dict[str, int]] = None,
    principal: Optional[dict[str, Any]] = None,
    root_run_id: Optional[str] = None,
    bundle: Optional[list[dict[str, str]]] = None,
    runtime_declarations_ref: Optional[dict[str, Any]] = None,
    queue_lanes: Optional[dict[str, str]] = None,
    run_id: Optional[str] = None,
    emit_projection: bool = False,
    projection_batch_size: int = 20,
    projection_batch_interval_s: float = 2.0,
) -> Any:
    """Start :class:`FlowWorkflow` for a frozen flow and await its result.

    ``client`` is a connected ``temporalio.client.Client``. ``flow_json`` /
    ``manifest_json`` come from :func:`julep.freeze.freeze` (then
    serialized). The workflow id is the session id, so a re-submission with the
    same id is deduplicated by Temporal. ``principal`` is the run's opaque
    tenant/credential reference (never a secret) — see
    :data:`~julep.execution.effects.RunPrincipal`.
    """
    return await client.execute_workflow(
        FlowWorkflow.run,
        build_flow_input(
            session_id=session_id,
            input=input,
            flow_json=flow_json,
            manifest_json=manifest_json,
            pinned_pures=pinned_pures,
            max_call_limits=max_call_limits,
            policy=policy,
            principal=principal,
            root_run_id=root_run_id,
            bundle=bundle,
            runtime_declarations_ref=runtime_declarations_ref,
            queue_lanes=queue_lanes,
            run_id=run_id,
            emit_projection=emit_projection,
            projection_batch_size=projection_batch_size,
            projection_batch_interval_s=projection_batch_interval_s,
        ),
        id=session_id,
        task_queue=task_queue,
    )


async def start_flow(
    client,
    flow_json: dict[str, Any],
    manifest_json: dict[str, Any],
    *,
    session_id: str,
    input: Any = None,
    task_queue: str = "julep",
    policy: Optional[ExecutionPolicy] = None,
    pinned_pures: Optional[dict[str, str]] = None,
    max_call_limits: Optional[dict[str, int]] = None,
    principal: Optional[dict[str, Any]] = None,
    root_run_id: Optional[str] = None,
    bundle: Optional[list[dict[str, str]]] = None,
    runtime_declarations_ref: Optional[dict[str, Any]] = None,
    queue_lanes: Optional[dict[str, str]] = None,
    workflow_start_options: Optional[Mapping[str, Any]] = None,
    run_id: Optional[str] = None,
    emit_projection: bool = False,
    projection_batch_size: int = 20,
    projection_batch_interval_s: float = 2.0,
):
    """Like :func:`run_flow` but returns the :class:`WorkflowHandle` immediately.

    Use the handle to signal a human gate (``handle.signal("submitHuman", {...})``)
    or query the projection (``handle.query("projection")``) while the run is live.
    """
    start_options = dict(workflow_start_options or {})
    if "id" in start_options or "task_queue" in start_options:
        raise ValueError("workflow_start_options cannot override id or task_queue")
    return await client.start_workflow(
        FlowWorkflow.run,
        build_flow_input(
            session_id=session_id,
            input=input,
            flow_json=flow_json,
            manifest_json=manifest_json,
            pinned_pures=pinned_pures,
            max_call_limits=max_call_limits,
            policy=policy,
            principal=principal,
            root_run_id=root_run_id,
            bundle=bundle,
            runtime_declarations_ref=runtime_declarations_ref,
            queue_lanes=queue_lanes,
            run_id=run_id,
            emit_projection=emit_projection,
            projection_batch_size=projection_batch_size,
            projection_batch_interval_s=projection_batch_interval_s,
        ),
        id=session_id,
        task_queue=task_queue,
        **start_options,
    )


async def _start_session(
    client,
    flow_json: dict[str, Any],
    manifest_json: dict[str, Any],
    *,
    session_id: str,
    init: Any,
    in_channel: str = "in",
    out_channel: str = "out",
    task_queue: str = "julep",
    policy: Optional[ExecutionPolicy] = None,
    principal: Optional[dict[str, Any]] = None,
    history_threshold: Optional[int] = None,
    channel_capacity: Optional[int] = None,
    max_call_limits: Optional[dict[str, int]] = None,
    pinned_pures: Optional[dict[str, str]] = None,
    budget: Optional[dict[str, Any]] = None,
    bundle: Optional[list[dict[str, str]]] = None,
    runtime_declarations_ref: Optional[dict[str, Any]] = None,
):
    """Internal session starter for deployments validated by ``Agent._deploy_session``.

    The caller must provide a frozen Deployment that has already run
    validate(target="session"), capability compile enforcement, max-call limit
    extraction, and pinned-pure/bundle wiring.
    """
    handle = await client.start_workflow(
        SessionWorkflow.run,
        SessionInput(
            session_id=session_id,
            flow_json=flow_json,
            manifest_json=manifest_json,
            init=init,
            max_call_limits=max_call_limits,
            pinned_pures=pinned_pures,
            budget=budget,
            bundle=bundle,
            runtime_declarations_ref=runtime_declarations_ref,
            in_channel=in_channel,
            out_channel=out_channel,
            policy=(policy or ExecutionPolicy()).to_json(),
            principal=principal,
            history_threshold=history_threshold,
            channel_capacity=channel_capacity,
        ),
        id=session_id,
        task_queue=task_queue,
    )
    await handle.query("state")
    return handle


class TemporalSessionHandle:
    """Client-side facade over a live ``SessionWorkflow``."""

    def __init__(
        self,
        wfhandle: Any,
        *,
        in_channel: str = "in",
        out_channel: str = "out",
        poll_s: float = 0.02,
    ) -> None:
        self._wfhandle = wfhandle
        self._in_channel = in_channel
        self._out_channel = out_channel
        self._poll_s = poll_s
        self._close_requested = False
        self._close_reason: Optional[str] = None
        self._events_subscribed = False

    async def send(
        self,
        value: Any,
        *,
        channel: Optional[str] = None,
        idempotency_key: Any = None,
    ) -> dict[str, Any]:
        ch = channel or self._in_channel
        payload = {"channel": ch, "value": value}
        if idempotency_key is not None:
            payload["idempotency_key"] = idempotency_key
        return await self._wfhandle.execute_update("send", payload)

    async def state(self) -> dict[str, Any]:
        return await self._wfhandle.query("state")

    async def open_receives(self) -> list[dict[str, Any]]:
        return await self._wfhandle.query("open_receives")

    async def close(self, reason: Optional[str] = None) -> None:
        self._close_requested = True
        self._close_reason = reason
        await self._wfhandle.execute_update("close", {"reason": reason})
        deadline = asyncio.get_running_loop().time() + 30.0
        while True:
            try:
                snap = await self.state()
                records = await self._wfhandle.query("events")
                if (
                    snap.get("closed") is True
                    and (not records or records[-1].get("kind") == "closed")
                ):
                    return
            except WorkflowFailureError:
                return
            except Exception:
                try:
                    await asyncio.wait_for(
                        self._wfhandle.result(),
                        timeout=self._poll_s,
                    )
                    return
                except asyncio.TimeoutError:
                    pass
                except WorkflowFailureError:
                    return
            if asyncio.get_running_loop().time() >= deadline:
                raise TimeoutError("session close did not quiesce")
            await asyncio.sleep(self._poll_s)

    @staticmethod
    def _event_from_record(record: dict[str, Any]) -> SessionEvent:
        kind = str(record.get("kind"))
        if kind == "turn":
            turn = str(record.get("turn"))
            if turn == "started":
                return SessionEvent.turn_started()
            if turn == "done":
                return SessionEvent.turn_done()
            return SessionEvent.error(f"unknown turn event {turn!r}", fatal=True)
        if kind == "emit":
            return SessionEvent.emit(
                str(record.get("channel", "out")),
                int(record.get("seq", 0)),
                record.get("payload"),
            )
        if kind == "error":
            return SessionEvent.error(
                str(record.get("reason", "")),
                fatal=bool(record.get("fatal", False)),
            )
        if kind == "closed":
            reason = record.get("reason")
            return SessionEvent.closed(
                reason if reason is None or isinstance(reason, str) else str(reason)
            )
        return SessionEvent.error(f"unknown session event kind {kind!r}", fatal=True)

    def events(self) -> AsyncIterator[SessionEvent]:
        if self._events_subscribed:
            raise JulepError("session events() is single-consumer per handle")
        self._events_subscribed = True

        async def gen() -> AsyncIterator[SessionEvent]:
            last_eseq = 0
            last_acked_eseq = 0
            while True:
                if last_eseq > last_acked_eseq:
                    try:
                        await self._wfhandle.execute_update(
                            "ack_events",
                            {"eseq": last_eseq},
                        )
                        last_acked_eseq = last_eseq
                    except Exception:
                        if self._close_requested:
                            last_acked_eseq = last_eseq
                            continue
                        # A fatal workflow can complete before the lazy ack for
                        # an already-delivered event is accepted. Delivery has
                        # advanced, so keep reading the durable log.
                        last_acked_eseq = last_eseq
                        continue

                try:
                    records = await self._wfhandle.query("events")
                except Exception as exc:
                    yield SessionEvent.error(str(exc), fatal=True)
                    yield SessionEvent.closed()
                    return

                next_item: Optional[dict[str, Any]] = None
                for item in sorted(records, key=lambda entry: int(entry.get("eseq", 0))):
                    if int(item.get("eseq", 0)) > last_eseq:
                        next_item = dict(item)
                        break

                if next_item is not None:
                    last_eseq = int(next_item.get("eseq", 0))
                    event = self._event_from_record(next_item)
                    yield event
                    if event.is_closed:
                        if last_eseq > last_acked_eseq:
                            try:
                                await self._wfhandle.execute_update(
                                    "ack_events",
                                    {"eseq": last_eseq},
                                )
                                last_acked_eseq = last_eseq
                            except Exception:
                                pass
                        return
                    continue

                try:
                    snap = await self.state()
                except Exception as exc:
                    yield SessionEvent.error(str(exc), fatal=True)
                    yield SessionEvent.closed()
                    return
                if snap.get("closed") and self._close_requested:
                    # The workflow appends a durable Closed event after quiescing;
                    # keep polling for that record unless the query path fails.
                    pass
                await asyncio.sleep(self._poll_s)

        return gen()


__all__ = [
    "ExecutionPolicy",
    "FlowWorkflow",
    "SessionWorkflow",
    "RecvTimeout",
    "AgentWorkflow",
    "FlowInput",
    "SessionInput",
    "AgentInput",
    "finishTrajectory",
    "startTrajectory",
    "flushStructural",
    "runSubCapture",
    "build_flow_input",
    "run_flow",
    "start_flow",
    "TemporalSessionHandle",
]
