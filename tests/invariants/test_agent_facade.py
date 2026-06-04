from __future__ import annotations

import asyncio
import warnings
from typing import Any

import pytest

from composable_agents import Agent, Shape, ValidationError, deploy, get_brain, snapshot_from_tools, tool
from composable_agents.capabilities import Budget, CapabilityManifest, ToolGrant
from composable_agents.dsl import app
from composable_agents.ir import Op
from composable_agents.kinds import Effect, Idempotency


@tool(effect="read", idempotent=True)
def a_read_tool(value: str) -> str:
    return f"read:{value}"


def test_keyless_stub_run_warns_once() -> None:
    agent = Agent("m", tools=[a_read_tool], name="agent_stub")

    with pytest.warns(RuntimeWarning, match="llm=None"):
        first = agent.run("hi")
    with warnings.catch_warnings(record=True) as second_warnings:
        warnings.simplefilter("always")
        second = agent.run("hi again")

    assert first["status"] == "done"
    assert "no model configured" in first["output"]["note"]
    assert first["output"]["input"] == "hi"
    assert second["status"] == "done"
    assert len(second_warnings) == 0


def test_scripted_think_call_finish() -> None:
    replies = [
        {"tool": "web_search", "input": "q"},
        {"output": "final"},
    ]
    seen: list[tuple[str, dict[str, Any]]] = []
    tool_calls: list[str] = []

    def llm(brain_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        seen.append((brain_name, payload))
        return replies.pop(0)

    @tool(effect="read", idempotent=True)
    def web_search(q: str) -> list[str]:
        tool_calls.append(q)
        return [f"hit:{q}"]

    agent = Agent("m", tools=[web_search], name="agent_scripted", llm=llm)
    result = agent.run("find")

    assert result["status"] == "done"
    assert result["output"] == "final"
    assert result["trace"] == [{"decision": "call", "ref": "web_search", "cost": 1.0}]
    assert tool_calls == ["q"]
    assert [entry[0] for entry in seen] == ["m", "m"]
    assert seen[1][1]["input"] == ["hit:q"]


def test_deny_ungranted_hallucinated_tool() -> None:
    called = False

    def llm(_brain_name: str, _payload: dict[str, Any]) -> dict[str, Any]:
        return {"tool": "net/evil", "input": "x"}

    @tool(effect="read", idempotent=True)
    def safe_tool(value: str) -> str:
        nonlocal called
        called = True
        return value

    agent = Agent("m", tools=[safe_tool], name="agent_deny_ungranted", llm=llm)
    result = agent.run("hi")

    assert result["status"] == "denied"
    assert "not granted" in result["reason"]
    assert called is False


def test_deny_all_when_tools_empty() -> None:
    def llm(_brain_name: str, _payload: dict[str, Any]) -> dict[str, Any]:
        return {"tool": "anything", "input": "x"}

    agent = Agent("m", tools=[], name="agent_deny_all", llm=llm)
    result = agent.run("hi")

    assert result["status"] == "denied"
    assert "not granted" in result["reason"]


def test_budget_flows_into_agent_config() -> None:
    def llm(_brain_name: str, _payload: dict[str, Any]) -> dict[str, Any]:
        return {"tool": "budget_tool", "input": "x"}

    @tool(effect="read", idempotent=True)
    def budget_tool(value: str) -> str:
        return value

    agent = Agent("m", tools=[budget_tool], name="agent_budget", llm=llm, budget_usd=1.0)
    result = agent.run("hi")

    assert result["status"] == "over_budget"
    assert result["spentUsd"] == 0.0
    assert result["trace"] == []


def test_deployed_allow_list_is_encoded() -> None:
    @tool(effect="read", idempotent=True)
    def web_search(query: str) -> str:
        return f"hit:{query}"

    agent = Agent("m", tools=[web_search], name="agent_allow_list")
    deployment = agent.deployment()

    assert deployment.flow.op == Op.APP
    assert deployment.flow.tools == ["web_search"]

    deny_all = Agent("m", tools=[], name="agent_allow_list_empty")
    assert deny_all.deployment().flow.op == Op.APP
    assert deny_all.deployment().flow.tools == []


def test_registered_brain_carries_tools() -> None:
    @tool(effect="read", idempotent=True)
    def web_search(query: str) -> str:
        return f"hit:{query}"

    Agent("m", tools=[web_search], name="agent_brain_tools")

    assert get_brain("agent_brain_tools").tools == ("web_search",)


def test_dangerous_tool_is_rejected_at_construction() -> None:
    @tool(effect="dangerous")
    def danger(x: str) -> str:
        return x

    with pytest.raises(ValidationError, match="CAP_APP_APPROVAL_TOOL"):
        Agent("m", tools=[danger], name="agent_danger")


def test_deploy_artifact_and_shape_are_deterministic() -> None:
    agent = Agent(
        "m",
        tools=[a_read_tool],
        name="agent_artifact",
        llm=lambda _brain_name, _payload: {"output": "ok"},
        budget_usd=1.0,
    )

    deployment = agent.deployment()
    assert deployment.surface_shape == Shape.AGENT
    assert isinstance(deployment.artifact_hash, str)
    assert deployment.artifact_hash

    budget = Budget(usd=1.0)
    capabilities = CapabilityManifest(
        tools={
            a_read_tool.name: ToolGrant(
                name=a_read_tool.name,
                effect=Effect.READ,
                idempotency=Idempotency.NATIVE,
            )
        },
        budget=budget,
        _has_tools=True,
    )
    rebuilt = deploy(
        app("agent_artifact", tools=[a_read_tool.name], budget=budget, max_rounds=24),
        snapshot_from_tools([a_read_tool]),
        capabilities=capabilities,
    )
    assert rebuilt.artifact_hash == deployment.artifact_hash


def test_deploy_forwards_to_deployment_run(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("temporalio")
    agent = Agent("m", tools=[], name="agent_forward", llm=lambda _b, _p: {"output": "ok"})
    calls: list[dict[str, Any]] = []

    async def fake_run(
        client: Any,
        *,
        session_id: str,
        input: Any = None,
        task_queue: str = "composable-agents",
        policy: Any = None,
    ) -> dict[str, Any]:
        calls.append(
            {
                "client": client,
                "session_id": session_id,
                "input": input,
                "task_queue": task_queue,
                "policy": policy,
            }
        )
        return {"status": "done"}

    monkeypatch.setattr(agent.deployment(), "run", fake_run)
    client = object()
    result = asyncio.run(
        agent.deploy(
            client,
            session_id="run-1",
            input="payload",
            task_queue="queue",
            policy={"p": True},
        )
    )

    assert result == {"status": "done"}
    assert calls == [
        {
            "client": client,
            "session_id": "run-1",
            "input": "payload",
            "task_queue": "queue",
            "policy": {"p": True},
        }
    ]
