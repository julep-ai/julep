from __future__ import annotations

from typing import Any

import pytest

from composable_agents import Agent, ValidationError, call, ident, native, tool
from composable_agents.derived import race
from composable_agents.flow import as_flow, seq
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
    named = as_flow(ident()).named("tf6.svc.v1")

    parent = Agent("m", tools=[named], name="tf6_flowcap")

    assert parent.to_ir().to_json()["subflows"] == ["tf6.svc.v1"]
    assert get_flow("tf6.svc.v1").node.to_json() == named.to_ir().to_json()


def test_plain_flow_sub_threads_result() -> None:
    ref = "tf6.ident.v1"
    named = as_flow(ident()).named(ref)
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

    named = as_flow(call(native("tf6_dup_native"))).named("tf6_dup")

    with pytest.raises(ValidationError, match="CAP_APP_TOOL_COLLISION"):
        Agent("m", tools=[duplicate, named], name="tf6_dup_agent")


def test_unnamed_flow_cap_raises() -> None:
    with pytest.raises(ValidationError, match=".named"):
        Agent("m", tools=[as_flow(call(native("tf6_unnamed_native")))], name="tf6_unnamed")


def test_app_json_subflows_are_omitted_for_tools_and_present_for_flow_caps() -> None:
    tool_only = Agent("m", tools=[read_tool], name="tf6_json_toolonly")
    ref = "tf6.json.v1"
    flow_cap = as_flow(ident()).named(ref)
    with_flow = Agent("m", tools=[flow_cap], name="tf6_json_flowcap")

    assert "subflows" not in tool_only.to_ir().to_json()
    assert with_flow.to_ir().to_json()["subflows"] == [ref]


def test_plain_flow_cap_with_ungranted_tool_is_rejected_cleanly() -> None:
    @tool(effect="read", idempotent=True, name="c2_secret")
    def secret(value: str) -> str:
        return value

    fc = as_flow(secret).named("c2.svc")

    with pytest.raises(ValidationError, match="CAP_APP_FLOW_UNGRANTED_TOOL"):
        Agent("m", tools=[fc], name="c2_bad")


def test_plain_flow_cap_with_granted_tool_runs_through_parent_grant() -> None:
    calls: list[str] = []

    @tool(effect="read", idempotent=True, name="c2_t")
    def t(value: str) -> str:
        calls.append(value)
        return f"t:{value}"

    fc = as_flow(t).named("c2.ok")
    replies = [
        {"sub": "c2.ok", "input": "hi"},
        {"output": "done"},
    ]
    parent = Agent(
        "m",
        tools=[t, fc],
        name="c2_good",
        llm=lambda _brain_name, _payload: replies.pop(0),
    )

    result = parent.run("x")

    assert result["status"] == "done"
    assert calls == ["hi"]


def test_unsafe_plain_flow_cap_rejected_by_race_admission_strict() -> None:
    @tool(effect="write", idempotent=False, name="tf6_write_race_strict")
    def w(value: str) -> str:
        return f"w:{value}"

    cap = as_flow(race(w.to_ir(), w.to_ir())).named("tf6.bad.race.strict")
    parent = Agent("m", tools=[w, cap], name="tf6_bad_race_parent_strict")

    diagnostics = parent.check()
    assert any(d.code == "RACE_UNSAFE" for d in diagnostics)

    with pytest.raises(ValidationError, match="RACE_UNSAFE"):
        parent.run("x")

    with pytest.raises(ValidationError, match="RACE_UNSAFE"):
        parent.deployment()


def test_unsafe_plain_flow_cap_surfaces_prod_gap_in_dev() -> None:
    @tool(effect="write", idempotent=False, name="tf6_write_race_dev")
    def w(value: str) -> str:
        return f"w:{value}"

    cap = as_flow(race(w.to_ir(), w.to_ir())).named("tf6.bad.race.dev")
    parent = Agent(
        "m",
        tools=[w, cap],
        name="tf6_bad_race_parent_dev",
        mode="dev",
    )

    diagnostics = parent.check()
    deployment = parent.deployment()

    assert any(d.code == "RACE_UNSAFE" for d in diagnostics)
    assert any(d.code == "RACE_UNSAFE" for d in deployment.prod_gap)


def test_safe_plain_flow_cap_still_runs_with_compiled_manifest() -> None:
    calls: list[tuple[str, str]] = []

    @tool(effect="read", idempotent=True, name="tf6_read_seq_first")
    def first(value: str) -> str:
        calls.append(("first", value))
        return f"first:{value}"

    @tool(effect="read", idempotent=True, name="tf6_read_seq_second")
    def second(value: str) -> str:
        calls.append(("second", value))
        return f"second:{value}"

    cap = seq(first, second).named("tf6.good.seq")
    replies = [
        {"sub": "tf6.good.seq", "input": "start"},
        {"output": "done"},
    ]
    seen: list[dict[str, Any]] = []

    def llm(_brain_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        seen.append(payload)
        return replies.pop(0)

    parent = Agent(
        "m",
        tools=[first, second, cap],
        name="tf6_good_seq_parent",
        llm=llm,
    )

    assert parent.check() == []
    result = parent.run("x")

    assert result["status"] == "done"
    assert calls == [("first", "start"), ("second", "first:start")]
    assert seen[1]["input"] == "second:first:start"


def test_sub_caps_expose_deployments_and_deploy_fails_loud() -> None:
    """Bounded seam guard: sub-cap deployments are discoverable; deploy() fails loud."""
    import asyncio

    @tool(effect="read", idempotent=True, name="tf_seam_read")
    def r(value: str) -> str:
        return value

    plain = as_flow(r).named("seam.plain.v1")          # parent's own granted tool
    sub_agent = Agent("m", tools=[r], name="seam.subagent.v1")
    parent = Agent("m", tools=[r, plain, sub_agent], name="seam.parent")

    # The compiled child deployments are exposed (not stuck in a private cache).
    subs = parent.sub_deployments()
    assert set(subs) == {"seam.plain.v1", "seam.subagent.v1"}
    assert all(d.artifact_hash for d in subs.values())

    # Temporal deploy fails loud (no silent divergence); the guard precedes the
    # lazy temporalio import, so this runs without temporalio installed.
    with pytest.raises(NotImplementedError, match="sub_deployments"):
        asyncio.run(parent.deploy(object(), session_id="x"))
