"""Bounded polling bridge from durable projection rows to SSE."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping
from typing import Any

from fastapi import Request
from sse_starlette.event import ServerSentEvent
from sse_starlette.sse import EventSourceResponse

from ..execution.projection_store import ExecutionStore, TERMINAL_RUN_STATUSES
from ..ir import canonical_json

EVENT_PAGE_LIMIT = 500
DEFAULT_HEARTBEAT_SECONDS = 15
DEFAULT_POLL_SECONDS = 0.25
SLOW_CLIENT_SEND_TIMEOUT_SECONDS = 30.0


def event_sequence(event: Mapping[str, Any]) -> int:
    value = event.get("seq")
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("stored projection event has no integer sequence")
    return value


def is_terminal_event(event: Mapping[str, Any]) -> bool:
    attrs = event.get("attrs")
    return isinstance(attrs, Mapping) and attrs.get("terminal") is True


def terminal_projection_is_persisted(
    run: Mapping[str, Any],
    *,
    terminal_seen: bool,
) -> bool:
    # A failed submission never had a workflow and therefore can never produce
    # a projection terminal row. Close the stream without synthesizing one.
    if run.get("status") == "start_failed":
        return True
    if run.get("status") not in TERMINAL_RUN_STATUSES:
        return False
    # A reconciler can stamp a terminal status when finishRun crashed. Status
    # (and its retention timestamp) is never proof that the projection row
    # landed, so only an observed durable terminal event closes the stream.
    return terminal_seen


async def _terminal_event_at_or_before(
    store: ExecutionStore,
    run_id: str,
    through_seq: int,
) -> bool:
    """Find a terminal row skipped by a reconnecting Last-Event-ID cursor."""

    if through_seq <= 0:
        return False
    cursor = 0
    while True:
        rows = await asyncio.to_thread(
            store.read_events,
            run_id,
            cursor,
            EVENT_PAGE_LIMIT,
        )
        if not rows:
            return False
        for row in rows:
            seq = event_sequence(row)
            if seq > through_seq:
                return False
            if is_terminal_event(row):
                return True
            cursor = seq
        if len(rows) < EVENT_PAGE_LIMIT:
            return False


async def iter_run_events(
    request: Request,
    store: ExecutionStore,
    run_id: str,
    *,
    after_seq: int,
    poll_seconds: float = DEFAULT_POLL_SECONDS,
) -> AsyncIterator[ServerSentEvent]:
    """Yield durable events, then stop only after the terminal transaction."""

    cursor = after_seq
    terminal_seen = await _terminal_event_at_or_before(store, run_id, after_seq)
    while True:
        if await request.is_disconnected():
            return

        rows = await asyncio.to_thread(
            store.read_events,
            run_id,
            cursor,
            EVENT_PAGE_LIMIT,
        )
        for row in rows:
            cursor = event_sequence(row)
            terminal_seen = terminal_seen or is_terminal_event(row)
            yield ServerSentEvent(
                data=canonical_json(row),
                event="projection",
                id=str(cursor),
            )

        run = await asyncio.to_thread(store.get_run, run_id)
        if run is None:
            return
        if not rows and terminal_projection_is_persisted(run, terminal_seen=terminal_seen):
            return
        if not rows:
            await asyncio.sleep(poll_seconds)


def run_event_response(
    request: Request,
    store: ExecutionStore,
    run_id: str,
    *,
    after_seq: int,
    heartbeat_seconds: int = DEFAULT_HEARTBEAT_SECONDS,
    poll_seconds: float = DEFAULT_POLL_SECONDS,
) -> EventSourceResponse:
    """Create an SSE response with comment heartbeats and bounded backpressure."""

    async def content() -> AsyncIterator[ServerSentEvent]:
        # An initial comment lets clients confirm that the stream was
        # established even when the first durable event is not yet available;
        # EventSourceResponse continues the same comment every heartbeat period.
        yield ServerSentEvent(comment="keep-alive")
        async for event in iter_run_events(
            request,
            store,
            run_id,
            after_seq=after_seq,
            poll_seconds=poll_seconds,
        ):
            yield event

    return EventSourceResponse(
        content(),
        ping=heartbeat_seconds,
        ping_message_factory=lambda: ServerSentEvent(comment="keep-alive"),
        send_timeout=SLOW_CLIENT_SEND_TIMEOUT_SECONDS,
    )


__all__ = [
    "DEFAULT_HEARTBEAT_SECONDS",
    "DEFAULT_POLL_SECONDS",
    "EVENT_PAGE_LIMIT",
    "event_sequence",
    "iter_run_events",
    "run_event_response",
]
