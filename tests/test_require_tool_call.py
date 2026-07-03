from __future__ import annotations

import asyncio
from typing import Any

from composable_agents import Agent, tool
from composable_agents.agent_loop import AgentConfig, drive_agent_loop
from composable_agents.dotctx import Reasoner

REQUIRE_TOOL_CALL_ERROR = "require_tool_call: reply with a tool call, not text"
REQUIRE_TOOL_CALL_REASON = "require_tool_call: controller never called a tool"
REASK_TRACE = {
    "decision": "reask",
    "cost": 0.0,
    "error": REQUIRE_TOOL_CALL_ERROR,
}


def test_require_tool_call_reasks_after_text_then_accepts_tool_call() -> None:
    seen_payloads: list[dict[str, Any]] = []

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        seen_payloads.append(payload)
        if len(seen_payloads) == 1:
            return {"output": "premature text"}
        if len(seen_payloads) == 2:
            assert payload["input"] == {
                "error": REQUIRE_TOOL_CALL_ERROR,
                "reply": "premature text",
            }
            assert payload["trace"] == [REASK_TRACE]
            return {"tool": "lookup", "input": {"q": "julep"}}
        return {"output": "final"}

    async def call_tool(actual_tool: str, value: Any) -> Any:
        assert actual_tool == "lookup"
        assert value == {"q": "julep"}
        return {"ok": True}

    out = asyncio.run(
        drive_agent_loop(
            input={"task": "go"},
            cfg=AgentConfig(require_tool_call=True),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
        )
    )

    assert out["status"] == "done"
    assert out["output"] == "final"
    assert out["trace"] == [
        REASK_TRACE,
        {"decision": "call", "cost": 1.0, "ref": "lookup"},
    ]


def test_require_tool_call_halts_after_two_reasks() -> None:
    seen_payloads: list[dict[str, Any]] = []

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        seen_payloads.append(payload)
        return {"output": "text"}

    async def call_tool(actual_tool: str, value: Any) -> Any:
        raise AssertionError(f"tool should not run: {actual_tool} {value!r}")

    out = asyncio.run(
        drive_agent_loop(
            input={"task": "go"},
            cfg=AgentConfig(require_tool_call=True),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
        )
    )

    assert out["status"] == "controller_error"
    assert out["reason"] == REQUIRE_TOOL_CALL_REASON
    assert [entry for entry in out["trace"] if entry["decision"] == "reask"] == [
        REASK_TRACE,
        REASK_TRACE,
    ]
    assert len(seen_payloads) == 3


def test_require_tool_call_allows_finish_after_successful_tool_call() -> None:
    seen_payloads: list[dict[str, Any]] = []

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        seen_payloads.append(payload)
        if len(seen_payloads) == 1:
            return {"tool": "lookup", "input": "first"}
        return {"output": "answer"}

    async def call_tool(actual_tool: str, value: Any) -> Any:
        assert (actual_tool, value) == ("lookup", "first")
        return {"lookup": "ok"}

    out = asyncio.run(
        drive_agent_loop(
            input="q",
            cfg=AgentConfig(require_tool_call=True),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
        )
    )

    assert out["status"] == "done"
    assert out["output"] == "answer"
    assert [entry for entry in out["trace"] if entry["decision"] == "reask"] == []
    assert out["trace"] == [{"decision": "call", "cost": 1.0, "ref": "lookup"}]


def test_require_tool_call_does_not_suppress_escalate() -> None:
    async def invoke_controller(payload: dict[str, Any]) -> Any:
        return {"escalate": "need human"}

    async def call_tool(actual_tool: str, value: Any) -> Any:
        raise AssertionError(f"tool should not run: {actual_tool} {value!r}")

    out = asyncio.run(
        drive_agent_loop(
            input="q",
            cfg=AgentConfig(require_tool_call=True),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
        )
    )

    assert out["status"] == "escalated"
    assert out["reason"] == "need human"
    assert out["trace"] == []


def test_agent_facade_require_tool_call_max_rounds_with_tool_call_is_success() -> None:
    @tool(name="require_tool_call_side_effect")
    def side_effect(value: Any) -> dict[str, Any]:
        return {"side_effect": value}

    def llm(_reasoner_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"tool": side_effect.name, "input": payload["input"]}

    agent = Agent(
        Reasoner(
            name="tests.require_tool_call.facade.required",
            model="local:demo",
            require_tool_call=True,
        ),
        tools=[side_effect],
        llm=llm,
        max_rounds=2,
    )

    assert agent._cfg.require_tool_call is True

    result = agent.run({"task": "side effect"})

    assert result.ok is True
    assert result.output is None
    assert result["reason"] == "max_rounds"
    assert any(
        entry["decision"] == "call" and "error" not in entry
        for entry in result.trace
    )


def test_agent_facade_without_require_tool_call_keeps_max_rounds_failure() -> None:
    @tool(name="optional_tool_call_side_effect")
    def side_effect(value: Any) -> dict[str, Any]:
        return {"side_effect": value}

    def llm(_reasoner_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"tool": side_effect.name, "input": payload["input"]}

    agent = Agent(
        Reasoner(name="tests.require_tool_call.facade.optional", model="local:demo"),
        tools=[side_effect],
        llm=llm,
        max_rounds=2,
    )

    result = agent.run({"task": "side effect"})

    assert result.ok is False
    assert result.status == "max_rounds"


def test_require_tool_call_absent_preserves_text_finish_behavior() -> None:
    async def invoke_controller(payload: dict[str, Any]) -> Any:
        return {"output": "text"}

    async def call_tool(actual_tool: str, value: Any) -> Any:
        raise AssertionError(f"tool should not run: {actual_tool} {value!r}")

    out = asyncio.run(
        drive_agent_loop(
            input="q",
            cfg=AgentConfig(),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
        )
    )

    assert out["status"] == "done"
    assert out["output"] == "text"
    assert out["trace"] == []


def test_agent_config_require_tool_call_json_round_trips() -> None:
    required = AgentConfig(require_tool_call=True)
    required_json = required.to_json()
    assert required_json["requireToolCall"] is True

    plain_json = AgentConfig().to_json()
    assert "requireToolCall" not in plain_json

    assert AgentConfig.from_json({"requireToolCall": True}).require_tool_call is True
    assert AgentConfig.from_json({}).require_tool_call is False
    assert AgentConfig.from_json(required_json).require_tool_call is True
