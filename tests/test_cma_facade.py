"""Agent facade tests for Claude Managed Agents execution."""

from __future__ import annotations

from typing import Any

from composable_agents import Agent, tool
from composable_agents.execution.cma import CMAAgentEnv as RealCMAAgentEnv
from composable_agents.execution.cma import CMAEvent
from cma_fakes import FakeCMAClient, FakeCMASession


def test_agent_run_on_cma_happy_path_calls_tool_and_returns_result() -> None:
    calls: list[str] = []

    @tool(effect="read", idempotent=True)
    def cma_facade_search(query: str) -> dict[str, str]:
        """Search the local fixture."""
        calls.append(query)
        return {"hit": query}

    session = FakeCMASession([
        CMAEvent("custom_tool_use", tool="cma_facade_search", input="hi", call_id="call-1"),
        CMAEvent("terminal", output={"answer": "done"}),
    ])
    client = FakeCMAClient(session)
    agent = Agent(
        "claude-sonnet-4-6",
        tools=[cma_facade_search],
        name="cma_facade_happy",
    )

    result = agent.run_on_cma("hi", client=client, environment={"kind": "test"})

    assert result.status == "done"
    assert result.output == {"answer": "done"}
    assert result["status"] == "done"
    assert calls == ["hi"]
    assert session.results == [("call-1", {"hit": "hi"})]
    assert client.environment == {"kind": "test"}


def test_agent_run_on_cma_honors_grants_for_ungranted_tool() -> None:
    @tool(effect="read", idempotent=True)
    def cma_facade_allowed(query: str) -> str:
        raise AssertionError("granted tool should not run")

    session = FakeCMASession([
        CMAEvent("custom_tool_use", tool="cma_facade_bogus", input="x", call_id="call-1"),
    ])
    client = FakeCMAClient(session)
    agent = Agent(
        "claude-sonnet-4-6",
        tools=[cma_facade_allowed],
        name="cma_facade_denied",
    )

    result = agent.run_on_cma("hi", client=client)

    assert result.status == "denied"
    assert "cma_facade_bogus" in (result.reason or "")
    assert session.results == []
    assert session.errors == [("call-1", result["reason"])]


def test_agent_run_on_cma_projects_custom_tool_manifest_in_tool_order() -> None:
    @tool(effect="read", idempotent=True, name="cma_facade_first")
    def first(query: str) -> str:
        """First tool."""
        return query

    @tool(effect="read", idempotent=True, name="cma_facade_second")
    def second(query: str) -> str:
        return query

    session = FakeCMASession([
        CMAEvent("terminal", output={"ok": True}),
    ])
    client = FakeCMAClient(session)
    agent = Agent(
        "claude-sonnet-4-6",
        tools=[first, second],
        name="cma_facade_manifest",
    )

    result = agent.run_on_cma("hi", client=client)

    assert result.status == "done"
    assert client.agent is not None
    tools = client.agent["tools"]
    assert [item["name"] for item in tools] == ["cma_facade_first", "cma_facade_second"]
    assert [item["type"] for item in tools] == ["custom", "custom"]
    assert all(item["name"] != "agent_toolset_20260401" for item in tools)
    assert tools[0]["description"] == "First tool."
    # CMA requires an object input_schema; a single scalar-arg tool is projected
    # as an object that names the parameter (here "query": {"type": "string"}).
    assert tools[0]["input_schema"] == {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
        "additionalProperties": False,
    }
    assert first.input_schema == {"type": "string"}


def test_agent_run_on_cma_passes_same_grants_and_contract_keys(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    class RecordingCMAAgentEnv(RealCMAAgentEnv):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            captured["granted"] = kwargs["granted"]
            captured["contracts"] = kwargs["contracts"]
            super().__init__(*args, **kwargs)

    @tool(effect="read", idempotent=True)
    def cma_facade_contract_tool(query: str) -> str:
        return query

    import composable_agents.agent as agent_module

    monkeypatch.setattr(agent_module, "CMAAgentEnv", RecordingCMAAgentEnv)
    session = FakeCMASession([
        CMAEvent("terminal", output={"ok": True}),
    ])
    agent = Agent(
        "claude-sonnet-4-6",
        tools=[cma_facade_contract_tool],
        name="cma_facade_contracts",
    )

    result = agent.run_on_cma("hi", client=FakeCMAClient(session))

    assert result.status == "done"
    assert captured["granted"] == agent._granted
    assert captured["contracts"].keys() == agent._contracts.keys()
