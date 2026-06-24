"""Local session primitives (cata inside / ana outside, design §4).

A session wraps an ordinary finite turn flow inside an unbounded ``Op.LOOP`` IR
boundary. The interpreter remains the catamorphism over the turn; this module
provides the local in-memory anamorphism that feeds messages in, threads the
carrier, and collects emitted outputs.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from collections.abc import AsyncIterator, Callable
from itertools import islice
from typing import Any, Generic, Iterable, Optional, Protocol, TypeVar

from .dsl import _nid, _node
from .errors import ComposableAgentsError, SessionTurnError
from .ir import ChannelRef, JSONSchema, Node
from .kinds import EnforcementMode, Op
from .execution.interpreter import InMemoryEnv, SessionClosed, interpret
from .projection import InMemoryProjection, ProjectionEmitter

I = TypeVar("I")
O = TypeVar("O")
T = TypeVar("T")


def _local_value_fingerprint(value: Any) -> str:
    try:
        from .execution.session_store import value_fingerprint

        return value_fingerprint(value)
    except Exception:
        return repr(value)


class Channel(Generic[T]):
    """A typed in-memory session port."""

    name: str
    payload: Optional[JSONSchema]

    def __init__(self, name: str, payload: Optional[JSONSchema] = None) -> None:
        self.name = name
        self.payload = payload
        self._inbound: asyncio.Queue[T] = asyncio.Queue()
        self._outbound: list[object] = []

    async def recv(self) -> T:
        """Take the next inbound message from the channel FIFO."""
        return await self._inbound.get()

    def append(self, value: T) -> None:
        """Append an inbound message to the channel FIFO."""
        self._inbound.put_nowait(value)

    def emit(self, value: object) -> None:
        """Append an outbound value to this channel's output buffer."""
        self._outbound.append(value)

    def drain(self) -> list[object]:
        """Return and clear the outbound output buffer."""
        out = list(self._outbound)
        self._outbound.clear()
        return out


@dataclass
class Session(Generic[I, O]):
    """A typed handle for a LOOP body and its local carrier state."""

    body: Node
    init: object
    in_channel: str
    out_channel: str


@dataclass(frozen=True)
class SessionEvent:
    """A normalized event from a live session."""

    kind: str
    channel: Optional[str] = None
    seq: Optional[int] = None
    payload: Any = None
    turn: Optional[str] = None
    reason: Optional[str] = None
    fatal: bool = False

    @classmethod
    def emit(cls, channel: str, seq: int, payload: Any) -> "SessionEvent":
        return cls(kind="emit", channel=channel, seq=seq, payload=payload)

    @classmethod
    def turn_started(cls) -> "SessionEvent":
        return cls(kind="turn", turn="started")

    @classmethod
    def turn_done(cls) -> "SessionEvent":
        return cls(kind="turn", turn="done")

    @classmethod
    def error(cls, reason: str, *, fatal: bool) -> "SessionEvent":
        return cls(kind="error", reason=reason, fatal=fatal)

    @classmethod
    def closed(cls, reason: Optional[str] = None) -> "SessionEvent":
        return cls(kind="closed", reason=reason)

    @property
    def is_emit(self) -> bool:
        return self.kind == "emit"

    @property
    def is_turn(self) -> bool:
        return self.kind == "turn"

    @property
    def is_error(self) -> bool:
        return self.kind == "error"

    @property
    def is_closed(self) -> bool:
        return self.kind == "closed"


class SessionHandle(Protocol):
    """A live session facade shared by local and Temporal backends."""

    def events(self) -> AsyncIterator[SessionEvent]: ...

    async def send(
        self,
        value: Any,
        *,
        channel: Optional[str] = None,
        idempotency_key: Any = None,
    ) -> dict[str, Any]: ...

    async def state(self) -> dict[str, Any]: ...

    async def open_receives(self) -> list[dict[str, Any]]: ...

    async def close(self, reason: Optional[str] = None) -> None: ...


class SessionValidationError(ComposableAgentsError):
    """Raised when a public session constructor receives an unsafe LOOP body."""


