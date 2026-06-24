"""CMA-backed per-turn live session handle."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import AsyncIterator, Callable, Mapping
from typing import Any, Optional

from ..errors import ComposableAgentsError
from ..session import SessionEvent
from .cma import CMAClient, CMAEvent, CMASession
from .interpreter import SessionClosed

__all__ = ["CMASessionHandle"]


class CMASessionHandle:
    """SessionHandle-compatible facade backed by one CMA session per turn."""

    _WAKE: object = object()

    def __init__(
        self,
        *,
        client: CMAClient,
        tools: Mapping[str, Callable[[Any], Any]],
        agent: dict[str, Any],
        environment: Any = None,
        in_channel: str = "in",
        out_channel: str = "out",
        session_cid: str = "cma-session",
    ) -> None:
        self._client = client
        self._tools: dict[str, Callable[[Any], Any]] = dict(tools)
        self._agent = dict(agent)
        self._environment = environment
        self._in_channel = in_channel
        self._out_channel = out_channel
        self._session_cid = session_cid

        self._events: asyncio.Queue[SessionEvent] = asyncio.Queue()
        self._inbound: asyncio.Queue[Any] = asyncio.Queue()
        self._active_session: Optional[CMASession] = None

        self._send_seq = 0
        self._out_seq = 0
        self._turn_seq = 0
        self._completed_turns = 0

        self._closed = False
        self._closing = False
        self._close_reason: Optional[str] = None
        self._closed_event_sent = False
        self._events_subscribed = False
        self._driver = asyncio.create_task(self._drive())

    @classmethod
    async def open(
        cls,
        *,
        client: CMAClient,
        tools: Mapping[str, Callable[[Any], Any]],
        agent: dict[str, Any],
        environment: Any = None,
        in_channel: str = "in",
        out_channel: str = "out",
        session_cid: str = "cma-session",
    ) -> "CMASessionHandle":
        return cls(
            client=client,
            tools=tools,
            agent=agent,
            environment=environment,
            in_channel=in_channel,
            out_channel=out_channel,
            session_cid=session_cid,
        )

    async def _drive(self) -> None:
        reason: Optional[str] = None
        try:
            while True:
                item = await self._inbound.get()
                if item is self._WAKE or self._closing:
                    break

                self._turn_seq += 1
                await self._events.put(SessionEvent.turn_started())
                cma_session = await self._client.create_session(
                    agent=self._agent,
                    environment=self._environment,
                    session_cid=f"{self._session_cid}-turn-{self._turn_seq}",
                    input=item,
                )
                self._active_session = cma_session
                terminal_seen = False

                try:
                    async for event in cma_session.events():
                        if self._closing:
                            break
                        if event.is_custom_tool_use:
                            await self._service_tool(cma_session, event)
                            continue
                        if event.is_terminal:
                            await self._handle_terminal(event)
                            terminal_seen = True
                            self._completed_turns += 1
                            break
                        if event.is_error:
                            reason = event.reason or "session error"
                            self._closing = True
                            await self._events.put(
                                SessionEvent.error(reason, fatal=True)
                            )
                            break
                finally:
                    try:
                        await cma_session.cancel()
                    finally:
                        if self._active_session is cma_session:
                            self._active_session = None

                if self._closing:
                    break
                if not terminal_seen:
                    reason = "session ended without terminal output"
                    await self._events.put(SessionEvent.error(reason, fatal=True))
                    break
        except Exception as exc:
            reason = str(exc)
            self._closing = True
            await self._events.put(SessionEvent.error(reason, fatal=True))
        finally:
            self._closed = True
            await self._put_closed_once(self._close_reason or reason)

    async def _service_tool(self, cma_session: CMASession, event: CMAEvent) -> None:
        call_id = self._event_call_id(event)
        try:
            tool = self._event_tool(event)
            fn = self._tools[tool]
            result = fn(event.input)
            if inspect.isawaitable(result):
                result = await result
        except Exception as exc:
            await cma_session.tool_error(call_id, str(exc))
            return
        await cma_session.tool_result(call_id, result)

    async def _handle_terminal(self, event: CMAEvent) -> None:
        if event.output is not None:
            self._out_seq += 1
            await self._events.put(
                SessionEvent.emit(self._out_channel, self._out_seq, event.output)
            )
        await self._events.put(SessionEvent.turn_done())

    async def _put_closed_once(self, reason: Optional[str]) -> None:
        if self._closed_event_sent:
            return
        self._closed_event_sent = True
        await self._events.put(SessionEvent.closed(reason))

    def events(self) -> AsyncIterator[SessionEvent]:
        if self._events_subscribed:
            raise ComposableAgentsError("session events() is single-consumer per handle")
        self._events_subscribed = True

        async def gen() -> AsyncIterator[SessionEvent]:
            while True:
                event = await self._events.get()
                yield event
                if event.is_closed:
                    return

        return gen()

    async def send(
        self,
        value: Any,
        *,
        channel: Optional[str] = None,
        idempotency_key: Any = None,
    ) -> dict[str, Any]:
        del idempotency_key
        if self._closed or self._closing:
            raise SessionClosed("session is closed")
        self._send_seq += 1
        self._inbound.put_nowait(value)
        return {"seq": self._send_seq, "channel": channel or self._in_channel}

    async def state(self) -> dict[str, Any]:
        return {"closed": self._closed, "turns": self._completed_turns}

    async def open_receives(self) -> list[dict[str, Any]]:
        return []

    async def close(self, reason: Optional[str] = None) -> None:
        if self._closed:
            return
        self._close_reason = reason
        self._closing = True
        active = self._active_session
        if active is not None:
            await active.cancel()
        self._inbound.put_nowait(self._WAKE)
        await asyncio.gather(self._driver, return_exceptions=True)

    @staticmethod
    def _event_tool(event: CMAEvent) -> str:
        if event.tool is None:
            raise ComposableAgentsError("custom_tool_use event missing tool")
        return event.tool

    @staticmethod
    def _event_call_id(event: CMAEvent) -> str:
        if event.call_id is None:
            raise ComposableAgentsError("custom_tool_use event missing call_id")
        return event.call_id
