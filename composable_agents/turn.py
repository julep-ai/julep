"""The agent loop as an iterated endomorphism on AgentState (design:
docs/design/agent-loop-as-turn.md). Pure: no IO, no Temporal, no IR emitted.

A ``Step`` is one round in the turn category — ``AgentState -> (AgentState |
Halt)``, the operational reading of algebra.hs's ``Flow (a,s) (Either s b)``.
``drive`` iterates a Step to its verdict; ``Op.ITER_UP_TO`` is deliberately NOT
folded in here (its do-while convergence + causal threading would regress — see
the design note).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Optional, Union

from .agent_loop import AgentState, terminal_result


@dataclass(frozen=True)
class Halt:
    """A round's verdict (algebra.hs's ``Right b``). Cost/round/trace accrued on
    the shared AgentState before the Halt survive, because ``drive`` reads that
    same mutated state when it builds the terminal_result."""

    status: str
    output: Any = None
    reason: Optional[str] = None


StepResult = Union[AgentState, Halt]
Step = Callable[[AgentState], Awaitable[StepResult]]
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


__all__ = ["Halt", "StepResult", "Step", "Halter", "Finalize", "drive"]
