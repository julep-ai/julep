import asyncio
from typing import Any

from composable_agents.agent_loop import AgentState
from composable_agents.turn import Halt, drive


def test_drive_accumulates_then_halts() -> None:
    # A step that bumps round/cost twice, then halts with the carried state.
    async def step(s: AgentState) -> Any:
        if s.round >= 2:
            return Halt("done", output=s.last)
        s.round += 1
        s.charge(1.0)
        s.last = s.round
        return s

    out = asyncio.run(drive(step, AgentState(last=0), halt=lambda s: None))
    assert out == {"status": "done", "output": 2, "rounds": 2, "cost": 2.0, "trace": []}


def test_drive_pre_round_halt_wins_before_step() -> None:
    async def step(s: AgentState) -> Any:  # must never run
        raise AssertionError("step ran despite pre-round halt")

    out = asyncio.run(
        drive(step, AgentState(last="x"), halt=lambda s: Halt("max_rounds"))
    )
    assert out == {"status": "max_rounds", "output": "x", "rounds": 0, "cost": 0.0, "trace": []}