def scan(
    step_flow: Node,
    init: object,
    *,
    in_channel: str = "in",
    out_channel: str = "out",
    state_schema: Optional[JSONSchema] = None,
) -> Session[Any, Any]:
    """Wrap ``step_flow`` as the turn body of a session LOOP."""
    loop_node = _loop_node(
        step_flow,
        in_channel=in_channel,
        out_channel=out_channel,
        state_schema=state_schema,
        split=True,
    )
    _raise_on_blocking_session_diagnostics(loop_node)
    return Session(
        body=loop_node,
        init=init,
        in_channel=in_channel,
        out_channel=out_channel,
    )


def loop(
    body: Node,
    *,
    init: object,
    in_channel: str = "in",
    out_channel: str = "out",
    state_schema: Optional[JSONSchema] = None,
) -> Session[Any, Any]:
    """Build a LOOP IR node around an already-authored turn body."""
    loop_node = _loop_node(
        body,
        in_channel=in_channel,
        out_channel=out_channel,
        state_schema=state_schema,
    )
    _raise_on_blocking_session_diagnostics(loop_node)
    return Session(
        body=loop_node,
        init=init,
        in_channel=in_channel,
        out_channel=out_channel,
    )


def _loop_node(
    body: Node,
    *,
    in_channel: str = "in",
    out_channel: str = "out",
    state_schema: Optional[JSONSchema] = None,
    split: bool = False,
) -> Node:
    """Build a LOOP node without running the public construction gate."""
    args = {"split": True} if split else None
    return _node(
        op=Op.LOOP,
        id=_nid("loop"),
        body=body,
        state_schema=state_schema,
        channels=[ChannelRef(in_channel), ChannelRef(out_channel)],
        args=args,
    )


def _raise_on_blocking_session_diagnostics(loop_node: Node) -> None:
    from .validate import blocking, validate

    # Enforce at construction rather than freeze time: deploy.py freezes before
    # validate, and session safety should not perturb that order.
    errors = [
        d
        for d in blocking(validate(loop_node))
        if d.code.startswith("SESSION_")
    ]
    if not errors:
        return
    details = "; ".join(f"{d.code}: {d.message}" for d in errors)
    raise SessionValidationError(f"invalid session LOOP: {details}")


async def drive_session(
    session: Session[I, O],
    *,
    inputs: Iterable[I],
    max_turns: int = 1000,
    env: Optional[InMemoryEnv] = None,
) -> tuple[object, list[O]]:
    """Run a session LOOP over in-memory channel input and collect emissions."""
    messages = list(islice(inputs, max(0, max_turns + 1)))
    if len(messages) > max_turns:
        raise ComposableAgentsError(
            f"session consumed more than {max_turns} messages"
        )
    if env is None:
        env = InMemoryEnv(
            {},
            ProjectionEmitter(InMemoryProjection()),
            inbound={session.in_channel: messages},
        )
    result = await interpret(session.body, session.init, env)
    return result.value, env.emitted(session.out_channel)


