from __future__ import annotations

from typing import Any

import pytest

from composable_agents import Agent, ValidationError, call, ident, native, tool
from composable_agents.flow import flow
from composable_agents.flow_registry import get_flow


@tool(effect="read", idempotent=True, name="tf6_read_toolonly")
def read_tool(value: str) -> str:
    return f"read:{value}"


def test_tool_only_agent_has_no_subflows_key() -> None:
    agent = Agent("m", tools=[read_tool], name="tf6_toolonly")
    app_json = agent.to_ir().to_json()

    assert "subflows" not in app_json
    assert app_json["tools"] == ["tf6_read_toolonly"]


def test_flow_cap_becomes_app_subflow_and_is_registered() -> None:
    named = flow(call(native("tf6_svc"))).named("tf6.svc.v1")

    parent = Agent("m", tools=[named], name="tf6_flowcap")

    assert parent.to_ir().to_json()["subflows"] == ["tf6.svc.v1"]
    assert get_flow("tf6.svc.v1").node.to_json() == named.to_ir().to_json()


def test_plain_flow_sub_threads_result() -> None:
    ref = "tf6.ident.v1"
    named = flow(ident()).named(ref)
    replies = [
        {"sub": ref, "input": "hello"},
        {"output": "done"},
    ]
    seen: list[dict[str, Any]] = []

    def llm(_brain_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        seen.append(payload)
        return replies.pop(0)

    parent = Agent("m", tools=[named], name="tf6_plain_flow_parent", llm=llm)
    result = parent.run("start")

    assert result["status"] == "done"
    assert result["output"] == "done"
    assert result["trace"][0]["decision"] == "sub"
    assert result["trace"][0]["ref"] == ref
    assert seen[1]["input"] == "hello"


def test_sub_agent_threads_result_without_granting_parent_sub_agent_tools() -> None:
    secret_calls: list[str] = []
    sub_replies = [
        {"tool": "tf6_secret", "input": "open"},
        {"output": "sub done"},
    ]

    @tool(effect="read", idempotent=True, name="tf6_secret")
    def secret(value: str) -> str:
        secret_calls.append(value)
        return f"secret:{value}"

    def sub_llm(_brain_name: str, _payload: dict[str, Any]) -> dict[str, Any]:
        return sub_replies.pop(0)

    sub = Agent("m", tools=[secret], name="tf6_sub_agent", llm=sub_llm)
    parent_replies = [
        {"sub": sub._name, "input": "start-sub"},
        {"output": "parent done"},
    ]
    parent_seen: list[dict[str, Any]] = []

    def parent_llm(_brain_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        parent_seen.append(payload)
        return parent_replies.pop(0)

    parent = Agent("m", tools=[sub], name="tf6_parent_agent", llm=parent_llm)
    result = parent.run("start")

    assert result["status"] == "done"
    assert result["trace"][0]["decision"] == "sub"
    assert result["trace"][0]["ref"] == "tf6_sub_agent"
    assert parent_seen[1]["input"]["status"] == "done"
    assert parent_seen[1]["input"]["output"] == "sub done"
    assert secret_calls == ["open"]

    denied_parent = Agent(
        "m",
        tools=[sub],
        name="tf6_parent_denied_secret",
        llm=lambda _brain_name, _payload: {"tool": "tf6_secret", "input": "x"},
    )
    denied = denied_parent.run("start")

    assert denied["status"] == "denied"
    assert "not granted" in denied["reason"]

    direct_replies = [
        {"tool": "tf6_secret", "input": "direct"},
        {"output": "direct done"},
    ]
    direct_sub = Agent(
        "m",
        tools=[secret],
        name="tf6_sub_agent_direct",
        llm=lambda _brain_name, _payload: direct_replies.pop(0),
    )
    direct = direct_sub.run("start")

    assert direct["status"] == "done"
    assert direct["output"] == "direct done"
    assert secret_calls[-1] == "direct"


def test_tool_subflow_name_collision_is_rejected_at_agent_construction() -> None:
    @tool(effect="read", idempotent=True, name="tf6_dup")
    def duplicate(value: str) -> str:
        return value

    named = flow(call(native("tf6_dup_native"))).named("tf6_dup")

    with pytest.raises(ValidationError, match="CAP_APP_TOOL_COLLISION"):
        Agent("m", tools=[duplicate, named], name="tf6_dup_agent")


def test_unnamed_flow_cap_raises() -> None:
    with pytest.raises(ValidationError, match=".named"):
        Agent("m", tools=[flow(call(native("tf6_unnamed_native")))], name="tf6_unnamed")


def test_app_json_subflows_are_omitted_for_tools_and_present_for_flow_caps() -> None:
    tool_only = Agent("m", tools=[read_tool], name="tf6_json_toolonly")
    ref = "tf6.json.v1"
    flow_cap = flow(ident()).named(ref)
    with_flow = Agent("m", tools=[flow_cap], name="tf6_json_flowcap")

    assert "subflows" not in tool_only.to_ir().to_json()
    assert with_flow.to_ir().to_json()["subflows"] == [ref]
