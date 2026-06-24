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
from composable_agents.errors import (
    ComposableAgentsError,
    SessionTurnError,
    ValidationError,
)
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


def _facade_boom(value: Any) -> Any:
    del value
    raise RuntimeError("boom")


register_pure("tests.session_facade.boom", _facade_boom)

_NON_FATAL_CALLS = 0


def _facade_non_fatal_once(value: dict[str, Any]) -> tuple[list[Any], dict[str, Any]]:
    global _NON_FATAL_CALLS
    _NON_FATAL_CALLS += 1
    if _NON_FATAL_CALLS == 1:
        raise SessionTurnError("try again", fatal=False)
    carrier = list(value["carrier"] or [])
    msg = value["msg"]
    next_carrier = [*carrier, msg]
    return next_carrier, {"seen": list(next_carrier), "reply": f"ack:{msg}"}


register_pure("tests.session_facade.non_fatal_once", _facade_non_fatal_once)


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

        for _ in range(100):
            snap = await handle.state()
            if len(snap.get("emitted", {}).get("out", [])) >= 2:
                break
            await asyncio.sleep(0.01)
        snap = await handle.state()
        assert snap["carrier"] == ["a", "b"]
        assert snap["emitted"]["out"] == [
            {"seq": 1, "payload": {"seen": ["a"], "reply": "ack:a"}},
            {"seq": 2, "payload": {"seen": ["a", "b"], "reply": "ack:b"}},
        ]
        assert snap["closed"] is False

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
        assert snap["emitted"]["out"] == []
        assert snap["closed"] is False

        await handle.close("done")
        closed = await _next_event(agen)
        assert closed == SessionEvent.closed("done")
        with pytest.raises(StopAsyncIteration):
            await agen.__anext__()

    run(main())


def test_local_open_receives_reports_parked_channel() -> None:
    async def main() -> None:
        agent = Agent("test-model", llm=None)
        handle = await agent.open(session=_session(), backend="local")
        handle.events()

        records = []
        for _ in range(50):
            records = await handle.open_receives()
            if any(record.get("channel") == "in" for record in records):
                break
            await asyncio.sleep(0.01)

        parked = [record for record in records if record.get("channel") == "in"]
        assert parked, records
        assert set(parked[0]) == {"channel", "seq"}
        assert isinstance(parked[0]["seq"], int)

        await handle.close()

    run(main())


def test_local_session_turn_error_surfaces_error_event_no_unretrieved() -> None:
    async def main() -> None:
        session = scan(
            seq(recv("in"), arr("tests.session_facade.boom")),
            init=[],
            in_channel="in",
            out_channel="out",
        )
        agent = Agent("test-model", llm=None)
        handle = await agent.open(session=session, backend="local")
        agen = handle.events()

        await handle.send("a")

        started = await _next_event(agen)
        assert started == SessionEvent.turn_started()

        error = await _next_event(agen)
        assert error.is_error
        assert error.fatal is True
        assert "boom" in (error.reason or "")

        closed = await _next_event(agen)
        assert closed.is_closed

        await handle.close()

    run(main())


def test_local_close_flushes_in_flight_turn_before_closed() -> None:
    async def main() -> None:
        agent = Agent("test-model", llm=None)
        handle = await agent.open(session=_session(), backend="local")
        agen = handle.events()

        await handle.send("a")
        await handle.close("done")

        events = [_event_to_tuple(await _next_event(agen)) for _ in range(4)]
        assert events == [
            ("turn", "started"),
            ("emit", 1, {"seen": ["a"], "reply": "ack:a"}),
            ("turn", "done"),
            ("closed", "done"),
        ]
        with pytest.raises(StopAsyncIteration):
            await agen.__anext__()

    run(main())


