"""CMA-backed per-turn session handle tests."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any, Optional

import pytest

from composable_agents.execution.cma import CMAEvent
from composable_agents.execution.cma_session import CMASessionHandle
from composable_agents.session import SessionEvent
from cma_fakes import FakeCMASession
from conftest import run


class QueueingFakeCMAClient:
    """Return a fresh scripted CMA session for each turn."""

    def __init__(self, sessions: list[FakeCMASession]) -> None:
        self._sessions = list(sessions)
        self.calls: list[dict[str, Any]] = []

    async def create_session(
        self,
        *,
        agent: dict[str, Any],
        environment: Any,
        session_cid: str,
        input: Any = None,
    ) -> FakeCMASession:
        if not self._sessions:
            raise AssertionError("no queued CMA session")
        self.calls.append(
            {
                "agent": agent,
                "environment": environment,
                "session_cid": session_cid,
                "input": input,
            }
        )
        return self._sessions.pop(0)


async def _next_event(
    agen: AsyncIterator[SessionEvent],
    *,
    timeout_s: float = 1.0,
) -> SessionEvent:
    return await asyncio.wait_for(agen.__anext__(), timeout=timeout_s)


def _event_to_tuple(event: SessionEvent) -> tuple[Any, ...]:
    if event.is_turn:
        return ("turn", event.turn)
    if event.is_emit:
        return ("emit", event.channel, event.seq, event.payload)
    if event.is_error:
        return ("error", event.reason, event.fatal)
    if event.is_closed:
        return ("closed", event.reason)
    return (event.kind,)


def test_two_turn_session_matches_local_event_shape() -> None:
    async def main() -> None:
        turn1 = FakeCMASession([CMAEvent("terminal", output="ack:a")])
        turn2 = FakeCMASession([CMAEvent("terminal", output="ack:b")])
        client = QueueingFakeCMAClient([turn1, turn2])
        handle = CMASessionHandle(
            client=client,
            tools={},
            agent={"name": "controller", "tools": []},
        )
        agen = handle.events()

        ack1 = await handle.send("a")
        assert ack1 == {"seq": 1, "channel": "in"}
        first_turn = [_event_to_tuple(await _next_event(agen)) for _ in range(3)]
        assert first_turn == [
            ("turn", "started"),
            ("emit", "out", 1, "ack:a"),
            ("turn", "done"),
        ]

        ack2 = await handle.send("b")
        assert ack2 == {"seq": 2, "channel": "in"}
        second_turn = [_event_to_tuple(await _next_event(agen)) for _ in range(3)]
        assert second_turn == [
            ("turn", "started"),
            ("emit", "out", 2, "ack:b"),
            ("turn", "done"),
        ]

        assert [call["input"] for call in client.calls] == ["a", "b"]
        assert [call["session_cid"] for call in client.calls] == [
            "cma-session-turn-1",
            "cma-session-turn-2",
        ]

        await handle.close("done")
        assert await _next_event(agen) == SessionEvent.closed("done")
        assert turn1.cancelled >= 1
        assert turn2.cancelled >= 1
        with pytest.raises(StopAsyncIteration):
            await agen.__anext__()

    run(main())


def test_custom_tool_use_serviced_via_tool_result_mid_turn() -> None:
    async def main() -> None:
        turn = FakeCMASession(
            [
                CMAEvent(
                    "custom_tool_use",
                    tool="search",
                    input={"q": "x"},
                    call_id="e1",
                ),
                CMAEvent("terminal", output="done"),
            ]
        )
        client = QueueingFakeCMAClient([turn])
        handle = CMASessionHandle(
            client=client,
            tools={"search": lambda value: {"searched": value}},
            agent={"name": "controller", "tools": []},
        )
        agen = handle.events()

        await handle.send("query")
        events = [_event_to_tuple(await _next_event(agen)) for _ in range(3)]
        assert events == [
            ("turn", "started"),
            ("emit", "out", 1, "done"),
            ("turn", "done"),
        ]
        assert turn.results == [("e1", {"searched": {"q": "x"}})]

        await handle.close("done")
        assert await _next_event(agen) == SessionEvent.closed("done")

    run(main())


def test_cma_error_yields_error_then_closed() -> None:
    async def main() -> None:
        turn = FakeCMASession([CMAEvent("error", reason="boom")])
        client = QueueingFakeCMAClient([turn])
        handle = CMASessionHandle(
            client=client,
            tools={},
            agent={"name": "controller", "tools": []},
        )
        agen = handle.events()

        await handle.send("a")
        events = [_event_to_tuple(await _next_event(agen)) for _ in range(3)]
        assert events == [
            ("turn", "started"),
            ("error", "boom", True),
            ("closed", "boom"),
        ]
        with pytest.raises(StopAsyncIteration):
            await agen.__anext__()

    run(main())


def test_close_maps_to_cancel() -> None:
    async def main() -> None:
        turn = FakeCMASession([CMAEvent("terminal", output="x")])
        client = QueueingFakeCMAClient([turn])
        handle = CMASessionHandle(
            client=client,
            tools={},
            agent={"name": "controller", "tools": []},
        )
        agen = handle.events()

        await handle.send("a")
        events = [_event_to_tuple(await _next_event(agen)) for _ in range(3)]
        assert events == [
            ("turn", "started"),
            ("emit", "out", 1, "x"),
            ("turn", "done"),
        ]

        await handle.close("done")
        assert turn.cancelled >= 1
        assert await _next_event(agen) == SessionEvent.closed("done")
        with pytest.raises(StopAsyncIteration):
            await agen.__anext__()

    run(main())
