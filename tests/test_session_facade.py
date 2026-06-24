"""Public session facade tests (M2 facade)."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from composable_agents import (
    Agent,
    SessionEvent,
    arr,
    deploy,
    recv,
    register_pure,
    scan,
    seq,
    validate,
)
from composable_agents.errors import ValidationError
from composable_agents.execution.interpreter import InMemoryEnv, interpret
from composable_agents.freeze import McpSnapshot
from composable_agents.projection import EventType, InMemoryProjection, ProjectionEmitter
from composable_agents.validate import blocking
from conftest import run


def _facade_append_with_reply(value: dict[str, Any]) -> tuple[list[Any], dict[str, Any]]:
    carrier = list(value["carrier"] or [])
    msg = value["msg"]
    next_carrier = [*carrier, msg]
    return next_carrier, {"seen": list(next_carrier), "reply": f"ack:{msg}"}


register_pure("tests.session_facade.append_with_reply", _facade_append_with_reply)


def _session():
    return scan(
        seq(recv("in"), arr("tests.session_facade.append_with_reply")),
        init=[],
        in_channel="in",
        out_channel="out",
    )


async def _next_event(handle, *, timeout_s: float = 1.0) -> SessionEvent:
    return await asyncio.wait_for(handle.__anext__(), timeout=timeout_s)


def test_agent_open_local_drives_live_session_until_closed() -> None:
    async def main() -> None:
        session = _session()
        agent = Agent("test-model", llm=None)
        handle = await agent.open(session=session, backend="local")

        agen = handle.events()
        ack1 = await handle.send("a")
        ack2 = await handle.send("b")
        assert ack1 == {"seq": 1, "channel": "in"}
        assert ack2 == {"seq": 2, "channel": "in"}

        events = [_event_to_tuple(await _next_event(agen)) for _ in range(6)]
        assert events == [
            ("turn", "started"),
            ("emit", 1, {"seen": ["a"], "reply": "ack:a"}),
            ("turn", "done"),
            ("turn", "started"),
            ("emit", 2, {"seen": ["a", "b"], "reply": "ack:b"}),
            ("turn", "done"),
        ]

        snap = await handle.state()
        assert snap["carrier"] == ["a", "b"]
        assert snap["emitted"]["out"] == [
            {"seq": 1, "payload": {"seen": ["a"], "reply": "ack:a"}},
            {"seq": 2, "payload": {"seen": ["a", "b"], "reply": "ack:b"}},
        ]
        assert snap["closed"] is False

        await handle.close("done")
        closed = await _next_event(agen)
        assert closed == SessionEvent.closed("done")
        with pytest.raises(StopAsyncIteration):
            await agen.__anext__()

    run(main())


def test_deploy_rejects_session_loop_in_flow_target() -> None:
    session = _session()
    with pytest.raises(ValidationError) as raised:
        deploy(session.body, McpSnapshot())

    codes = {diagnostic.code for diagnostic in raised.value.diagnostics}
    assert "SESSION_LOOP_IN_FLOW" in codes


def test_runtime_compiled_plan_validation_rejects_session_ops_in_flow_target() -> None:
    session = _session()
    diagnostics = blocking(validate(session.body, target="flow"))
    codes = {diagnostic.code for diagnostic in diagnostics}
    assert "SESSION_LOOP_IN_FLOW" in codes
    assert "SESSION_RECV_IN_FLOW" in codes


def test_clean_session_close_leaves_no_orphan_planned_projection_events() -> None:
    session = _session()
    store = InMemoryProjection()
    env = InMemoryEnv(
        {},
        ProjectionEmitter(store),
        inbound={"in": ["a"]},
    )

    run(interpret(session.body, session.init, env))

    terminal = {
        (event.node, event.cid)
        for event in store.events()
        if event.type in (EventType.DID, EventType.FAILED)
    }
    orphan_planned = [
        event
        for event in store.events()
        if event.type == EventType.PLANNED and (event.node, event.cid) not in terminal
    ]
    assert orphan_planned == []


def _event_to_tuple(event: SessionEvent) -> tuple[Any, ...]:
    if event.is_turn:
        return ("turn", event.turn)
    if event.is_emit:
        return ("emit", event.seq, event.payload)
    return (event.kind, event.reason)
