"""Local session primitives (cata inside / ana outside, design §4).

A session wraps an ordinary finite turn flow inside an unbounded ``Op.LOOP`` IR
boundary. The interpreter remains the catamorphism over the turn; this module
provides the local in-memory anamorphism that feeds messages in, threads the
carrier, and collects emitted outputs.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Generic, Iterable, Optional, TypeVar

from .dsl import _nid, _node
from .errors import ComposableAgentsError
from .ir import ChannelRef, JSONSchema, Node
from .kinds import Op

I = TypeVar("I")
O = TypeVar("O")
T = TypeVar("T")


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


def scan(
    step_flow: Node,
    init: object,
    *,
    in_channel: str = "in",
    out_channel: str = "out",
    state_schema: Optional[JSONSchema] = None,
) -> Session[Any, Any]:
    """Wrap ``step_flow`` as the turn body of a session LOOP."""
    return loop(
        step_flow,
        init=init,
        in_channel=in_channel,
        out_channel=out_channel,
        state_schema=state_schema,
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
    loop_node = _node(
        op=Op.LOOP,
        id=_nid("loop"),
        body=body,
        state_schema=state_schema,
        channels=[ChannelRef(in_channel), ChannelRef(out_channel)],
    )
    return Session(
        body=loop_node,
        init=init,
        in_channel=in_channel,
        out_channel=out_channel,
    )


async def drive_session(
    session: Session[I, O],
    step: Callable[[object, I], Awaitable[tuple[object, O]]],
    *,
    inputs: Iterable[I],
    max_turns: int = 1000,
) -> tuple[object, list[O]]:
    """Local unfold: recv -> turn -> emit -> thread carrier -> park."""
    carrier = session.init
    outs: list[O] = []
    for turn, msg in enumerate(inputs):
        if turn >= max_turns:
            raise ComposableAgentsError(
                f"session did not park within {max_turns} turns"
            )
        carrier, out = await step(carrier, msg)
        outs.append(out)
    return carrier, outs
