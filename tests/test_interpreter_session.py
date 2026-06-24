"""Long-lived session interpreter tests (recv/emit + LOOP)."""

from __future__ import annotations

from typing import Any

import pytest

from composable_agents import (
    call,
    emit,
    mcp,
    recv,
    scan,
    seq,
)
from composable_agents.execution.interpreter import InMemoryEnv, SessionClosed, interpret
from composable_agents.ir import Node
from composable_agents.projection import InMemoryProjection, ProjectionEmitter
from conftest import run


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
    flow = seq(recv("in", timeout_s=3), emit("out"))
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
    session = scan(seq(recv("in"), emit("out")), init=None)
    flow, env = _env(session.body, inbound={"in": ["a", "b", "c"]})

    run(interpret(flow, session.init, env))

    assert env.emitted("out") == ["a", "b", "c"]


def test_loop_accumulator_session_e2e() -> None:
    total = [0]

    def accum(value: int) -> int:
        total[0] += value
        return total[0]

    session = scan(seq(recv("in"), call(mcp("srv", "accum")), emit("out")), init=0)
    flow, env = _env(
        session.body,
        tools={"srv/accum": accum},
        inbound={"in": [1, 2, 3]},
    )

    out = run(interpret(flow, session.init, env))

    assert env.emitted("out") == [1, 3, 6]
    assert out.value == 6
