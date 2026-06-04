from __future__ import annotations

import asyncio
from dataclasses import replace
from typing import Any

import pytest

from composable_agents import Agent, AgentConfig, call, freeze, mcp, seq, tool
from composable_agents.errors import CapabilityDenied, ValidationError
from composable_agents.agent_loop import drive_agent_loop
from composable_agents.execution.interpreter import InMemoryEnv, interpret
from composable_agents.kinds import EnforcementMode
from composable_agents.projection import InMemoryProjection, ProjectionEmitter
from conftest import read_snapshot, run


def test_in_memory_env_dev_allows_max_calls_prod_gap() -> None:
    calls = {"count": 0}

    def inc(value: int) -> int:
        calls["count"] += 1
        return value + 1

    flow = seq(call(mcp("srv", "inc")), call(mcp("srv", "inc")))
    frozen = freeze(flow, read_snapshot("inc"))

    strict_env = InMemoryEnv(
        frozen.manifest,
        ProjectionEmitter(InMemoryProjection()),
        hands={"srv/inc": inc},
        max_calls={"srv/inc": 1},
    )
    with pytest.raises(CapabilityDenied):
        run(interpret(frozen.flow, 5, strict_env))
    assert calls["count"] == 1

    calls["count"] = 0
    dev_env = InMemoryEnv(
        frozen.manifest,
        ProjectionEmitter(InMemoryProjection()),
        hands={"srv/inc": inc},
        max_calls={"srv/inc": 1},
        mode=EnforcementMode.DEV,
    )

    out = run(interpret(frozen.flow, 5, dev_env))

    assert out.value == 7
    assert calls["count"] == 2
    assert dev_env.call_counts == {"srv/inc": 2}
    assert dev_env.dev_warnings == [
        {"code": "CAP_TOOL_DENIED_RUNTIME", "tool": "srv/inc", "limit": 1}
    ]


def test_drive_agent_loop_dev_allows_ungranted_tool_with_prod_gap() -> None:
    async def call_tool(tool_name: str, value: Any) -> dict[str, Any]:
        return {"tool": tool_name, "value": value}

    async def strict_controller(_payload: dict[str, Any]) -> dict[str, Any]:
        return {"tool": "net/fetch", "input": "https://example.com"}

    strict = asyncio.run(
        drive_agent_loop(
            input="q",
            cfg=AgentConfig(),
            invoke_controller=strict_controller,
            call_tool=call_tool,
            granted={"calc/add"},
        )
    )
    assert strict["status"] == "denied"
    assert "not granted" in strict["reason"]
    assert "prodGap" not in strict

    replies = [
        {"tool": "net/fetch", "input": "https://example.com"},
        {"output": "done"},
    ]
    seen_tools: list[str] = []

    async def dev_controller(_payload: dict[str, Any]) -> dict[str, Any]:
        return replies.pop(0)

    async def dev_call_tool(tool_name: str, value: Any) -> dict[str, Any]:
        seen_tools.append(tool_name)
        return {"tool": tool_name, "value": value}

    dev = asyncio.run(
        drive_agent_loop(
            input="q",
            cfg=AgentConfig(mode=EnforcementMode.DEV),
            invoke_controller=dev_controller,
            call_tool=dev_call_tool,
            granted={"calc/add"},
        )
    )

    assert dev["status"] == "done"
    assert seen_tools == ["net/fetch"]
    assert dev["prodGap"] == ["tool 'net/fetch' is not granted"]


