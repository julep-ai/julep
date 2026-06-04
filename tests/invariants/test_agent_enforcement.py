from __future__ import annotations

from composable_agents import Budget, Effect, Idempotency, ToolContract
from composable_agents.agent_loop import (
    AgentConfig,
    AgentState,
    authorize_subflow,
    authorize_call,
    charge_tool_call,
    precheck_controller,
    retry_max_attempts_for_contract,
)


def test_empty_grants_deny_call_but_absent_grants_allow() -> None:
    denied = authorize_call(
        "srv/search",
        unconstrained=False,
        granted_set=set(),
        contracts={},
    )
    allowed = authorize_call(
        "srv/search",
        unconstrained=True,
        granted_set=set(),
        contracts={},
    )

    assert denied is not None
    assert denied.reason == "tool 'srv/search' is not granted"
    assert allowed is None


def test_approval_required_tools_are_denied_even_when_granted() -> None:
    dangerous = authorize_call(
        "srv/delete",
        unconstrained=False,
        granted_set={"srv/delete"},
        contracts={"srv/delete": {"effect": "dangerous", "idempotency": "none"}},
    )
    approval_grant = authorize_call(
        "srv/archive",
        unconstrained=False,
        granted_set={"srv/archive"},
        contracts={"srv/archive": {"effect": "read", "idempotency": "native", "approval": True}},
    )

    assert dangerous is not None
    assert dangerous.reason == "approval-required tool 'srv/delete'; agent must ESCALATE"
    assert approval_grant is not None
    assert approval_grant.reason == "approval-required tool 'srv/archive'; agent must ESCALATE"


def test_contract_retry_attempts_use_cautious_or_liberal_policy() -> None:
    write_none = ToolContract(Effect.WRITE, Idempotency.NONE)
    read_native = ToolContract(Effect.READ, Idempotency.NATIVE)

    assert retry_max_attempts_for_contract(
        write_none,
        idempotent_max_attempts=9,
        write_max_attempts=2,
    ) == 2
    assert retry_max_attempts_for_contract(
        read_native,
        idempotent_max_attempts=9,
        write_max_attempts=2,
    ) == 9


def test_controller_budget_precheck_stops_without_spend() -> None:
    state = AgentState(spent_usd=0)
    cfg = AgentConfig(think_cost=2, budget=Budget(usd=1))

    result = precheck_controller(state, cfg)

    assert result is not None
    assert result["status"] == "over_budget"
    assert result["spentUsd"] == 0
    assert state.spent_usd == 0
    assert state.trace == []


def test_agent_max_calls_counter_denies_after_limit_and_survives_json_round_trip() -> None:
    state = AgentState()
    contracts = {
        "srv/search": {"effect": "read", "idempotency": "native", "maxCalls": 1}
    }

    assert charge_tool_call(state, "srv/search", contracts) is None
    carried = AgentState.from_json(state.to_json())
    denial = charge_tool_call(carried, "srv/search", contracts)

    assert carried.call_counts == {"srv/search": 1}
    assert denial is not None
    assert denial.reason == "tool 'srv/search' exceeded maxCalls=1"


def test_agent_max_calls_absent_limit_is_unconstrained() -> None:
    state = AgentState()

    assert charge_tool_call(state, "srv/search", {}) is None
    assert charge_tool_call(state, "srv/search", {}) is None
    assert state.call_counts == {}


def test_subflow_grants_preserve_none_vs_empty_list() -> None:
    assert authorize_subflow("child", granted_subflows=None) is None
    assert authorize_subflow("child", granted_subflows={"child"}) is None

    empty = authorize_subflow("child", granted_subflows=set())
    other = authorize_subflow("child", granted_subflows={"other"})

    assert empty is not None
    assert empty.reason == "subflow 'child' is not granted"
    assert other is not None
    assert other.reason == "subflow 'child' is not granted"
