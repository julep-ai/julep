"""The durable harness (blueprint §2): Temporal workflows that run frozen IR.

This is the only module that binds the framework to Temporal. It supplies an
:class:`~composable_agents.execution.interpreter.Env` whose effect handlers are
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
  ``Idempotency-Key`` the ``callHand`` activity sends.
* **Hands / Brains** = activities (``callHand`` / ``invokeBrain``), which run
  outside the sandbox and hold all IO and non-determinism.
* **Sub** (``run_sub``) = a child :class:`FlowWorkflow`. The Joined firewall is
  structural — :func:`~composable_agents.shapes.surface_shape` already makes a
  Sub opaque (Pipeline) at the surface — so the child's value crosses while its
  internal shape does not leak into the parent's projection.
* **Agent** (``run_agent``) = a child :class:`AgentWorkflow`, deliberately *its
  own* workflow so its ``continue_as_new`` truncates only the agent's history,
  not the parent flow's.
* **Projection** is built by a *derived* path, not here: the in-workflow
  :class:`~composable_agents.projection.ProjectionEmitter` exists only to thread
  causal ids deterministically and is exposed read-only via a query; the durable
  observability sink (Postgres / OTel) is fed by an interceptor over history
  (see :mod:`composable_agents.execution.otel`). The workflow performs no
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
from typing import Any, Awaitable, Callable, Optional, Sequence

from temporalio import activity, workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError

# Best-effort swallow paths log via stdlib logging: it never raises, works
# outside a live workflow runtime (so the helpers stay unit-testable by direct
# call), and does not mutate the trajectory best-effort counter on replay, unlike
# workflow.logger (which requires a workflow context) or trajectory._best_effort
# (which would inflate the counter every time workflow code re-executes).
_LOG = logging.getLogger(__name__)

# Import the pure pieces through the sandbox-safe import pass so Temporal's
# workflow sandbox does not trip over disallowed modules at definition time.
with workflow.unsafe.imports_passed_through():
    from .. import agent_loop as al
    from ..continuation import continuation_value, is_continuation
    from ..contracts import ToolContract, contract_allows_retry, manifest_from_json
    from ..errors import ComposableAgentsError
    from ..ir import Ann, Node
    from ..projection import InMemoryProjection, ProjectionEmitter
    from ..purity import get_pure as _get_pure_from_registry
    from ..transcript import TRANSCRIPT_SCOPES, split_summary_reply, transcript_for
    from .policy import ExecutionPolicy
    from .effects import toolref_json_from_key as _toolref_json_from_key
    from .timeouts import activity_timeout
    from .interpreter import (
        BranchThunk,
        Result,
        call_contract,
        call_ref_key,
        gather_bounded,
        interpret,
        race_first_from_thunks,
    )
    from .activities import (
        CallHandInput,
        CommitStateInput,
        CompilePlanInput,
        InvokeBrainInput,
        LoadStateInput,
        PutBlobInput,
        RunSubInput,
        callHand,
        commitState,
        compilePlan,
        invokeBrain,
        loadState,
        putBlob,
        resolveAgentSpec,
        resolveRuntimeCapabilities,
        resolveSubflow,
        verifyPures,
    )


# Errors that represent a settled policy decision must never be retried.
_NON_RETRYABLE = [
    "CapabilityDenied",
    "PlanRejected",
    "ValidationError",
    "FreezeError",
    "PureDriftError",
    "PrincipalRequired",
]


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
    _traj._best_effort(lambda: sink.finish_run(run_id, status, time.time()))
    await _effects.record_marker_step(
        kind="final",
        run_id=run_id,
        root_run_id=root_run_id,
        segment_seq=inp.get("segmentSeq"),
        value=inp.get("result"),
        cid=f"{run_id}:final",
        value_kind="output",
    )


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


def _brain_retry(policy: ExecutionPolicy) -> RetryPolicy:
    """Engine retries for brain/plan activities (``brain_max_attempts``).

    Workers whose ``LlmCaller`` owns resilience (fallback chains, breakers —
    ``make_resilient_llm_caller``) should run with ``brain_max_attempts=1`` so
    these blind retries don't multiply the caller's ladder.
    """
    return RetryPolicy(
        initial_interval=timedelta(seconds=1),
        backoff_coefficient=2.0,
        maximum_interval=timedelta(seconds=60),
        maximum_attempts=policy.brain_max_attempts,
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
    # Worker-side STORE_URL and CA_BUNDLE_ALLOWED_SIGNERS remain authoritative.
    bundle: Optional[list[dict[str, str]]] = None
    # Trajectory identity: root_run_id is root session_id; segment_seq bumps on continue_as_new.
    root_run_id: Optional[str] = None
    segment_seq: int = 0


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
    state: Optional[dict[str, Any]] = None      # set on continue-as-new
    state_cursor: Optional[int] = None          # set on continue-as-new under the store path
    use_session_store: bool = False             # opt-in: route state through loadState/commitState
    policy: Optional[dict[str, Any]] = None
    resolve_spec: bool = True
    principal: Optional[dict[str, Any]] = None  # run principal (see FlowInput.principal)
    # Trajectory identity: root_run_id is root session_id; segment_seq bumps on continue_as_new.
    root_run_id: Optional[str] = None
    segment_seq: int = 0


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
        max_call_limits: Optional[dict[str, int]] = None,
        call_counts: Optional[dict[str, int]] = None,
        principal: Optional[dict[str, Any]] = None,
        root_run_id: Optional[str] = None,
        segment_seq: int = 0,
    ) -> None:
        self.manifest = manifest
        self.emitter = emitter
        self.native_call_retries = True
        self.principal = principal
        self.root_run_id = root_run_id
        self.segment_seq = segment_seq
        self._session = session_id
        self._manifest_json = manifest_json
        self._policy = policy
        self._gate_waiter = gate_waiter
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
    async def call_hand(self, node: Node, value: Any, cid: str) -> Any:
        # Frozen calls resolve through the manifest; a staged plan's calls are
        # admitted but unfrozen, so late-bind by tool ref (and use a conservative
        # contract for retry shaping).
        ref_key = call_ref_key(node, self.manifest)
        contract = call_contract(node, self.manifest)
        timeout_s = node.ann.timeout if node.ann else None
        cache = node.ann.cache.to_json() if node.ann and node.ann.cache is not None else None
        return await workflow.execute_activity(
            callHand,
            CallHandInput(
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
                kind="hand",
            ),
            start_to_close_timeout=activity_timeout(timeout_s, self._policy.hand_timeout_s),
            retry_policy=_retry_policy_for(contract, self._policy, node.ann),
        )

    async def invoke_brain(
        self,
        brain: str,
        value: Any,
        cid: str,
        timeout_s: Optional[int],
    ) -> Any:
        return await workflow.execute_activity(
            invokeBrain,
            InvokeBrainInput(
                brain=brain,
                value=value,
                cid=cid,
                principal=self.principal,
                run_id=self._session,
                root_run_id=self.root_run_id,
                segment_seq=self.segment_seq,
                op="think",
                kind="brain",
            ),
            start_to_close_timeout=activity_timeout(timeout_s, self._policy.brain_timeout_s),
            retry_policy=_brain_retry(self._policy),
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
            ),
            start_to_close_timeout=timedelta(seconds=self._policy.plan_timeout_s),
            retry_policy=_brain_retry(self._policy),
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
            ),
            id=child_id,
            task_timeout=timedelta(seconds=self._policy.sub_task_timeout_s),
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

        return await workflow.execute_child_workflow(
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
                state=state_json,
                policy=self._policy.to_json(),
                principal=self.principal,
                root_run_id=self.root_run_id,
            ),
            id=child_id,
            task_timeout=timedelta(seconds=self._policy.agent_task_timeout_s),
        )

    async def human_gate(self, value: Any, cid: str, timeout_s: Optional[int]) -> Any:
        return await self._gate_waiter(value, cid, timeout_s)

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
        self._open_gates: set[str] = set()
        self._store: Optional[InMemoryProjection] = None

    # ----- human gate plumbing --------------------------------------------- #
    @workflow.signal(name="submitHuman")
    def submit_human(self, payload: dict[str, Any]) -> None:
        """Deliver a human decision keyed by activation id (``cid``)."""
        self._human_inbox[payload["cid"]] = payload.get("value")

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

        # Pure source lookup reads the worker registry, so it stays in an
        # activity. Each FlowWorkflow verifies the pins supplied with that flow;
        # ref children verify their own pins when the subflow registry carries
        # pureSourceHashes/pinnedPures, without inheriting parent registry state.
        if pinned_pures is not None:
            await workflow.execute_activity(
                verifyPures,
                pinned_pures,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(
                    maximum_attempts=1,
                    non_retryable_error_types=_NON_RETRYABLE,
                ),
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
        node_ops = {n.id: n.op.value for n in flow.walk()}
        manifest = manifest_from_json(manifest_json or {})

        store, emitter = _make_emitter()
        self._store = store
        env = _TemporalEnv(
            manifest=manifest,
            emitter=emitter,
            session_id=inp.session_id,
            manifest_json=manifest_json,
            policy=policy,
            gate_waiter=self._await_human,
            max_call_limits=max_call_limits,
            call_counts=call_counts,
            principal=inp.principal,
            root_run_id=(inp.root_run_id or inp.session_id),
            segment_seq=inp.segment_seq,
        )
        await self._start_trajectory(inp)

        try:
            result: Result = await interpret(flow, inp.input, env)
        except ComposableAgentsError as exc:
            raise ApplicationError(
                str(exc),
                type=type(exc).__name__,
                non_retryable=True,
            ) from exc
        if is_continuation(result.value):
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
                )
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
        contracts = dict(inp.granted_contracts or {})
        grants_supplied = inp.granted_tools is not None or inp.granted_tools_unconstrained
        subflows_supplied = inp.granted_subflows is not None

        if inp.resolve_spec:
            spec = await workflow.execute_activity(
                resolveAgentSpec,
                inp.controller,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3, non_retryable_error_types=_NON_RETRYABLE),
            )
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

        cfg = al.AgentConfig.from_json(config or {})
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
            # summarization are activity work inside invokeBrain.
            transcript_plan = None
            if cfg.ctx is not None and cfg.ctx.scope in TRANSCRIPT_SCOPES:
                transcript_plan = transcript_for(state, cfg.ctx, input=inp.input)

            reply = await workflow.execute_activity(
                invokeBrain,
                InvokeBrainInput(
                    brain=inp.controller,
                    value={"input": state.last, "trace": [t.to_json() for t in state.trace]},
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
                    run_id=inp.session_id,
                    root_run_id=(inp.root_run_id or inp.session_id),
                    segment_seq=inp.segment_seq,
                    op="think",
                    kind="brain",
                ),
                start_to_close_timeout=timedelta(seconds=policy.brain_timeout_s),
                retry_policy=_brain_retry(policy),
            )
            new_summary, reply = split_summary_reply(reply)
            if new_summary is not None:
                state.summary = new_summary
            state.charge(cfg.think_cost)
            action = al.interpret_brain_reply(reply, strict=not cfg.permissive_controller)

            # 2) Terminal decisions end the loop.
            if action.decision is al.Decision.FINISH:
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
            if action.decision is al.Decision.CALL:
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
                out = await workflow.execute_activity(
                    callHand,
                    CallHandInput(
                        tool_ref=_toolref_json_from_key(tool),
                        value=call_input,
                        cid=f"{inp.session_id}-call-{state.round}",
                        principal=inp.principal,
                        run_id=inp.session_id,
                        root_run_id=(inp.root_run_id or inp.session_id),
                        segment_seq=inp.segment_seq,
                        op="call",
                        kind="hand",
                    ),
                    start_to_close_timeout=timedelta(seconds=policy.hand_timeout_s),
                    retry_policy=_retry_policy_for(contract, policy),
                )
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
                    al.TraceEntry(decision="call", ref=tool, cost=cost, output_ref=output_ref)
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
                    ),
                    id=child_id,
                    task_timeout=timedelta(seconds=policy.sub_task_timeout_s),
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
                            state=None,
                            state_cursor=cursor,
                            use_session_store=True,
                            policy=policy.to_json(),
                            resolve_spec=False,
                            principal=inp.principal,
                            root_run_id=(inp.root_run_id or inp.session_id),
                            segment_seq=inp.segment_seq + 1,
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
                            state=state.to_json(),
                            policy=policy.to_json(),
                            resolve_spec=False,
                            principal=inp.principal,
                            root_run_id=(inp.root_run_id or inp.session_id),
                            segment_seq=inp.segment_seq + 1,
                        )
                    )


# --------------------------------------------------------------------------- #
# Client helper.
# --------------------------------------------------------------------------- #
async def run_flow(
    client,
    flow_json: dict[str, Any],
    manifest_json: dict[str, Any],
    *,
    session_id: str,
    input: Any = None,
    task_queue: str = "composable-agents",
    policy: Optional[ExecutionPolicy] = None,
    pinned_pures: Optional[dict[str, str]] = None,
    max_call_limits: Optional[dict[str, int]] = None,
    principal: Optional[dict[str, Any]] = None,
    root_run_id: Optional[str] = None,
    bundle: Optional[list[dict[str, str]]] = None,
) -> Any:
    """Start :class:`FlowWorkflow` for a frozen flow and await its result.

    ``client`` is a connected ``temporalio.client.Client``. ``flow_json`` /
    ``manifest_json`` come from :func:`composable_agents.freeze.freeze` (then
    serialized). The workflow id is the session id, so a re-submission with the
    same id is deduplicated by Temporal. ``principal`` is the run's opaque
    tenant/credential reference (never a secret) — see
    :data:`~composable_agents.execution.effects.RunPrincipal`.
    """
    return await client.execute_workflow(
        FlowWorkflow.run,
        FlowInput(
            session_id=session_id,
            input=input,
            flow_json=flow_json,
            manifest_json=manifest_json,
            pinned_pures=pinned_pures,
            max_call_limits=max_call_limits,
            policy=(policy or ExecutionPolicy()).to_json(),
            principal=principal,
            root_run_id=root_run_id,
            bundle=bundle,
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
    task_queue: str = "composable-agents",
    policy: Optional[ExecutionPolicy] = None,
    pinned_pures: Optional[dict[str, str]] = None,
    max_call_limits: Optional[dict[str, int]] = None,
    principal: Optional[dict[str, Any]] = None,
    root_run_id: Optional[str] = None,
    bundle: Optional[list[dict[str, str]]] = None,
):
    """Like :func:`run_flow` but returns the :class:`WorkflowHandle` immediately.

    Use the handle to signal a human gate (``handle.signal("submitHuman", {...})``)
    or query the projection (``handle.query("projection")``) while the run is live.
    """
    return await client.start_workflow(
        FlowWorkflow.run,
        FlowInput(
            session_id=session_id,
            input=input,
            flow_json=flow_json,
            manifest_json=manifest_json,
            pinned_pures=pinned_pures,
            max_call_limits=max_call_limits,
            policy=(policy or ExecutionPolicy()).to_json(),
            principal=principal,
            root_run_id=root_run_id,
            bundle=bundle,
        ),
        id=session_id,
        task_queue=task_queue,
    )


__all__ = [
    "ExecutionPolicy",
    "FlowWorkflow",
    "AgentWorkflow",
    "FlowInput",
    "AgentInput",
    "finishTrajectory",
    "startTrajectory",
    "flushStructural",
    "runSubCapture",
    "run_flow",
    "start_flow",
]
