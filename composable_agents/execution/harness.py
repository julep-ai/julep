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
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Awaitable, Callable, Optional, Sequence

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError

# Import the pure pieces through the sandbox-safe import pass so Temporal's
# workflow sandbox does not trip over disallowed modules at definition time.
with workflow.unsafe.imports_passed_through():
    from .. import agent_loop as al
    from ..contracts import ToolContract, manifest_from_json
    from ..errors import ComposableAgentsError
    from ..ir import Node, toolref_key
    from ..projection import InMemoryProjection, ProjectionEmitter
    from .timeouts import activity_timeout
    from .interpreter import (
        BranchThunk,
        Result,
        call_contract,
        call_ref_key,
        interpret,
        race_first_from_thunks,
    )
    from .activities import (
        CallHandInput,
        CompilePlanInput,
        InvokeBrainInput,
        callHand,
        compilePlan,
        invokeBrain,
        resolveAgentSpec,
        resolveRuntimeCapabilities,
        resolveSubflow,
        verifyPures,
    )


# --------------------------------------------------------------------------- #
# Tunable execution policy (a §6 open seam; override per deployment).
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ExecutionPolicy:
    hand_timeout_s: int = 30
    brain_timeout_s: int = 120
    plan_timeout_s: int = 120
    sub_task_timeout_s: int = 3600
    agent_task_timeout_s: int = 3600
    # Retry shaping.
    idempotent_max_attempts: int = 5
    write_max_attempts: int = 3
    initial_retry_s: float = 1.0
    retry_backoff: float = 2.0
    max_retry_interval_s: int = 60

    def to_json(self) -> dict[str, Any]:
        return {
            "handTimeoutS": self.hand_timeout_s,
            "brainTimeoutS": self.brain_timeout_s,
            "planTimeoutS": self.plan_timeout_s,
            "subTaskTimeoutS": self.sub_task_timeout_s,
            "agentTaskTimeoutS": self.agent_task_timeout_s,
            "idempotentMaxAttempts": self.idempotent_max_attempts,
            "writeMaxAttempts": self.write_max_attempts,
            "initialRetryS": self.initial_retry_s,
            "retryBackoff": self.retry_backoff,
            "maxRetryIntervalS": self.max_retry_interval_s,
        }

    @staticmethod
    def from_json(d: Optional[dict[str, Any]]) -> "ExecutionPolicy":
        d = d or {}
        base = ExecutionPolicy()
        return ExecutionPolicy(
            hand_timeout_s=d.get("handTimeoutS", base.hand_timeout_s),
            brain_timeout_s=d.get("brainTimeoutS", base.brain_timeout_s),
            plan_timeout_s=d.get("planTimeoutS", base.plan_timeout_s),
            sub_task_timeout_s=d.get("subTaskTimeoutS", base.sub_task_timeout_s),
            agent_task_timeout_s=d.get("agentTaskTimeoutS", base.agent_task_timeout_s),
            idempotent_max_attempts=d.get("idempotentMaxAttempts", base.idempotent_max_attempts),
            write_max_attempts=d.get("writeMaxAttempts", base.write_max_attempts),
            initial_retry_s=d.get("initialRetryS", base.initial_retry_s),
            retry_backoff=d.get("retryBackoff", base.retry_backoff),
            max_retry_interval_s=d.get("maxRetryIntervalS", base.max_retry_interval_s),
        )


# Errors that represent a settled policy decision must never be retried.
_NON_RETRYABLE = [
    "CapabilityDenied",
    "PlanRejected",
    "ValidationError",
    "FreezeError",
    "PureDriftError",
]


def _retry_policy_for(contract: ToolContract, policy: ExecutionPolicy) -> RetryPolicy:
    """Per-tool retry policy: liberal for idempotent reads, cautious otherwise."""
    attempts = al.retry_max_attempts_for_contract(
        contract,
        idempotent_max_attempts=policy.idempotent_max_attempts,
        write_max_attempts=policy.write_max_attempts,
    )
    return RetryPolicy(
        initial_interval=timedelta(seconds=policy.initial_retry_s),
        backoff_coefficient=policy.retry_backoff,
        maximum_interval=timedelta(seconds=policy.max_retry_interval_s),
        maximum_attempts=attempts,
        non_retryable_error_types=_NON_RETRYABLE,
    )


_BRAIN_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=60),
    maximum_attempts=4,
    non_retryable_error_types=_NON_RETRYABLE,
)


