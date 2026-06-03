"""Shared deterministic helpers for invariant tests.

The core ``InMemoryEnv`` accepts synchronous handlers today. ``AsyncInMemoryEnv``
keeps the same constructor shape while also awaiting async fake hands, which
lets later concurrency tests express timing and cancellation directly.
"""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass
from typing import Any, Callable, MutableSequence

from composable_agents.execution.interpreter import InMemoryEnv, call_ref_key
from composable_agents.ir import Node


@dataclass(frozen=True)
class RecordedCall:
    """A deterministic record of a fake hand invocation."""

    key: str
    value: Any
    cid: str


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


class AsyncInMemoryEnv(InMemoryEnv):
    """``InMemoryEnv`` variant that accepts sync or async fake handlers."""

    async def call_hand(self, node: Node, value: Any, cid: str) -> Any:
        key = call_ref_key(node, self.manifest)
        fn = self._hands.get(key)
        if fn is None:
            raise KeyError(f"no in-memory hand for {key!r}")
        return await _maybe_await(fn(value))


def slow_ok(delay: float, value: Any) -> Callable[[Any], Any]:
    """Return an async fake hand that resolves to ``value`` after ``delay`` seconds."""

    async def hand(_input: Any) -> Any:
        await asyncio.sleep(delay)
        return value

    return hand


def fast_fail(exc: Exception) -> Callable[[Any], Any]:
    """Return an async fake hand that raises ``exc`` on its next call."""

    async def hand(_input: Any) -> Any:
        raise exc

    return hand


def records_call(
    sink: MutableSequence[RecordedCall],
    *,
    key: str = "hand",
    result: Any = None,
) -> Callable[[Any], Any]:
    """Return a fake hand that appends its input to ``sink`` and returns a value.

    ``result=None`` means the fake echoes its input. A fixed ``key`` can be used
    when the test does not need to route through ``call_ref_key``.
    """

    def hand(value: Any, cid: str = "") -> Any:
        sink.append(RecordedCall(key=key, value=value, cid=cid))
        return value if result is None else result

    return hand
