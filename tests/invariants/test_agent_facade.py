from __future__ import annotations

import asyncio
import warnings
from typing import Any

import pytest

from julep import Agent, Shape, ValidationError, deploy, get_reasoner, snapshot_from_tools, tool
from julep.capabilities import Budget, CapabilityManifest, ToolGrant
from julep.dsl import app
from julep.freeze import McpSnapshot, NativeToolSpec, freeze
from julep.ir import Op, toolref_key
from julep.kinds import Effect, Idempotency


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

    def llm(reasoner_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        seen.append((reasoner_name, payload))
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
    # The controller receives the reasoner *name* (the registry key a real llm
    # caller resolves), not the model string "m".
    assert [entry[0] for entry in seen] == ["agent_scripted", "agent_scripted"]
    assert seen[1][1]["input"] == ["hit:q"]


def test_deny_ungranted_hallucinated_tool() -> None:
    called = False

    def llm(_reasoner_name: str, _payload: dict[str, Any]) -> dict[str, Any]:
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
    def llm(_reasoner_name: str, _payload: dict[str, Any]) -> dict[str, Any]:
        return {"tool": "anything", "input": "x"}

    agent = Agent("m", tools=[], name="agent_deny_all", llm=llm)
    result = agent.run("hi")

    assert result["status"] == "denied"
    assert "not granted" in result["reason"]


def test_budget_flows_into_agent_config() -> None:
    def llm(_reasoner_name: str, _payload: dict[str, Any]) -> dict[str, Any]:
        return {"tool": "budget_tool", "input": "x"}

    @tool(effect="read", idempotent=True)
    def budget_tool(value: str) -> str:
        return value

    agent = Agent("m", tools=[budget_tool], name="agent_budget", llm=llm, budget_cost=1.0)
    result = agent.run("hi")

    assert result["status"] == "over_budget"
    assert result["cost"] == 0.0
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


def test_agent_deployment_manifest_carries_inline_tool_contracts() -> None:
    agent = Agent("m", tools=[a_read_tool], name="agent_manifest_contract")
    deployment = agent.deployment()

    tools_by_key = {toolref_key(frozen.ref): frozen for frozen in deployment.manifest.values()}

    assert a_read_tool.name in tools_by_key
    frozen = tools_by_key[a_read_tool.name]
    assert frozen.contract.effect == Effect.READ
    assert frozen.contract.idempotency == Idempotency.NATIVE


def test_freeze_binds_raw_app_inline_tools_to_manifest() -> None:
    contract = a_read_tool.contract
    snapshot = McpSnapshot(
        native={
            "t": NativeToolSpec(
                input_schema={"type": "string"},
                output_schema={"type": "string"},
                contract=contract,
            )
        }
    )

    frozen = freeze(app("c", tools=["t"]), snapshot)
    tools_by_key = {toolref_key(tool.ref): tool for tool in frozen.manifest.values()}

    assert "t" in tools_by_key
    assert tools_by_key["t"].contract == contract


def test_deployed_agent_contract_derivation_reads_manifest_contracts() -> None:
    from julep.agent_loop import manifest_contracts_for_agent

    agent = Agent("m", tools=[a_read_tool], name="agent_temporal_contract")
    deployment = agent.deployment()

    contracts = manifest_contracts_for_agent(deployment.manifest, {a_read_tool.name})

    assert contracts[a_read_tool.name] == {
        "effect": Effect.READ.value,
        "idempotency": Idempotency.NATIVE.value,
        "asserted": True,
        "assertionProvenance": "capability_manifest",
    }


def test_registered_reasoner_carries_tools() -> None:
    @tool(effect="read", idempotent=True)
    def web_search(query: str) -> str:
        return f"hit:{query}"

    Agent("m", tools=[web_search], name="agent_reasoner_tools")

    assert get_reasoner("agent_reasoner_tools").tools == ("web_search",)


def test_default_named_agents_with_distinct_tools_coexist() -> None:
    @tool(effect="read", idempotent=True)
    def search_tool(query: str) -> str:
        return f"search:{query}"

    @tool(effect="read", idempotent=True)
    def email_tool(query: str) -> str:
        return f"email:{query}"

    search_agent = Agent("m", tools=[search_tool])
    email_agent = Agent("m", tools=[email_tool])

    assert search_agent._name != email_agent._name
    assert search_agent.deployment().flow.controller != email_agent.deployment().flow.controller
    assert search_agent.deployment().artifact_hash != email_agent.deployment().artifact_hash


def test_identical_default_named_agents_share_name_reasoner_and_artifact_hash() -> None:
    @tool(effect="read", idempotent=True)
    def shared_tool(query: str) -> str:
        return f"shared:{query}"

    first = Agent("m", tools=[shared_tool])
    second = Agent("m", tools=[shared_tool])

    assert first._name == second._name
    assert first.deployment().artifact_hash == second.deployment().artifact_hash
    assert get_reasoner(first._name).tools == ("shared_tool",)


def test_default_agent_name_is_deterministic_for_same_config() -> None:
    @tool(effect="read", idempotent=True)
    def deterministic_tool(query: str) -> str:
        return f"deterministic:{query}"

    assert Agent("m", tools=[deterministic_tool])._name == Agent("m", tools=[deterministic_tool])._name


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
        llm=lambda _reasoner_name, _payload: {"output": "ok"},
        budget_cost=1.0,
    )

    deployment = agent.deployment()
    assert deployment.surface_shape == Shape.AGENT
    assert isinstance(deployment.artifact_hash, str)
    assert deployment.artifact_hash

    budget = Budget(cost=1.0)
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
        task_queue: str = "julep",
        policy: Any = None,
        principal: Any = None,
    ) -> dict[str, Any]:
        calls.append(
            {
                "client": client,
                "session_id": session_id,
                "input": input,
                "task_queue": task_queue,
                "policy": policy,
                "principal": principal,
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
            principal={"storeId": 413, "tokenRef": "cred_abc"},
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
            "principal": {"storeId": 413, "tokenRef": "cred_abc"},
        }
    ]