def test_local_non_fatal_turn_error_keeps_session_alive() -> None:
    async def main() -> None:
        global _NON_FATAL_CALLS
        _NON_FATAL_CALLS = 0
        session = scan(
            seq(recv("in"), arr("tests.session_facade.non_fatal_once")),
            init=[],
            in_channel="in",
            out_channel="out",
        )
        agent = Agent("test-model", llm=None)
        handle = await agent.open(session=session, backend="local")
        agen = handle.events()

        await handle.send("first")
        first_turn = [_event_contract_tuple(await _next_event(agen)) for _ in range(3)]
        assert first_turn == [
            ("turn", "started", None, None, None),
            ("error", None, None, "try again", False),
            ("turn", "done", None, None, None),
        ]

        snap = await handle.state()
        assert snap["carrier"] == []
        assert snap["closed"] is False

        await handle.send("second")
        second_turn = [_event_contract_tuple(await _next_event(agen)) for _ in range(3)]
        assert second_turn == [
            ("turn", "started", None, None, None),
            ("emit", None, 1, {"seen": ["second"], "reply": "ack:second"}, None),
            ("turn", "done", None, None, None),
        ]

        await handle.close("done")
        closed = await _next_event(agen)
        assert closed == SessionEvent.closed("done")

    run(main())


def test_local_event_contract_two_turn_sequence() -> None:
    async def main() -> None:
        agent = Agent("test-model", llm=None)
        handle = await agent.open(session=_session(), backend="local")
        agen = handle.events()

        await handle.send("a")
        await handle.send("b")
        events = [_event_contract_tuple(await _next_event(agen)) for _ in range(6)]
        await handle.close("done")
        events.append(_event_contract_tuple(await _next_event(agen)))

        assert events == _expected_event_contract_sequence()

    run(main())


def test_local_events_is_single_consumer() -> None:
    async def main() -> None:
        agent = Agent("test-model", llm=None)
        handle = await agent.open(session=_session(), backend="local")
        handle.events()
        with pytest.raises(ComposableAgentsError, match="single-consumer"):
            handle.events()
        await handle.close()

    run(main())


def test_local_send_idempotency_key_dedups_and_conflicts() -> None:
    async def main() -> None:
        agent = Agent("test-model", llm=None)
        handle = await agent.open(session=_session(), backend="local")

        ack1 = await handle.send("a", idempotency_key="k1")
        ack2 = await handle.send("a", idempotency_key="k1")
        assert ack1 == {"seq": 1, "channel": "in"}
        assert ack2 == ack1

        with pytest.raises(ComposableAgentsError, match="different payload"):
            await handle.send("DIFFERENT", idempotency_key="k1")

        agen = handle.events()
        events = [_event_to_tuple(await _next_event(agen)) for _ in range(3)]
        assert events == [
            ("turn", "started"),
            ("emit", 1, {"seen": ["a"], "reply": "ack:a"}),
            ("turn", "done"),
        ]

        await handle.close()

    run(main())


def test_open_session_local_is_unsupported() -> None:
    agent = Agent("test-model", llm=None)
    with pytest.raises(RuntimeError, match="await"):
        agent.open_session(session=_session(), backend="local")


def test_local_channel_capacity_is_surfaced_in_state() -> None:
    async def main() -> None:
        agent = Agent("test-model", llm=None)
        handle = await agent.open(
            session=_session(),
            backend="local",
            channel_capacity=1,
        )

        snap = await handle.state()
        assert snap["capacity"] == 1

        await handle.close()

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


def _event_contract_tuple(event: SessionEvent) -> tuple[Any, ...]:
    if event.is_turn:
        return ("turn", event.turn, None, None, None)
    if event.is_emit:
        return ("emit", None, event.seq, event.payload, None)
    if event.is_error:
        return ("error", None, None, event.reason, event.fatal)
    return (event.kind, None, None, event.reason, None)


def _expected_event_contract_sequence() -> list[tuple[Any, ...]]:
    return [
        ("turn", "started", None, None, None),
        ("emit", None, 1, {"seen": ["a"], "reply": "ack:a"}, None),
        ("turn", "done", None, None, None),
        ("turn", "started", None, None, None),
        ("emit", None, 2, {"seen": ["a", "b"], "reply": "ack:b"}, None),
        ("turn", "done", None, None, None),
        ("closed", None, None, "done", None),
    ]
