"""Local session turn-error survival tests."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from julep import (
    Agent,
    LocalSessionHandle,
    SessionEvent,
    arr,
    recv,
    register_pure,
    scan,
    seq,
)
from julep.errors import SessionTurnError
from julep.execution.interpreter import SessionClosed
from conftest import run


def _survival_step(value: dict[str, Any]) -> tuple[list[Any], dict[str, Any]]:
    carrier = list(value["carrier"] or [])
    msg = str(value["msg"])

    if msg.startswith("boom"):
        raise RuntimeError(msg)
    if msg.startswith("fatal"):
        raise SessionTurnError(msg, fatal=True)
    if msg.startswith("close"):
        raise SessionClosed(msg)

    next_carrier = [*carrier, msg]
    return next_carrier, {"seen": list(next_carrier), "reply": f"ack:{msg}"}


register_pure("tests.session_error_survival.step", _survival_step)


def _session():
    return scan(
        seq(recv("in"), arr("tests.session_error_survival.step")),
        init=[],
        in_channel="in",
        out_channel="out",
    )


async def _next_event(
    agen: AsyncIterator[SessionEvent], *, timeout_s: float = 1.0
) -> SessionEvent:
    return await asyncio.wait_for(agen.__anext__(), timeout=timeout_s)


async def _collect_until_closed(
    agen: AsyncIterator[SessionEvent],
) -> list[SessionEvent]:
    events: list[SessionEvent] = []
    while True:
        event = await _next_event(agen)
        events.append(event)
        if event.is_closed:
            return events


def _error_contracts(events: list[SessionEvent]) -> list[tuple[str, bool]]:
    return [
        (event.reason or "", event.fatal)
        for event in events
        if event.is_error
    ]


def _fatal_errors(events: list[SessionEvent]) -> list[str]:
    return [
        event.reason or ""
        for event in events
        if event.is_error and event.fatal
    ]


def _emit_payloads(events: list[SessionEvent]) -> list[Any]:
    return [event.payload for event in events if event.is_emit]


def _turn_started_count(events: list[SessionEvent]) -> int:
    return sum(
        1 for event in events if event.is_turn and event.turn == "started"
    )


def test_plain_exception_turn_is_non_fatal_and_later_turns_process() -> None:
    async def main() -> None:
        handle = await LocalSessionHandle.open(_session())
        agen = handle.events()

        for msg in ("one", "boom:two", "three", "four"):
            await handle.send(msg)
        await handle.close("done")

        events = await _collect_until_closed(agen)
        assert _error_contracts(events) == [("boom:two", False)]
        assert _fatal_errors(events) == []
        assert _emit_payloads(events) == [
            {"seen": ["one"], "reply": "ack:one"},
            {"seen": ["one", "three"], "reply": "ack:three"},
            {"seen": ["one", "three", "four"], "reply": "ack:four"},
        ]
        assert events[-1] == SessionEvent.closed("done")

    run(main())


def test_three_consecutive_plain_exceptions_hit_default_fatal_limit() -> None:
    async def main() -> None:
        handle = await LocalSessionHandle.open(_session())
        agen = handle.events()

        for msg in ("boom:first", "boom:second", "boom:third", "after"):
            await handle.send(msg)
        await handle.close("done")

        events = await _collect_until_closed(agen)
        assert _turn_started_count(events) == 3
        assert _error_contracts(events) == [
            ("boom:first", False),
            ("boom:second", False),
            ("boom:third", True),
        ]
        assert _emit_payloads(events) == []
        assert events[-1].is_closed

    run(main())


def test_consecutive_plain_exception_counter_resets_after_success() -> None:
    async def main() -> None:
        handle = await LocalSessionHandle.open(_session())
        agen = handle.events()

        for msg in ("boom:first", "ok:one", "boom:second", "ok:two"):
            await handle.send(msg)
        await handle.close("done")

        events = await _collect_until_closed(agen)
        assert _error_contracts(events) == [
            ("boom:first", False),
            ("boom:second", False),
        ]
        assert _fatal_errors(events) == []
        assert _emit_payloads(events) == [
            {"seen": ["ok:one"], "reply": "ack:ok:one"},
            {"seen": ["ok:one", "ok:two"], "reply": "ack:ok:two"},
        ]
        assert events[-1] == SessionEvent.closed("done")

    run(main())


def test_session_closed_still_exits_silently() -> None:
    async def main() -> None:
        handle = await LocalSessionHandle.open(_session())
        agen = handle.events()

        await handle.send("close:now")

        events = await _collect_until_closed(agen)
        assert _error_contracts(events) == []
        assert _emit_payloads(events) == []
        assert events[-1] == SessionEvent.closed()

    run(main())


def test_fatal_session_turn_error_tears_down_immediately() -> None:
    async def main() -> None:
        handle = await LocalSessionHandle.open(_session())
        agen = handle.events()

        await handle.send("fatal:first")
        await handle.send("after")
        await handle.close("done")

        events = await _collect_until_closed(agen)
        assert _error_contracts(events) == [("fatal:first", True)]
        assert _emit_payloads(events) == []
        assert events[-1].is_closed

    run(main())


def test_local_open_accepts_custom_max_consecutive_turn_errors() -> None:
    async def main() -> None:
        handle = await LocalSessionHandle.open(
            _session(),
            max_consecutive_turn_errors=1,
        )
        agen = handle.events()

        await handle.send("boom:single")
        await handle.send("after")
        await handle.close("done")

        events = await _collect_until_closed(agen)
        assert _turn_started_count(events) == 1
        assert _error_contracts(events) == [("boom:single", True)]
        assert _emit_payloads(events) == []
        assert events[-1].is_closed

    run(main())


def test_agent_open_local_accepts_custom_max_consecutive_turn_errors() -> None:
    async def main() -> None:
        agent = Agent("test-model", llm=None)
        handle = await agent.open(
            session=_session(),
            backend="local",
            max_consecutive_turn_errors=1,
        )
        agen = handle.events()

        await handle.send("boom:single")
        await handle.send("after")
        await handle.close("done")

        events = await _collect_until_closed(agen)
        assert _turn_started_count(events) == 1
        assert _error_contracts(events) == [("boom:single", True)]
        assert _emit_payloads(events) == []
        assert events[-1].is_closed

    run(main())
