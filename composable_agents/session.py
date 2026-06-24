"""Local session primitives (cata inside / ana outside, design §4).

A session wraps an ordinary finite turn flow inside an unbounded ``Op.LOOP`` IR
boundary. The interpreter remains the catamorphism over the turn; this module
provides the local in-memory anamorphism that feeds messages in, threads the
carrier, and collects emitted outputs.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Generic, Iterable, Optional, TypeVar

from .dsl import _nid, _node
from .errors import ComposableAgentsError
from .ir import ChannelRef, JSONSchema, Node
from .kinds import Op
from .execution.interpreter import InMemoryEnv, interpret
from .projection import InMemoryProjection, ProjectionEmitter

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
) -> Node:
    """Build a LOOP node without running the public construction gate."""
    return _node(
        op=Op.LOOP,
        id=_nid("loop"),
        body=body,
        state_schema=state_schema,
        channels=[ChannelRef(in_channel), ChannelRef(out_channel)],
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
) -> tuple[object, list[O]]:
    """Run a session LOOP over in-memory channel input and collect emissions."""
    messages = list(inputs)
    if len(messages) > max_turns:
        raise ComposableAgentsError(
            f"session did not park within {max_turns} turns"
        )
    env = InMemoryEnv(
        {},
        ProjectionEmitter(InMemoryProjection()),
        inbound={session.in_channel: messages},
    )
    result = await interpret(session.body, session.init, env)
    return result.value, env.emitted(session.out_channel)
