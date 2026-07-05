from __future__ import annotations

import asyncio
from typing import Any

from julep import Budget, AgentConfig, app, freeze
from julep.agent_loop import drive_agent_loop
from julep.execution.interpreter import InMemoryEnv, interpret
from julep.projection import InMemoryProjection, ProjectionEmitter
from conftest import read_snapshot


def test_drive_agent_loop_think_call_finish() -> None:
    replies: list[dict[str, Any]] = [
        {"tool": "calc/add", "input": 2},
        {"output": "done:4"},
    ]
    seen_payloads: list[dict[str, Any]] = []

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        seen_payloads.append(payload)
        return replies.pop(0)

    async def call_tool(tool: str, value: Any) -> Any:
        assert tool == "calc/add"
        return value * 2

    out = asyncio.run(
        drive_agent_loop(
            input=1,
            cfg=AgentConfig(),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
        )
    )

    assert out == {
        "status": "done",
        "output": "done:4",
        "rounds": 1,
        "cost": 5.0,
        "trace": [{"decision": "call", "cost": 1.0, "ref": "calc/add"}],
    }
    assert seen_payloads == [
        {"input": 1, "trace": []},
        {"input": 4, "trace": [{"decision": "call", "cost": 1.0, "ref": "calc/add"}]},
    ]


def test_drive_agent_loop_max_rounds() -> None:
    async def invoke_controller(payload: dict[str, Any]) -> Any:
        return {"tool": "calc/add", "input": payload["input"]}

    async def call_tool(tool: str, value: Any) -> Any:
        return value + 1

    out = asyncio.run(
        drive_agent_loop(
            input=0,
            cfg=AgentConfig(max_rounds=2),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
        )
    )

    assert out["status"] == "max_rounds"
    assert out["output"] == 2
    assert out["rounds"] == 2
    assert out["cost"] == 6.0
    assert out["trace"] == [
        {"decision": "call", "cost": 1.0, "ref": "calc/add"},
        {"decision": "call", "cost": 1.0, "ref": "calc/add"},
    ]


def test_drive_agent_loop_denies_ungranted_tool() -> None:
    async def invoke_controller(payload: dict[str, Any]) -> Any:
        return {"tool": "net/fetch", "input": "https://example.com"}

    async def call_tool(tool: str, value: Any) -> Any:
        raise AssertionError("denied tool must not run")

    out = asyncio.run(
        drive_agent_loop(
            input="q",
            cfg=AgentConfig(),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
            granted={"calc/add"},
        )
    )

    assert out["status"] == "denied"
    assert "not granted" in out["reason"]
    assert out["cost"] == 2.0
    assert out["trace"] == []


def test_drive_agent_loop_over_budget_before_think() -> None:
    called = False

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        nonlocal called
        called = True
        return {"output": "unreachable"}

    async def call_tool(tool: str, value: Any) -> Any:
        raise AssertionError("over-budget loop must not call tools")

    out = asyncio.run(
        drive_agent_loop(
            input="q",
            cfg=AgentConfig(budget=Budget(cost=1.0)),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
        )
    )

    assert out["status"] == "over_budget"
    assert out["output"] == "q"
    assert out["cost"] == 0.0
    assert called is False


def test_drive_agent_loop_denies_second_call_via_contract_max_calls() -> None:
    async def invoke_controller(payload: dict[str, Any]) -> Any:
        return {"tool": "calc/add", "input": payload["input"]}

    async def call_tool(tool: str, value: Any) -> Any:
        return value + 1

    out = asyncio.run(
        drive_agent_loop(
            input=0,
            cfg=AgentConfig(),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
            contracts={"calc/add": {"maxCalls": 1}},
        )
    )

    assert out["status"] == "denied"
    assert "exceeded maxCalls" in out["reason"]
    assert out["output"] == 1
    assert out["rounds"] == 1
    assert out["cost"] == 5.0
    assert out["trace"] == [{"decision": "call", "cost": 1.0, "ref": "calc/add"}]


def test_drive_agent_loop_runs_end_to_end_through_interpreter() -> None:
    replies: list[dict[str, Any]] = [
        {"tool": "calc/add", "input": 2},
        {"output": "done:4"},
    ]

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        return replies.pop(0)

    async def call_tool(tool: str, value: Any) -> Any:
        assert tool == "calc/add"
        return value * 2

    frozen = freeze(app("ctrl"), read_snapshot())
    env = InMemoryEnv(
        frozen.manifest,
        ProjectionEmitter(InMemoryProjection()),
        agents={
            "ctrl": lambda v: drive_agent_loop(
                input=v,
                cfg=AgentConfig(),
                invoke_controller=invoke_controller,
                call_tool=call_tool,
            )
        },
    )

    out = asyncio.run(interpret(frozen.flow, 1, env))

    assert out.value == {
        "status": "done",
        "output": "done:4",
        "rounds": 1,
        "cost": 5.0,
        "trace": [{"decision": "call", "cost": 1.0, "ref": "calc/add"}],
    }
