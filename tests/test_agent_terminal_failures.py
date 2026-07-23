from __future__ import annotations

import asyncio

import pytest

from julep import AgentTerminalError as PublicAgentTerminalError
from julep import app, seq, think
from julep.errors import AgentTerminalError, raise_for_agent_terminal
from julep.execution.interpreter import InMemoryEnv, interpret
from julep.projection import EventType, InMemoryProjection, ProjectionEmitter


def test_agent_terminal_error_is_public() -> None:
    assert PublicAgentTerminalError is AgentTerminalError


@pytest.mark.parametrize(
    "status",
    [
        "controller_error",
        "max_rounds",
        "over_budget",
        "denied",
        "output_validation_failed",
    ],
)
def test_failed_agent_terminal_statuses_raise(status: str) -> None:
    result = {
        "status": status,
        "reason": "controller could not settle",
        "rounds": 2,
        "cost": 4.0,
        "trace": [],
    }

    with pytest.raises(AgentTerminalError) as caught:
        raise_for_agent_terminal(result)

    assert caught.value.status == status
    assert caught.value.result == result
    assert status in str(caught.value)
    assert "controller could not settle" not in str(caught.value)


@pytest.mark.parametrize("status", ["done", "escalated"])
def test_successful_agent_terminal_statuses_pass_through(status: str) -> None:
    result = {"status": status, "output": {"ok": True}}
    assert raise_for_agent_terminal(result) is result


def test_non_agent_results_pass_through() -> None:
    result = {"value": 3}
    assert raise_for_agent_terminal(result) is result


@pytest.mark.parametrize("status", sorted([
    "controller_error",
    "max_rounds",
    "over_budget",
    "denied",
    "output_validation_failed",
]))
def test_app_failure_stops_the_flow_and_emits_failed(status: str) -> None:
    downstream_calls = 0

    def downstream(value: object) -> object:
        nonlocal downstream_calls
        downstream_calls += 1
        return value

    store = InMemoryProjection()
    env = InMemoryEnv(
        {},
        ProjectionEmitter(store),
        agents={"controller": lambda _value: {"status": status, "reason": "bad"}},
        reasoners={"downstream": downstream},
    )

    with pytest.raises(AgentTerminalError) as caught:
        asyncio.run(interpret(seq(app("controller"), think("downstream")), {}, env))

    assert caught.value.status == status
    assert downstream_calls == 0
    assert [event.type for event in store.events()].count(EventType.FAILED) == 2
    assert all(event.type is not EventType.DID for event in store.events())
