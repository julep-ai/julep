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


from composable_agents.agent_loop import AgentConfig, Decision
from composable_agents.kinds import EnforcementMode
from composable_agents.turn import controller_turn, pre_round, make_finalize


def test_controller_turn_call_round_records_trace() -> None:
    async def invoke_controller(_p):  # one CALL round
        return {"tool": "calc/add", "input": 5}

    async def call_tool(tool, value):
        assert (tool, value) == ("calc/add", 5)
        return value * 2

    step = controller_turn(
        cfg=AgentConfig(), invoke_controller=invoke_controller, call_tool=call_tool,
        run_subflow=None, granted=None, granted_subflows=None, contracts=None,
        mode=EnforcementMode.STRICT, prod_gap=[],
    )
    s = AgentState(last=1)
    out = asyncio.run(step(s))
    assert out is s and s.round == 1 and s.last == 10
    assert s.spent == 3.0  # think_cost(2.0) + DEFAULT_TOOL_COST(1.0)
    assert [t.to_json() for t in s.trace] == [{"decision": "call", "cost": 1.0, "ref": "calc/add"}]


def test_controller_turn_finish_returns_halt() -> None:
    async def invoke_controller(_p):
        return {"output": "ok"}

    step = controller_turn(
        cfg=AgentConfig(), invoke_controller=invoke_controller, call_tool=None,
        run_subflow=None, granted=None, granted_subflows=None, contracts=None,
        mode=EnforcementMode.STRICT, prod_gap=[],
    )
    out = asyncio.run(step(AgentState(last="q")))
    assert isinstance(out, Halt) and out.status == "done" and out.output == "ok"


def test_pre_round_max_rounds_and_budget() -> None:
    from composable_agents.capabilities import Budget
    over = pre_round(AgentConfig(max_rounds=1))
    s = AgentState(); s.round = 1
    assert isinstance(over(s), Halt) and over(s).status == "max_rounds"
