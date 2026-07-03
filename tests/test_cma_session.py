"""CMA-backed per-turn session handle tests."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import pytest

from composable_agents import Agent, AgentConfig, Budget, EnforcementMode, tool
from composable_agents.derived import emit, recv
from composable_agents.dsl import seq
from composable_agents.errors import ComposableAgentsError
from composable_agents.execution.cma import CMAEvent
from composable_agents.execution.cma_session import CMASessionHandle
from composable_agents.session import SessionEvent, loop
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


def test_strict_ungranted_tool_denies_without_invoking_tool() -> None:
    async def main() -> None:
        invoked = False
        turn = FakeCMASession(
            [CMAEvent("custom_tool_use", tool="secret", input={}, call_id="e1")]
        )
        client = QueueingFakeCMAClient([turn])

        def secret(_value: Any) -> Any:
            nonlocal invoked
            invoked = True
            return {"should": "not run"}

        handle = CMASessionHandle(
            client=client,
            tools={"secret": secret},
            agent={"name": "controller", "tools": []},
            cfg=AgentConfig(mode=EnforcementMode.STRICT),
            granted=set(),
        )
        agen = handle.events()

        await handle.send("query")
        events = [_event_to_tuple(await _next_event(agen)) for _ in range(3)]
        assert events[0] == ("turn", "started")
        assert events[1][0] == "error"
        assert "secret" in events[1][1]
        assert events[1][2] is True
        assert events[2][0] == "closed"
        assert invoked is False
        assert turn.results == []
        assert turn.errors == [("e1", events[1][1])]

    run(main())


def test_dev_ungranted_tool_records_gap_and_skips_tool_result() -> None:
    async def main() -> None:
        invoked = False
        turn = FakeCMASession(
            [
                CMAEvent("custom_tool_use", tool="secret", input={}, call_id="e1"),
                CMAEvent("terminal", output="done"),
            ]
        )
        client = QueueingFakeCMAClient([turn])

        def secret(_value: Any) -> Any:
            nonlocal invoked
            invoked = True
            return {"should": "not run"}

        handle = CMASessionHandle(
            client=client,
            tools={"secret": secret},
            agent={"name": "controller", "tools": []},
            cfg=AgentConfig(mode=EnforcementMode.DEV),
            granted=set(),
        )
        agen = handle.events()

        await handle.send("query")
        events = [_event_to_tuple(await _next_event(agen)) for _ in range(3)]
        assert events == [
            ("turn", "started"),
            ("emit", "out", 1, "done"),
            ("turn", "done"),
        ]
        assert invoked is False
        assert turn.results == []
        assert turn.errors == []
        assert handle._prod_gaps == ["tool 'secret' is not granted"]

        await handle.close("done")
        assert await _next_event(agen) == SessionEvent.closed("done")

    run(main())


def test_budget_breach_ends_turn_without_invoking_tool() -> None:
    async def main() -> None:
        turn = FakeCMASession(
            [CMAEvent("custom_tool_use", tool="search", input={}, call_id="e1")]
        )
        client = QueueingFakeCMAClient([turn])

        def search(_value: Any) -> Any:
            raise AssertionError("tool should not execute")

        handle = CMASessionHandle(
            client=client,
            tools={"search": search},
            agent={"name": "controller", "tools": []},
            cfg=AgentConfig(budget=Budget(cost=0.75), think_cost=0.25),
            granted={"search"},
        )
        agen = handle.events()

        await handle.send("query")
        events = [_event_to_tuple(await _next_event(agen)) for _ in range(3)]
        assert events == [
            ("turn", "started"),
            ("error", "over_budget", True),
            ("closed", "CMA session tool request failed"),
        ]
        assert turn.results == []

    run(main())


def test_inputless_tool_event_uses_prior_state_last() -> None:
    async def main() -> None:
        seen: list[Any] = []
        turn = FakeCMASession(
            [
                CMAEvent("custom_tool_use", tool="search", input=None, call_id="e1"),
                CMAEvent("custom_tool_use", tool="fetch", input=None, call_id="e2"),
                CMAEvent("terminal", output="done"),
            ]
        )
        client = QueueingFakeCMAClient([turn])

        def search(value: Any) -> dict[str, Any]:
            seen.append(value)
            return {"searched": value}

        def fetch(value: Any) -> dict[str, Any]:
            seen.append(value)
            return {"fetched": value}

        handle = CMASessionHandle(
            client=client,
            tools={"search": search, "fetch": fetch},
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
        assert seen == ["query", {"searched": "query"}]
        assert turn.results == [
            ("e1", {"searched": "query"}),
            ("e2", {"fetched": {"searched": "query"}}),
        ]

        await handle.close("done")
        assert await _next_event(agen) == SessionEvent.closed("done")

    run(main())


def test_send_idempotency_dedups_and_rejects_payload_mismatch() -> None:
    async def main() -> None:
        turn = FakeCMASession([CMAEvent("terminal", output="ack")])
        client = QueueingFakeCMAClient([turn])
        handle = CMASessionHandle(
            client=client,
            tools={},
            agent={"name": "controller", "tools": []},
        )
        agen = handle.events()

        ack1 = await handle.send({"msg": "a"}, idempotency_key="k")
        ack2 = await handle.send({"msg": "a"}, idempotency_key="k")
        assert ack1 == {"seq": 1, "channel": "in"}
        assert ack2 == ack1
        with pytest.raises(ComposableAgentsError, match="different payload"):
            await handle.send({"msg": "b"}, idempotency_key="k")

        events = [_event_to_tuple(await _next_event(agen)) for _ in range(3)]
        assert events == [
            ("turn", "started"),
            ("emit", "out", 1, "ack"),
            ("turn", "done"),
        ]
        assert len(client.calls) == 1

        await handle.close("done")
        assert await _next_event(agen) == SessionEvent.closed("done")

    run(main())


def test_send_rejects_unsupported_channel() -> None:
    async def main() -> None:
        handle = CMASessionHandle(
            client=QueueingFakeCMAClient([]),
            tools={},
            agent={"name": "controller", "tools": []},
        )
        with pytest.raises(ComposableAgentsError, match="unsupported channel"):
            await handle.send("x", channel="side")
        state = await handle.state()
        assert state["pending"] == {"in": 0}
        await handle.close("done")

    run(main())


def test_close_cancels_hanging_active_stream_and_emits_closed_once() -> None:
    class HangingCMASession:
        def __init__(self) -> None:
            self.results: list[tuple[str, Any]] = []
            self.errors: list[tuple[str, str]] = []
            self.cancelled = 0
            self.serviced = asyncio.Event()

        async def events(self) -> AsyncIterator[CMAEvent]:
            yield CMAEvent("custom_tool_use", tool="search", input=None, call_id="e1")
            await asyncio.Event().wait()

        async def tool_result(self, call_id: str, result: Any) -> None:
            self.results.append((call_id, result))
            self.serviced.set()

        async def tool_error(self, call_id: str, reason: str) -> None:
            self.errors.append((call_id, reason))

        async def cancel(self) -> None:
            self.cancelled += 1

    async def main() -> None:
        turn = HangingCMASession()
        client = QueueingFakeCMAClient([turn])  # type: ignore[list-item]
        handle = CMASessionHandle(
            client=client,
            tools={"search": lambda value: {"searched": value}},
            agent={"name": "controller", "tools": []},
        )
        agen = handle.events()

        await handle.send("query")
        assert _event_to_tuple(await _next_event(agen)) == ("turn", "started")
        await asyncio.wait_for(turn.serviced.wait(), timeout=1.0)
        await asyncio.wait_for(handle.close("done"), timeout=1.0)

        assert await _next_event(agen) == SessionEvent.closed("done")
        with pytest.raises(StopAsyncIteration):
            await agen.__anext__()
        assert turn.cancelled >= 1

    run(main())


def test_agent_open_cma_wires_tools_grants_contracts_and_turns() -> None:
    @tool(effect="read", idempotent=True)
    def cma_session_lookup(value: str) -> dict[str, str]:
        """Look up a value."""
        return {"hit": value}

    async def main() -> None:
        turn = FakeCMASession(
            [
                CMAEvent(
                    "custom_tool_use",
                    tool="cma_session_lookup",
                    input={"value": "ticket"},
                    call_id="e1",
                ),
                CMAEvent("terminal", output={"answer": "ok"}),
            ]
        )
        client = QueueingFakeCMAClient([turn])
        agent = Agent("reply", tools=[cma_session_lookup], name="cma_session_agent")
        session = loop(seq(recv("in"), emit("out")), init=None)

        handle = await agent.open(
            session=session,
            backend="cma",
            client=client,
            environment={"kind": "test"},
        )
        assert isinstance(handle, CMASessionHandle)
        assert handle._granted == {"cma_session_lookup"}
        assert handle._contracts["cma_session_lookup"]["effect"] == "read"
        assert handle._contracts["cma_session_lookup"]["idempotency"] == "native"

        agen = handle.events()
        await handle.send("ticket")
        events = [_event_to_tuple(await _next_event(agen)) for _ in range(3)]
        assert events == [
            ("turn", "started"),
            ("emit", "out", 1, {"answer": "ok"}),
            ("turn", "done"),
        ]
        assert turn.results == [("e1", {"hit": "ticket"})]
        assert client.calls[0]["environment"] == {"kind": "test"}
        assert client.calls[0]["agent"]["name"] == "cma_session_agent"
        assert client.calls[0]["agent"]["tools"][0]["name"] == "cma_session_lookup"

        await handle.close("done")
        assert await _next_event(agen) == SessionEvent.closed("done")

    run(main())
