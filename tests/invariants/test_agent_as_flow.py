from __future__ import annotations

import pytest

from composable_agents import Agent, ValidationError, call, native, tool
from composable_agents.typed import Flow, as_flow, seq
from composable_agents.ir import Op


@tool(effect="read", idempotent=True)
def read_tool(value: str) -> str:
    return f"read:{value}"


def test_agent_is_a_flow_to_ir_is_app_node() -> None:
    agent = Agent("m", tools=[read_tool], name="agent_as_flow_1")

    node = agent.to_ir()

    assert node.op is Op.APP
    assert node is agent._flow


def test_agent_composes_in_seq() -> None:
    agent = Agent("m", tools=[read_tool], name="agent_as_flow_seq")

    composed = seq(as_flow(call(native("fetch"))), agent)
    node = composed.to_ir()

    assert isinstance(composed, Flow)
    assert node.op is Op.SEQ
    assert node.right.op is Op.APP


def test_agent_rshift_composes_as_left_side() -> None:
    agent = Agent("m", tools=[read_tool], name="agent_as_flow_rshift")
    next_leaf = call(native("next"))

    node = (agent >> as_flow(next_leaf)).to_ir()

    assert node.op is Op.SEQ
    assert node.left.op is Op.APP
    assert node.right is next_leaf


def test_agent_deployment_is_lazy_and_cached() -> None:
    agent = Agent("m", tools=[read_tool], name="agent_as_flow_lazy")

    assert agent._deployment_cache is None

    deployment = agent.deployment()

    assert agent._deployment_cache is not None
    assert agent.deployment() is deployment


def test_agent_eager_rejects_dangerous_tool_in_strict_mode() -> None:
    @tool(effect="dangerous")
    def danger(value: str) -> str:
        return value

    with pytest.raises(ValidationError, match="CAP_APP_APPROVAL_TOOL"):
        Agent("m", tools=[danger], name="agent_as_flow_danger_strict")


def test_agent_eager_rejects_duplicate_tool_names() -> None:
    @tool(name="dup")
    def first(value: str) -> str:
        return value

    @tool(name="dup")
    def second(value: str) -> str:
        return value

    with pytest.raises(ValidationError, match="CAP_APP_TOOL_COLLISION"):
        Agent("m", tools=[first, second], name="agent_as_flow_dup")


def test_agent_dev_dangerous_tool_constructs_and_exposes_prod_gap() -> None:
    @tool(effect="dangerous")
    def danger(value: str) -> str:
        return value

    agent = Agent("m", tools=[danger], name="agent_as_flow_danger_dev", mode="dev")

    assert agent.deployment().prod_gap
