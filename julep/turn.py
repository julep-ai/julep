"""The agent loop as an iterated endomorphism on AgentState (design:
docs/design/agent-loop-as-turn.md). Pure: no IO, no Temporal, no IR emitted.

A ``Step`` is one round in the turn category — ``AgentState -> (AgentState |
Halt)``, the operational reading of algebra.hs's ``Flow (a,s) (Either s b)``.
``drive`` iterates a Step to its verdict; ``Op.ITER_UP_TO`` is deliberately NOT
folded in here (its do-while convergence + causal threading would regress — see
the design note).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Coroutine
from dataclasses import dataclass
from typing import Any, Optional, Union, cast

from .agent_loop import (
    AgentConfig,
    AgentContractMap,
    AgentState,
    CallDenial,
    DEFAULT_TOOL_COST,
    Decision,
    REQUIRE_TOOL_CALL_NEVER_CALLED_REASON,
    REQUIRE_TOOL_CALL_REASK_MESSAGE,
    ROUND_NOTE_KEY,
    TraceEntry,
    ToolCaller,
    action_cost,
    authorize_call,
    authorize_subflow,
    charge_tool_call,
    contract_for_tool,
    coerce_round_note,
    interpret_reasoner_reply,
    terminal_result,
    would_exceed_budget,
)
from .kinds import Effect, EnforcementMode
from .transcript import (
    TRANSCRIPT_SCOPES,
    split_summary_reply,
    transcript_for,
    unwrap_reply_meta,
)

logger = logging.getLogger("julep.turn")


@dataclass(frozen=True)
class Halt:
    """A round's verdict (algebra.hs's ``Right b``). Cost/round/trace accrued on
    the shared AgentState before the Halt survive, because ``drive`` reads that
    same mutated state when it builds the terminal_result."""

    status: str
    output: Any = None
    reason: Optional[str] = None


@dataclass(frozen=True)
class CallManyResult:
    index: int
    observation: dict[str, Any]
    trace: TraceEntry


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
    call_tool: ToolCaller,
    run_subflow: Optional[Callable[[str, Any], Awaitable[Any]]],
    granted: Optional[set[str]],
    granted_subflows: Optional[set[str]],
    contracts: Optional[AgentContractMap],
    mode: EnforcementMode,
    prod_gap: list[str],
    run_input: Any = None,
    get_pure: Optional[Callable[[str], Callable[..., Any]]] = None,
) -> Step:
    """One agent round, lifted verbatim from drive_agent_loop's while-body.

    ``run_input`` is the run's original input, used only for the transcript
    plan when ``cfg.ctx`` declares a transcript scope (agent-transcripts)."""
    mode = EnforcementMode.coerce(mode)
    unconstrained = granted is None
    granted_set = set(granted or [])
    note_fn: Optional[Callable[..., Any]] = None
    if cfg.round_note is not None:
        if get_pure is not None:
            note_fn = get_pure(cfg.round_note)
        else:
            from .registry import DEFAULT_REGISTRY

            note_fn = DEFAULT_REGISTRY.get_pure(cfg.round_note)

    def denial_to_halt(denial: Optional[CallDenial]) -> Optional[Halt]:
        # STRICT: denial halts; DEV: warn-but-allow (record prodGap, proceed).
        if denial is None:
            return None
        if mode is EnforcementMode.DEV:
            prod_gap.append(denial.reason)
            return None
        return Halt("denied", reason=denial.reason)

    async def step(state: AgentState) -> StepResult:
        payload: dict[str, Any] = {
            "input": state.last,
            "trace": [t.to_json() for t in state.trace],
        }
        if note_fn is not None:
            # Fresh each round from loop state only; deterministic under Temporal
            # replay because the function is a registered pure.
            note = coerce_round_note(note_fn({
                "round": state.round,
                "maxRounds": cfg.max_rounds,
                "spent": state.spent,
                "callCounts": dict(state.call_counts),
            }))
            if note is not None:
                # The LLM prompt path (execution/llm.py _messages) renders this
                # reserved key as a trailing system line; namespaced so ordinary
                # reasoner "note" business fields are never injected.
                payload[ROUND_NOTE_KEY] = note
        if cfg.ctx is not None and cfg.ctx.scope in TRANSCRIPT_SCOPES:
            # Transcript plan: deterministic, ref-bearing, computed in workflow
            # code. Hydration/budget/summarization happen in the invoke_reasoner
            # effect; the engine binding moves these keys onto InvokeReasonerInput.
            payload["transcript"] = transcript_for(state, cfg.ctx, input=run_input)
            payload["ctx"] = cfg.ctx.to_json()
            if cfg.summarizer is not None:
                payload["summarizer"] = cfg.summarizer
            if state.summary is not None:
                payload["summary"] = state.summary
        reply = await invoke_controller(payload)
        if isinstance(reply, dict) and "__ca_meta__" in reply and "reply" in reply:
            meta = reply["__ca_meta__"]
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
        action = interpret_reasoner_reply(
            reply,
            strict=not cfg.permissive_controller,
            native_tools=cfg.native_tools,
        )

        if action.decision.value == "finish":
            if cfg.require_tool_call and not any(
                entry.decision == "call" and entry.error is None
                for entry in state.trace
            ):
                reasks = sum(1 for entry in state.trace if entry.decision == "reask")
                if reasks >= 2:
                    return Halt(
                        "controller_error",
                        reason=REQUIRE_TOOL_CALL_NEVER_CALLED_REASON,
                    )
                message = REQUIRE_TOOL_CALL_REASK_MESSAGE
                state.last = {"error": message, "reply": action.payload}
                state.record(TraceEntry(decision="reask", error=message))
                state.round += 1
                return state
            return Halt("done", output=action.payload)
        if action.decision.value == "escalate":
            return Halt("escalated", reason=str(action.payload))
        if action.decision.value == "controller_error":
            return Halt("controller_error", reason=str(action.payload))

        cost = action_cost(action)
        if would_exceed_budget(state, cost, cfg.budget):
            return Halt("over_budget")

        if action.decision is Decision.CALL_MANY:
            calls = cast(list[dict[str, Any]], action.payload)
            for entry in calls:
                tool = cast(str, entry["tool"])
                halt = denial_to_halt(authorize_call(
                    tool, unconstrained=unconstrained, granted_set=granted_set,
                    contracts=contracts))
                if halt is not None:
                    return halt
            for entry in calls:
                tool = cast(str, entry["tool"])
                denial = charge_tool_call(state, tool, contracts)
                halt = denial_to_halt(denial)
                if halt is not None:
                    return halt
                if denial is not None:
                    state.call_counts[tool] = state.call_counts.get(tool, 0) + 1

            async def execute_entry(index: int, entry: dict[str, Any]) -> CallManyResult:
                tool = cast(str, entry["tool"])
                call_input = entry.get("input")
                if call_input is None:
                    call_input = state.last
                error: Optional[str] = None
                try:
                    out = await call_tool(tool, call_input, call_index=index)
                except Exception as exc:  # noqa: BLE001
                    error = repr(exc)
                    logger.warning("tool %r failed: %s", tool, error)
                    out = {"error": error, "tool": tool}
                return CallManyResult(
                    index=index,
                    observation={
                        "id": entry.get("id"),
                        "tool": tool,
                        "output": out,
                    },
                    trace=TraceEntry(
                        decision="call",
                        ref=tool,
                        cost=DEFAULT_TOOL_COST,
                        call_id=cast(Optional[str], entry.get("id")),
                        error=error,
                    ),
                )

            results: list[Optional[CallManyResult]] = [None] * len(calls)
            read_items = [
                (index, entry)
                for index, entry in enumerate(calls)
                if contract_for_tool(cast(str, entry["tool"]), contracts).effect is Effect.READ
            ]
            if read_items:
                read_results = await asyncio.gather(
                    *(execute_entry(index, entry) for index, entry in read_items)
                )
                for result in read_results:
                    results[result.index] = result
            for index, entry in enumerate(calls):
                if results[index] is None:
                    results[index] = await execute_entry(index, entry)

            ordered_results: list[CallManyResult] = []
            for maybe_result in results:
                assert maybe_result is not None
                ordered_results.append(maybe_result)
            state.charge(cost)
            state.last = [result.observation for result in ordered_results]
            for result in ordered_results:
                state.record(result.trace)
        elif action.decision.value == "call":
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
            error: Optional[str] = None
            try:
                out = await call_tool(tool, call_input)
            except Exception as exc:  # noqa: BLE001
                error = repr(exc)
                logger.warning("tool %r failed: %s", tool, error)
                out = {"error": error, "tool": tool}
            state.charge(cost)
            state.last = out
            state.record(TraceEntry(decision="call", ref=tool, cost=cost, error=error))
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
            error = None
            try:
                out = await run_subflow(ref, sub_input)
            except Exception as exc:  # noqa: BLE001
                error = repr(exc)
                logger.warning("subflow %r failed: %s", ref, error)
                out = {"error": error, "tool": ref}
            state.charge(cost)
            state.last = out
            state.record(
                TraceEntry(
                    decision="sub",
                    ref=ref,
                    shape=action.payload.get("shape"),
                    cost=cost,
                    error=error,
                )
            )

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