def _toolref_json_from_key(key: str) -> dict[str, Any]:
    """Reverse of :func:`~composable_agents.ir.toolref_key`.

    A granted-tool key is ``"server/tool"`` for an MCP tool or a bare name for a
    native hand; the agent loop calls tools by key, so this maps back to the
    ``ToolRef`` JSON the ``callHand`` activity expects (MCP routes through the
    worker's MCP caller, native through its hand URL).
    """
    if "/" in key:
        server, tool = key.split("/", 1)
        return {"kind": "mcp", "server": server, "tool": tool}
    return {"kind": "native", "name": key}


def _manifest_contracts_for_agent(
    manifest,
    granted_tools: Optional[Sequence[str]],
    max_call_limits: Optional[dict[str, int]] = None,
) -> dict[str, dict[str, Any]]:
    """Serialize frozen contracts by tool key for the child agent workflow."""
    wanted = None if granted_tools is None else set(granted_tools)
    contracts: dict[str, dict[str, Any]] = {}
    for frozen in manifest.values():
        key = toolref_key(frozen.ref)
        if wanted is None or key in wanted:
            payload = frozen.contract.to_json()
            if max_call_limits is not None and key in max_call_limits:
                payload["maxCalls"] = int(max_call_limits[key])
            contracts[key] = payload
    return contracts


