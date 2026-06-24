"""Long-lived session interpreter tests (recv/emit + LOOP)."""

from __future__ import annotations

from typing import Any

import pytest

from composable_agents import (
    arr,
    drive_session,
    emit,
    register_pure,
    recv,
    scan,
    seq,
)
from composable_agents.errors import ComposableAgentsError
from composable_agents.execution.interpreter import InMemoryEnv, SessionClosed, interpret
from composable_agents.ir import Node
from composable_agents.projection import EventType, InMemoryProjection, ProjectionEmitter
from conftest import run


def _turn_msg(value: dict[str, Any]) -> Any:
    return value["msg"]


def _turn_sum(value: dict[str, Any]) -> int:
    return int(value["carrier"]) + int(value["msg"])


def _append_with_reply(value: dict[str, Any]) -> tuple[list[Any], str]:
    carrier = value["carrier"]
    assert isinstance(carrier, list)
    msg = value["msg"]
    return ([*carrier, msg], f"reply:{msg}")


register_pure("tests.session.turn_msg", _turn_msg)
register_pure("tests.session.turn_sum", _turn_sum)
register_pure("tests.session.append_with_reply", _append_with_reply)


def _env(flow: Node, **kw: Any) -> tuple[Node, InMemoryEnv]:
    store = InMemoryProjection()
    env = InMemoryEnv({}, ProjectionEmitter(store), **kw)
    return flow, env


class RecordingSessionEnv(InMemoryEnv):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.recv_calls = 0

    async def recv(self, channel: str, cid: str, timeout_s: int | None) -> Any:
        self.recv_calls += 1
        return await super().recv(channel, cid, timeout_s)

    async def run_call(self, node: Node, value: Any, cid: str) -> Any:
        raise AssertionError("recv/emit must not route through run_call")


def test_recv_emit_nonretryable() -> None:
    flow = seq(recv("in", timeout_s=3), arr("tests.session.turn_msg"), emit("out"))
    env = RecordingSessionEnv(
        {},
        ProjectionEmitter(InMemoryProjection()),
        inbound={"in": ["hello"]},
    )

    out = run(interpret(flow, "ignored", env))

    assert out.value == "hello"
    assert env.recv_calls == 1
    assert env.emitted("out") == ["hello"]


def test_recv_exhausted_raises_session_closed() -> None:
    flow, env = _env(recv("in"), inbound={"in": []})

    with pytest.raises(SessionClosed):
        run(interpret(flow, None, env))


def test_loop_echo_session_e2e() -> None:
    session = scan(seq(recv("in"), arr("tests.session.turn_msg"), emit("out")), init=None)
    flow, env = _env(session.body, inbound={"in": ["a", "b", "c"]})

    run(interpret(flow, session.init, env))

    assert env.emitted("out") == ["a", "b", "c"]


def test_clean_session_shutdown_records_no_failed_event() -> None:
    store = InMemoryProjection()
    session = scan(seq(recv("in"), arr("tests.session.turn_msg"), emit("out")), init=None)
    env = InMemoryEnv({}, ProjectionEmitter(store), inbound={"in": ["a", "b"]})

    run(interpret(session.body, session.init, env))

    failed = [e for e in store.events() if e.type == EventType.FAILED]
    assert failed == []


def test_recv_emit_do_not_consume_tool_call_quota() -> None:
    flow = seq(recv("in"), arr("tests.session.turn_msg"), emit("out"))
    env = InMemoryEnv(
        {},
        ProjectionEmitter(InMemoryProjection()),
        inbound={"in": ["hi"]},
    )

    run(interpret(flow, "ignored", env))

    # Reserved channel ops short-circuit before charge_call: no call accounting.
    assert dict(env.call_counts) == {}


def test_loop_accumulator_session_e2e() -> None:
    session = scan(seq(recv("in"), arr("tests.session.turn_sum"), emit("out")), init=0)

    for _ in range(2):
        flow, env = _env(session.body, inbound={"in": [1, 2, 3]})

        out = run(interpret(flow, session.init, env))

        assert env.emitted("out") == [1, 3, 6]
        assert out.value == 6


def test_loop_constant_emit_does_not_replace_carrier() -> None:
    session = scan(
        seq(recv("in"), arr("tests.session.turn_sum"), emit("out", value="ack")),
        init=0,
    )
    flow, env = _env(session.body, inbound={"in": [1, 2, 3]})

    out = run(interpret(flow, session.init, env))

    assert out.value == 6
    assert env.emitted("out") == ["ack", "ack", "ack"]


def test_scan_split_threads_carrier_and_emits_distinct_output() -> None:
    session = scan(seq(recv("in"), arr("tests.session.append_with_reply")), init=[])
    flow, env = _env(session.body, inbound={"in": ["a", "b", "c"]})

    out = run(interpret(flow, session.init, env))

    assert out.value == ["a", "b", "c"]
    assert env.emitted("out") == ["reply:a", "reply:b", "reply:c"]


def test_drive_session_raises_when_message_bound_exceeded() -> None:
    session = scan(seq(recv("in"), arr("tests.session.turn_sum"), emit("out")), init=0)
    consumed = 0

    def inputs() -> Any:
        nonlocal consumed
        for value in [1, 2, 3, 4]:
            consumed += 1
            yield value

    with pytest.raises(
        ComposableAgentsError,
        match="session consumed more than 2 messages",
    ):
        run(drive_session(session, inputs=inputs(), max_turns=2))

    assert consumed == 3


def test_drive_session_uses_caller_supplied_env() -> None:
    session = scan(seq(recv("in"), arr("tests.session.turn_msg"), emit("out")), init=None)
    env = InMemoryEnv(
        {},
        ProjectionEmitter(InMemoryProjection()),
        inbound={"in": ["x", "y"]},
    )

    carrier, outputs = run(drive_session(session, inputs=[], env=env))

    assert carrier == "y"
    assert outputs == ["x", "y"]
    assert env.emitted(session.out_channel) == ["x", "y"]
