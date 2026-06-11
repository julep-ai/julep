from __future__ import annotations

from typing import Any

import pytest

from composable_agents import Agent, call, native, tool
from composable_agents.flow import as_flow
from composable_agents.ir import Node
from composable_agents.transforms import normalize_ids


def _normalized_json(agent: Agent) -> dict[str, Any]:
    return normalize_ids(Node.from_json(agent.to_ir().to_json())).to_json()


def test_as_sub_requires_durable_ref() -> None:
    with pytest.raises(ValueError, match="durable ref"):
        as_flow(call(native("c3_x"))).as_sub()


def test_named_agent_split_cap_exposes_child_deployment_metadata() -> None:
    @tool(effect="read", idempotent=True, name="c3_tool")
    def a_tool(value: str) -> str:
        return value

    child = Agent("m", tools=[a_tool], name="c3_child")
    parent = Agent("m", tools=[child.as_sub(queue="c3-q")], name="c3_parent")

    assert parent.to_ir().to_json()["subflows"] == ["c3_child"]
    sc = parent.split_children()["c3_child"]
    assert sc.queue == "c3-q"
    assert sc.target.deployment().artifact_hash != parent.deployment().artifact_hash


def test_split_agent_local_run_uses_child_loop() -> None:
    calls: list[str] = []
    child_replies = [
        {"tool": "c3_child_tool", "input": "child-input"},
        {"output": "child done"},
    ]

    @tool(effect="read", idempotent=True, name="c3_child_tool")
    def child_tool(value: str) -> str:
        calls.append(value)
        return f"tool:{value}"

    def child_llm(_brain_name: str, _payload: dict[str, Any]) -> dict[str, Any]:
        return child_replies.pop(0)

    child = Agent("m", tools=[child_tool], name="c3_run_child", llm=child_llm)
    parent_replies = [
        {"sub": "c3_run_child", "input": "start-child"},
        {"output": "done"},
    ]

    parent = Agent(
        "m",
        tools=[child.as_sub()],
        name="c3_run_parent",
        llm=lambda _brain_name, _payload: parent_replies.pop(0),
    )

    result = parent.run("x")

    assert result["status"] == "done"
    assert result["output"] == "done"
    assert calls == ["child-input"]


def test_split_agent_attenuation_denies_direct_child_tool_call() -> None:
    @tool(effect="read", idempotent=True, name="c3_denied_tool")
    def child_tool(value: str) -> str:
        return value

    child = Agent("m", tools=[child_tool], name="c3_denied_child")
    parent = Agent(
        "m",
        tools=[child.as_sub()],
        name="c3_denied_parent",
        llm=lambda _brain_name, _payload: {"tool": "c3_denied_tool", "input": "x"},
    )

    result = parent.run("x")

    assert result["status"] == "denied"
    assert "not granted" in result["reason"]


def test_split_agent_and_inline_agent_emit_same_parent_app_json() -> None:
    @tool(effect="read", idempotent=True, name="c3_same_tool")
    def child_tool(value: str) -> str:
        return value

    child = Agent("m", tools=[child_tool], name="c3_same_child")

    inline_parent = Agent("m", tools=[child], name="c3_same_parent")
    split_parent = Agent("m", tools=[child.as_sub()], name="c3_same_parent")

    assert _normalized_json(split_parent) == _normalized_json(inline_parent)
    assert split_parent.deployment().artifact_hash == inline_parent.deployment().artifact_hash
