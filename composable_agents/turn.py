"""The agent loop as an iterated endomorphism on AgentState (design:
docs/design/agent-loop-as-turn.md). Pure: no IO, no Temporal, no IR emitted.

A ``Step`` is one round in the turn category — ``AgentState -> (AgentState |
Halt)``, the operational reading of algebra.hs's ``Flow (a,s) (Either s b)``.
``drive`` iterates a Step to its verdict; ``Op.ITER_UP_TO`` is deliberately NOT
folded in here (its do-while convergence + causal threading would regress — see
the design note).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Coroutine
from dataclasses import dataclass
from typing import Any, Optional, Union

from .agent_loop import (
    AgentConfig,
    AgentContractMap,
    AgentState,
    CallDenial,
    TraceEntry,
    action_cost,
    authorize_call,
    authorize_subflow,
    charge_tool_call,
    interpret_brain_reply,
    terminal_result,
    would_exceed_budget,
)
from .kinds import EnforcementMode


@dataclass(frozen=True)
class Halt:
    """A round's verdict (algebra.hs's ``Right b``). Cost/round/trace accrued on
    the shared AgentState before the Halt survive, because ``drive`` reads that
    same mutated state when it builds the terminal_result."""

    status: str
    output: Any = None
    reason: Optional[str] = None


StepResult = Union[AgentState, Halt]
# A Step is always an `async def` (a coroutine), which is what `asyncio.run`
# accepts — narrower than Awaitable, and accurate for every Step in the codebase.
Step = Callable[[AgentState], Coroutine[Any, Any, StepResult]]
Halter = Callable[[AgentState], Optional[Halt]]
Finalize = Callable[[dict[str, Any]], dict[str, Any]]


async def drive(
    step: Step,
    state: AgentState,
    *,
    halt: Halter,
    finalize: Optional[Finalize] = None,
) -> dict[str, Any]:
    """Iterate ``step`` to its verdict. ``halt`` is the pre-round guard; ``step``
    mutates ``state`` in place and may itself return a Halt. ``finalize``
    post-processes the terminal dict (used for DEV-mode prodGap)."""

    def done(h: Halt) -> dict[str, Any]:
        result = terminal_result(h.status, state, output=h.output, reason=h.reason)
        return finalize(result) if finalize is not None else result

    while True:
        pre = halt(state)
        if pre is not None:
            return done(pre)
        result = await step(state)
        if isinstance(result, Halt):
            return done(result)
        state = result


def pre_round(cfg: AgentConfig) -> Halter:
    """Pre-round guards from agent_loop.py:442-449: max_rounds, then think-cost
    budget (precheck_controller). Returns a Halt or None."""
    def halt(state: AgentState) -> Optional[Halt]:
        if state.round >= cfg.max_rounds:
            return Halt("max_rounds")
        if would_exceed_budget(state, cfg.think_cost, cfg.budget):
            return Halt("over_budget")
        return None
    return halt


def make_finalize(prod_gap: list[str]) -> Finalize:
    """DEV-mode prodGap rides on every terminal result when non-empty
    (agent_loop.py:426-428, 447-449)."""
    def finalize(result: dict[str, Any]) -> dict[str, Any]:
        if prod_gap:
            result["prodGap"] = list(prod_gap)
        return result
    return finalize


def controller_turn(
    *,
    cfg: AgentConfig,
    invoke_controller: Callable[[dict[str, Any]], Awaitable[Any]],
    call_tool: Callable[[str, Any], Awaitable[Any]],
    run_subflow: Optional[Callable[[str, Any], Awaitable[Any]]],
    granted: Optional[set[str]],
    granted_subflows: Optional[set[str]],
    contracts: Optional[AgentContractMap],
    mode: EnforcementMode,
    prod_gap: list[str],
) -> Step:
    """One agent round, lifted verbatim from drive_agent_loop's while-body."""
    mode = EnforcementMode.coerce(mode)
    unconstrained = granted is None
    granted_set = set(granted or [])

    def denial_to_halt(denial: Optional[CallDenial]) -> Optional[Halt]:
        # STRICT: denial halts; DEV: warn-but-allow (record prodGap, proceed).
        if denial is None:
            return None
        if mode is EnforcementMode.DEV:
            prod_gap.append(denial.reason)
            return None
        return Halt("denied", reason=denial.reason)

    async def step(state: AgentState) -> StepResult:
        payload = {"input": state.last, "trace": [t.to_json() for t in state.trace]}
        reply = await invoke_controller(payload)
        state.charge(cfg.think_cost)
        action = interpret_brain_reply(reply, strict=not cfg.permissive_controller)

        if action.decision.value == "finish":
            return Halt("done", output=action.payload)
        if action.decision.value == "escalate":
            return Halt("escalated", reason=str(action.payload))
        if action.decision.value == "controller_error":
            return Halt("controller_error", reason=str(action.payload))

        cost = action_cost(action)
        if would_exceed_budget(state, cost, cfg.budget):
            return Halt("over_budget")

        if action.decision.value == "call":
            tool = action.payload["tool"]
            halt = denial_to_halt(authorize_call(
                tool, unconstrained=unconstrained, granted_set=granted_set,
                contracts=contracts))
            if halt is not None:
                return halt
            denial = charge_tool_call(state, tool, contracts)
            halt = denial_to_halt(denial)
            if halt is not None:
                return halt
            if denial is not None:  # DEV warn-but-allow: still count the call
                state.call_counts[tool] = state.call_counts.get(tool, 0) + 1
            call_input = action.payload.get("input")
            if call_input is None:
                call_input = state.last
            out = await call_tool(tool, call_input)
            state.charge(cost)
            state.last = out
            state.record(TraceEntry(decision="call", ref=tool, cost=cost))
        else:  # sub
            ref = action.payload["ref"]
            halt = denial_to_halt(authorize_subflow(ref, granted_subflows=granted_subflows))
            if halt is not None:
                return halt
            if run_subflow is None:
                return Halt("denied", reason=f"no subflow runner for {ref!r}")
            sub_input = action.payload.get("input")
            if sub_input is None:
                sub_input = state.last
            out = await run_subflow(ref, sub_input)
            state.charge(cost)
            state.last = out
            state.record(TraceEntry(decision="sub", ref=ref, shape=action.payload.get("shape"), cost=cost))

        state.round += 1
        return state

    return step


def with_retry(step: Step, *, attempts: int) -> Step:
    """Reissue a round that raises, up to ``attempts`` times. The Step must be
    safe to retry (no half-applied effect); use only on idempotent rounds."""
    async def wrapped(state: AgentState) -> StepResult:
        last_exc: Optional[BaseException] = None
        for _ in range(attempts):
            try:
                return await step(state)
            except Exception as exc:  # noqa: BLE001 — re-raised after attempts
                last_exc = exc
        raise last_exc  # type: ignore[misc]
    return wrapped


__all__ = [
    "Halt",
    "StepResult",
    "Step",
    "Halter",
    "Finalize",
    "drive",
    "pre_round",
    "make_finalize",
    "controller_turn",
    "with_retry",
]