def _max_call_limits_from_contracts(
    contracts: Optional[dict[str, dict[str, Any]]],
) -> Optional[dict[str, int]]:
    limits: dict[str, int] = {}
    for tool, raw in (contracts or {}).items():
        limit = raw.get("maxCalls", raw.get("max_calls"))
        if limit is not None:
            limits[tool] = int(limit)
    return limits or None


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
    policy: Optional[dict[str, Any]] = None
    resolve_spec: bool = True


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
    ) -> None:
        self.manifest = manifest
        self.emitter = emitter
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
        # Pure functions are resolved from the in-process registry; they must be
        # deterministic by contract (see purity.py), so this is replay-safe.
        from ..purity import get_pure as _gp

        return _gp(name)

    def charge_call(self, tool_key: str) -> None:
        limit = self._max_call_limits.get(tool_key)
        if limit is None:
            return
        count = self._call_counts.get(tool_key, 0)
        if count >= limit:
            from ..errors import CapabilityDenied

            raise CapabilityDenied(f"tool {tool_key!r} exceeded maxCalls={limit}")
        self._call_counts[tool_key] = count + 1

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
            ),
            start_to_close_timeout=activity_timeout(timeout_s, self._policy.hand_timeout_s),
            retry_policy=_retry_policy_for(contract, self._policy),
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
            InvokeBrainInput(brain=brain, value=value, cid=cid),
            start_to_close_timeout=activity_timeout(timeout_s, self._policy.brain_timeout_s),
            retry_policy=_BRAIN_RETRY,
        )

    async def compile_plan(self, planner: str, value: Any, cid: str) -> Node:
        plan_json = await workflow.execute_activity(
            compilePlan,
            CompilePlanInput(planner=planner, value=value, cid=cid, manifest=self._manifest_json),
            start_to_close_timeout=timedelta(seconds=self._policy.plan_timeout_s),
            retry_policy=_BRAIN_RETRY,
        )
        return Node.from_json(plan_json)

    async def run_sub(self, ref: str, contract, value: Any, cid: str) -> Any:
        # A Sub is a child flow; the firewall is structural (surface shape is
        # already opaque), so the child's value crosses unchanged.
        child_id = self._child_id("sub", cid)
        return await workflow.execute_child_workflow(
            FlowWorkflow.run,
            FlowInput(
                session_id=child_id,
                input=value,
                ref=ref,
                policy=self._policy.to_json(),
                max_call_limits=self._max_call_limits,
                call_counts=dict(self._call_counts),
            ),
            id=child_id,
            task_timeout=timedelta(seconds=self._policy.sub_task_timeout_s),
        )

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

            tools = app_config.get("tools") if "tools" in app_config else None
            granted_tools = None if tools is None else list(tools)
            subflows = app_config.get("subflows") if "subflows" in app_config else None
            granted_subflows = None if subflows is None else list(subflows)
            if tools is not None:
                granted_contracts = _manifest_contracts_for_agent(
                    self.manifest,
                    granted_tools,
                    self._max_call_limits,
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
                policy=self._policy.to_json(),
            ),
            id=child_id,
            task_timeout=timedelta(seconds=self._policy.agent_task_timeout_s),
        )

    async def human_gate(self, value: Any, cid: str, timeout_s: Optional[int]) -> Any:
        return await self._gate_waiter(value, cid, timeout_s)

    # --- concurrency (deterministic under Temporal's asyncio) --- #
    async def gather(self, coros: Sequence[Awaitable[Any]]) -> list[Any]:
        return list(await asyncio.gather(*coros))

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

    # ----- entrypoint ------------------------------------------------------- #
    @workflow.run
    async def run(self, inp: FlowInput) -> Any:
        policy = ExecutionPolicy.from_json(inp.policy)
        flow_json = inp.flow_json
        manifest_json = inp.manifest_json
        pinned_pures = inp.pinned_pures
        max_call_limits = inp.max_call_limits
        call_counts = inp.call_counts

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
        )

        try:
            result: Result = await interpret(flow, inp.input, env)
        except ComposableAgentsError as exc:
            raise ApplicationError(
                str(exc),
                type=type(exc).__name__,
                non_retryable=True,
            ) from exc
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

    @workflow.run
    async def run(self, inp: AgentInput) -> dict[str, Any]:
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

        state = al.AgentState.from_json(inp.state) if inp.state else al.AgentState(last=inp.input)

        while True:
            if state.round >= cfg.max_rounds:
                return al.terminal_result("max_rounds", state)

            # 1) Check the controller's own cost before spending on it, then ask
            # the controller what to do and charge the per-round think cost.
            controller_precheck = al.precheck_controller(state, cfg)
            if controller_precheck is not None:
                return controller_precheck

            reply = await workflow.execute_activity(
                invokeBrain,
                InvokeBrainInput(
                    brain=inp.controller,
                    value={"input": state.last, "trace": [t.to_json() for t in state.trace]},
                    cid=f"{inp.session_id}-round-{state.round}",
                ),
                start_to_close_timeout=timedelta(seconds=policy.brain_timeout_s),
                retry_policy=_BRAIN_RETRY,
            )
            state.charge(cfg.think_cost)
            action = al.interpret_brain_reply(reply, strict=not cfg.permissive_controller)

            # 2) Terminal decisions end the loop.
            if action.decision is al.Decision.FINISH:
                return al.terminal_result("done", state, output=action.payload)
            if action.decision is al.Decision.ESCALATE:
                return al.terminal_result("escalated", state, reason=str(action.payload))
            if action.decision is al.Decision.CONTROLLER_ERROR:
                return al.terminal_result("controller_error", state, reason=str(action.payload))

            # 3) Budget guard before doing any work this round.
            cost = al.action_cost(action)
            if al.would_exceed_budget(state, cost, cfg.budget):
                return al.terminal_result("over_budget", state)

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
                    return al.terminal_result("denied", state, reason=denial.reason)
                denial = al.charge_tool_call(state, tool, contracts)
                if denial is not None:
                    return al.terminal_result("denied", state, reason=denial.reason)
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
                    ),
                    start_to_close_timeout=timedelta(seconds=policy.hand_timeout_s),
                    retry_policy=_retry_policy_for(contract, policy),
                )
                state.charge(cost)
                state.last = out
                state.record(al.TraceEntry(decision="call", ref=tool, cost=cost))

            else:  # Decision.SUB
                ref = action.payload["ref"]
                denial = al.authorize_subflow(
                    ref,
                    granted_subflows=(
                        None if granted_subflows is None else set(granted_subflows)
                    ),
                )
                if denial is not None:
                    return al.terminal_result("denied", state, reason=denial.reason)
                sub_input = action.payload.get("input")
                if sub_input is None:
                    sub_input = state.last
                child_id = f"{inp.session_id}-sub-{state.round}"
                out = await workflow.execute_child_workflow(
                    FlowWorkflow.run,
                    FlowInput(
                        session_id=child_id,
                        input=sub_input,
                        ref=ref,
                        policy=policy.to_json(),
                        max_call_limits=_max_call_limits_from_contracts(contracts),
                        call_counts=dict(state.call_counts),
                    ),
                    id=child_id,
                    task_timeout=timedelta(seconds=policy.sub_task_timeout_s),
                )
                state.charge(cost)
                state.last = out
                state.record(
                    al.TraceEntry(decision="sub", ref=ref, shape=action.payload.get("shape"), cost=cost)
                )

            state.round += 1

            # 5) §6 seam: truncate history by continuing as new with carried state.
            if al.should_continue_as_new(state, cfg):
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
) -> Any:
    """Start :class:`FlowWorkflow` for a frozen flow and await its result.

    ``client`` is a connected ``temporalio.client.Client``. ``flow_json`` /
    ``manifest_json`` come from :func:`composable_agents.freeze.freeze` (then
    serialized). The workflow id is the session id, so a re-submission with the
    same id is deduplicated by Temporal.
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
    "run_flow",
    "start_flow",
]