def test_drive_agent_loop_dev_allows_max_calls_with_prod_gap() -> None:
    async def call_tool(_tool_name: str, value: int) -> int:
        return value + 1

    async def strict_controller(payload: dict[str, Any]) -> dict[str, Any]:
        return {"tool": "t", "input": payload["input"]}

    strict = asyncio.run(
        drive_agent_loop(
            input=0,
            cfg=AgentConfig(),
            invoke_controller=strict_controller,
            call_tool=call_tool,
            contracts={"t": {"maxCalls": 1}},
        )
    )
    assert strict["status"] == "denied"
    assert strict["reason"] == "tool 't' exceeded maxCalls=1"

    replies = [
        {"tool": "t", "input": 0},
        {"tool": "t", "input": 1},
        {"output": "done"},
    ]

    async def dev_controller(_payload: dict[str, Any]) -> dict[str, Any]:
        return replies.pop(0)

    dev = asyncio.run(
        drive_agent_loop(
            input=0,
            cfg=AgentConfig(mode=EnforcementMode.DEV),
            invoke_controller=dev_controller,
            call_tool=call_tool,
            contracts={"t": {"maxCalls": 1}},
        )
    )

    assert dev["status"] == "done"
    assert dev["trace"] == [
        {"decision": "call", "cost": 1.0, "ref": "t"},
        {"decision": "call", "cost": 1.0, "ref": "t"},
    ]
    assert dev["prodGap"] == ["tool 't' exceeded maxCalls=1"]


def test_agent_config_mode_round_trips_and_defaults_strict() -> None:
    encoded = AgentConfig(mode=EnforcementMode.DEV).to_json()

    assert encoded["mode"] == "dev"
    assert AgentConfig.from_json(encoded).mode is EnforcementMode.DEV
    assert AgentConfig.from_json({}).mode is EnforcementMode.STRICT


def test_agent_facade_dev_constructs_dangerous_tool_with_prod_gap() -> None:
    @tool(effect="dangerous")
    def danger(value: str) -> str:
        return value

    with pytest.raises(ValidationError, match="CAP_APP_APPROVAL_TOOL"):
        Agent("m", tools=[danger], name="agent_dev_danger_strict")

    agent = Agent("m", tools=[danger], name="agent_dev_danger", mode="dev")

    assert agent.deployment().prod_gap


def test_agent_facade_dev_allows_over_called_tool() -> None:
    replies = [
        {"tool": "limited", "input": 0},
        {"tool": "limited", "input": 1},
        {"output": "done"},
    ]
    calls: list[int] = []

    def llm(_brain_name: str, _payload: dict[str, Any]) -> dict[str, Any]:
        return replies.pop(0)

    @tool(effect="read", idempotent=True)
    def limited(value: int) -> int:
        calls.append(value)
        return value + 1

    agent = Agent("m", tools=[limited], name="agent_dev_limited", llm=llm, mode="dev")
    assert agent.deployment().capabilities is not None
    grant = agent.deployment().capabilities.tools["limited"]
    agent.deployment().capabilities.tools["limited"] = replace(grant, max_calls=1)

    result = agent.run(0)

    assert result["status"] == "done"
    assert calls == [0, 1]
    assert result["prodGap"] == ["tool 'limited' exceeded maxCalls=1"]
    assert "denied" not in result


def test_agent_facade_dev_unregistered_tool_returns_placeholder_prod_gap() -> None:
    replies = [
        {"tool": "ungranted_tool", "input": "x"},
        {"output": "done"},
    ]
    seen_payloads: list[dict[str, Any]] = []

    def llm(_brain_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        seen_payloads.append(payload)
        return replies.pop(0)

    @tool(effect="read", idempotent=True)
    def granted_read_tool(value: str) -> str:
        return f"read:{value}"

    strict_agent = Agent(
        "m",
        tools=[granted_read_tool],
        name="agent_strict_unregistered_tool",
        llm=lambda _brain_name, _payload: {"tool": "ungranted_tool", "input": "x"},
    )
    strict = strict_agent.run("start")
    assert strict["status"] == "denied"
    assert strict["reason"] == "tool 'ungranted_tool' is not granted"

    dev_agent = Agent(
        "m",
        tools=[granted_read_tool],
        name="agent_dev_unregistered_tool",
        llm=llm,
        mode="dev",
    )

    result = dev_agent.run("start")

    placeholder = {
        "error": "tool 'ungranted_tool' unavailable (dev mode: not a registered tool of this agent)"
    }
    assert result["status"] == "done"
    assert result["prodGap"] == ["tool 'ungranted_tool' is not granted"]
    assert result["trace"] == [
        {"decision": "call", "cost": 1.0, "ref": "ungranted_tool"}
    ]
    assert seen_payloads[1]["input"] == placeholder