class _LiveLocalEnv(InMemoryEnv):
    """Channel-backed in-memory env for a long-lived local session."""

    _WAKE: object = object()

    def __init__(
        self,
        *args: Any,
        event_queue: asyncio.Queue[SessionEvent],
        channel_capacity: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._event_queue = event_queue
        self._live_inbound: dict[str, asyncio.Queue[Any]] = {}
        self._live_emitted: dict[str, list[dict[str, Any]]] = {}
        self._live_seq: dict[str, int] = {}
        self._open_recv: dict[str, int] = {}
        self._capacity = channel_capacity
        self._live_closed = False
        self._turn_started = False

    def _queue(self, channel: str) -> asyncio.Queue[Any]:
        return self._live_inbound.setdefault(channel, asyncio.Queue())

    def close_channels(self) -> None:
        self._live_closed = True
        for queue in self._live_inbound.values():
            queue.put_nowait(self._WAKE)

    def append_live(self, channel: str, value: Any) -> int:
        queue = self._queue(channel)
        seq = self._live_seq.get(f"in:{channel}", 0) + 1
        self._live_seq[f"in:{channel}"] = seq
        queue.put_nowait(value)
        return seq

    async def recv(self, channel: str, cid: str, timeout_s: Optional[int]) -> Any:
        del cid, timeout_s
        queue = self._queue(channel)
        while True:
            if self._live_closed and queue.empty():
                raise SessionClosed(f"session channel {channel!r} is closed")
            self._open_recv[channel] = (
                self._live_seq.get(f"consumed:{channel}", 0) + 1
            )
            try:
                item = await queue.get()
            finally:
                self._open_recv.pop(channel, None)
            if item is self._WAKE:
                if self._live_closed and queue.empty():
                    raise SessionClosed(f"session channel {channel!r} is closed")
                continue
            consumed = self._live_seq.get(f"consumed:{channel}", 0) + 1
            self._live_seq[f"consumed:{channel}"] = consumed
            self._turn_started = True
            await self._event_queue.put(SessionEvent.turn_started())
            return item

    async def emit(self, channel: str, value: Any, cid: str) -> None:
        del cid
        seq = self._live_seq.get(f"out:{channel}", 0) + 1
        self._live_seq[f"out:{channel}"] = seq
        item = {"seq": seq, "payload": value}
        self._live_emitted.setdefault(channel, []).append(item)
        await self._event_queue.put(SessionEvent.emit(channel, seq, value))

    def emitted_records(self) -> dict[str, list[dict[str, Any]]]:
        return {
            channel: [dict(item) for item in items]
            for channel, items in self._live_emitted.items()
        }

    def evict_emit(self, channel: str, seq: Optional[int]) -> None:
        if seq is None:
            return
        self._live_emitted[channel] = [
            item
            for item in self._live_emitted.get(channel, [])
            if int(item.get("seq", 0)) != seq
        ]

    def pending_counts(self) -> dict[str, int]:
        return {
            channel: queue.qsize()
            for channel, queue in self._live_inbound.items()
        }

    def pending_count(self, channel: str) -> int:
        return self._queue(channel).qsize()

    def capacity(self) -> Optional[int]:
        return self._capacity

    def open_receives_records(self) -> list[dict[str, Any]]:
        # cid is deferred to match the current workflow query shape.
        return [
            {"channel": channel, "seq": seq}
            for channel, seq in sorted(self._open_recv.items())
        ]

    def take_turn_started(self) -> bool:
        started = self._turn_started
        self._turn_started = False
        return started


class LocalSessionHandle:
    """In-memory live session handle."""

    def __init__(
        self,
        session: Session[Any, Any],
        env: _LiveLocalEnv,
        *,
        max_turns: int,
        reason: Optional[str] = None,
    ) -> None:
        self._session = session
        self._env = env
        self._events: asyncio.Queue[SessionEvent] = env._event_queue
        self._max_turns = max_turns
        self._carrier = session.init
        self._closed = False
        self._close_reason = reason
        self._done = asyncio.Event()
        self._closed_event_sent = False
        self._driver_exc: Optional[BaseException] = None
        self._events_subscribed = False
        self._idem: dict[str, dict[str, tuple[int, str]]] = {}
        self._driver = asyncio.create_task(self._drive())

    @classmethod
    async def open(
        cls,
        session: Session[Any, Any],
        *,
        tools: Optional[dict[str, Callable[[Any], Any]]] = None,
        reasoners: Optional[dict[str, Callable[[Any], Any]]] = None,
        subs: Optional[dict[str, Callable[[Any], Any]]] = None,
        agents: Optional[dict[str, Callable[[Any], Any]]] = None,
        planners: Optional[dict[str, Callable[[Any], Node]]] = None,
        max_calls: Optional[dict[str, int]] = None,
        mode: EnforcementMode | str = EnforcementMode.STRICT,
        principal: Optional[dict[str, Any]] = None,
        max_turns: int = 100000,
        channel_capacity: Optional[int] = None,
        env: Optional[_LiveLocalEnv] = None,
        manifest: Optional[Any] = None,
    ) -> "LocalSessionHandle":
        if env is None:
            env = _LiveLocalEnv(
                manifest or {},
                ProjectionEmitter(InMemoryProjection()),
                tools=tools,
                reasoners=reasoners,
                subs=subs,
                agents=agents,
                planners=planners,
                max_calls=max_calls,
                mode=mode,
                principal=principal,
                event_queue=asyncio.Queue(),
                channel_capacity=channel_capacity,
            )
        return cls(session, env, max_turns=max_turns)

    async def _drive(self) -> None:
        reason: Optional[str] = None
        turn_body = self._session.body.body
        split_result = bool(
            self._session.body.args and self._session.body.args.get("split") is True
        )
        try:
            if turn_body is None:
                raise ComposableAgentsError("session LOOP missing body")
            for _ in range(self._max_turns):
                try:
                    result = await interpret(turn_body, self._carrier, self._env)
                except SessionClosed:
                    break
                except SessionTurnError as exc:
                    if exc.fatal:
                        raise
                    await self._events.put(SessionEvent.error(str(exc), fatal=False))
                    if self._env.take_turn_started():
                        await self._events.put(SessionEvent.turn_done())
                    continue
                if split_result and isinstance(result.value, tuple) and len(result.value) == 2:
                    self._carrier, output = result.value
                    await self._env.emit(self._session.out_channel, output, result.event_id or "")
                else:
                    self._carrier = result.value
                if self._env.take_turn_started():
                    await self._events.put(SessionEvent.turn_done())
            else:
                raise ComposableAgentsError(
                    f"session consumed more than {self._max_turns} messages"
                )
        except Exception as exc:
            reason = str(exc)
            self._driver_exc = exc
            await self._events.put(SessionEvent.error(reason, fatal=True))
        finally:
            self._closed = True
            self._env.close_channels()
            self._closed_event_sent = True
            await self._events.put(SessionEvent.closed(self._close_reason or reason))
            self._done.set()

    def events(self) -> AsyncIterator[SessionEvent]:
        if self._events_subscribed:
            raise ComposableAgentsError("session events() is single-consumer per handle")
        self._events_subscribed = True

        async def gen() -> AsyncIterator[SessionEvent]:
            while True:
                event = await self._events.get()
                yield event
                if event.is_emit:
                    self._env.evict_emit(event.channel or "", event.seq)
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
        if self._closed:
            raise SessionClosed("session is closed")
        ch = channel or self._session.in_channel

        if idempotency_key is not None:
            key = str(idempotency_key)
            fingerprint = _local_value_fingerprint(value)
            channel_index = self._idem.setdefault(ch, {})
            prior = channel_index.get(key)
            if prior is not None:
                seq, prior_fingerprint = prior
                if prior_fingerprint != fingerprint:
                    raise ComposableAgentsError(
                        f"idempotency_key {key!r} reused with a different payload "
                        f"on channel {ch!r}"
                    )
                return {"seq": seq, "channel": ch}

        capacity = self._env.capacity()
        if capacity is not None and self._env.pending_count(ch) >= capacity:
            raise ComposableAgentsError(f"ChannelFull: channel {ch!r} is full")

        seq = self._env.append_live(ch, value)
        if idempotency_key is not None:
            self._idem.setdefault(ch, {})[str(idempotency_key)] = (
                seq,
                _local_value_fingerprint(value),
            )
        return {"seq": seq, "channel": ch}

    async def state(self) -> dict[str, Any]:
        return {
            "emitted": self._env.emitted_records(),
            "carrier": self._carrier,
            "closed": self._closed,
            "capacity": self._env.capacity(),
            "pending": self._env.pending_counts(),
        }

    async def open_receives(self) -> list[dict[str, Any]]:
        return self._env.open_receives_records()

    async def close(self, reason: Optional[str] = None) -> None:
        self._close_reason = reason
        self._env.close_channels()
        try:
            await asyncio.gather(self._driver, return_exceptions=True)
        finally:
            if not self._done.is_set():
                self._done.set()
