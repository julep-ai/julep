"""In-process coalescing for synchronous reasoner calls.

``SyncCoalescer`` is a small drop-in ``LlmCaller`` wrapper for the synchronous
QoS rungs only. It batches calls that arrive in the same event-loop tick, or
within ``window_s``, by dispatching the underlying caller with ``asyncio.gather``.
Each caller still receives exactly its own reply or exception; the wrapper does
not transform results.

``BATCH`` dispatches are not part of this path. If one reaches the coalescer,
it bypasses the buffer and calls the underlying ``LlmCaller`` directly.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from ..dotctx import Reasoner
from ..qos import ReasonerDispatch, QoSTier
from ..transcript import Transcript
from .effects import LlmCaller, RunPrincipal


_Sleep = Callable[[float], Awaitable[None]]


@dataclass
class _Pending:
    reasoner: Reasoner
    value: Any
    principal: RunPrincipal | None
    transcript: Transcript | None
    dispatch: ReasonerDispatch
    future: asyncio.Future[Any]


class SyncCoalescer:
    """Collect concurrent sync reasoner calls and dispatch them together.

    The default ``window_s=0`` still schedules a flush task and awaits
    ``sleep(0)``, so calls queued in the same event-loop turn are gathered into
    one flush. Positive windows extend that collection period. Reaching
    ``max_batch`` wakes the flush promptly instead of waiting for the full
    window, and surplus buffered items are flushed in later chunks.
    """

    def __init__(
        self,
        caller: LlmCaller,
        *,
        window_s: float = 0.0,
        max_batch: int = 64,
        sleep: _Sleep = asyncio.sleep,
    ) -> None:
        if window_s < 0:
            raise ValueError("window_s must be non-negative")
        if max_batch < 1:
            raise ValueError("max_batch must be at least 1")

        self._caller = caller
        self._window_s = window_s
        self._max_batch = max_batch
        self._sleep = sleep
        self._lock = asyncio.Lock()
        self._pending: list[_Pending] = []
        self._flush_task: asyncio.Task[None] | None = None
        self._flush_now: asyncio.Event | None = None
        self.flushes = 0

    async def call(
        self,
        reasoner: Reasoner,
        value: Any,
        principal: RunPrincipal | None = None,
        transcript: Transcript | None = None,
        dispatch: ReasonerDispatch | None = None,
    ) -> Any:
        """Call the wrapped sync-tier ``LlmCaller`` through the coalescer."""

        if dispatch is None:
            dispatch = ReasonerDispatch()

        if dispatch.qos == QoSTier.BATCH:
            return await self._caller(reasoner, value, principal, transcript, dispatch)

        loop = asyncio.get_running_loop()
        future: asyncio.Future[Any] = loop.create_future()
        item = _Pending(reasoner, value, principal, transcript, dispatch, future)

        async with self._lock:
            self._pending.append(item)
            if self._flush_task is None or self._flush_task.done():
                self._flush_now = asyncio.Event()
                self._flush_task = asyncio.create_task(self._flush_loop())
            if len(self._pending) >= self._max_batch:
                self._wake_flush_locked()

        return await future

    def _wake_flush_locked(self) -> None:
        if self._flush_now is not None:
            self._flush_now.set()

    async def _flush_loop(self) -> None:
        try:
            while True:
                await self._wait_for_window_or_cap()
                batch, had_surplus = await self._take_batch()
                if not batch:
                    return

                self.flushes += 1
                await self._dispatch(batch)

                async with self._lock:
                    if not self._pending:
                        self._flush_task = None
                        self._flush_now = None
                        return
                    if had_surplus or len(self._pending) >= self._max_batch:
                        self._wake_flush_locked()
        except Exception as exc:
            await self._fail_pending(exc)

    async def _wait_for_window_or_cap(self) -> None:
        async with self._lock:
            event = self._flush_now
            at_cap = len(self._pending) >= self._max_batch

        if at_cap or (event is not None and event.is_set()):
            return

        if self._window_s == 0:
            await self._sleep(0.0)
            return

        if event is None:
            await self._sleep(self._window_s)
            return

        sleep_task = asyncio.create_task(self._sleep(self._window_s))
        wake_task = asyncio.create_task(event.wait())
        waiters: set[asyncio.Task[Any]] = {sleep_task, wake_task}
        done, pending = await asyncio.wait(waiters, return_when=asyncio.FIRST_COMPLETED)

        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

        for task in done:
            task.result()

    async def _take_batch(self) -> tuple[list[_Pending], bool]:
        async with self._lock:
            if not self._pending:
                self._flush_task = None
                self._flush_now = None
                return [], False

            batch = self._pending[: self._max_batch]
            del self._pending[: self._max_batch]
            had_surplus = bool(self._pending)
            self._flush_now = asyncio.Event()
            if had_surplus:
                self._wake_flush_locked()
            return batch, had_surplus

    async def _dispatch(self, batch: list[_Pending]) -> None:
        try:
            results = await asyncio.gather(
                *(
                    self._caller(
                        item.reasoner,
                        item.value,
                        item.principal,
                        item.transcript,
                        item.dispatch,
                    )
                    for item in batch
                ),
                return_exceptions=True,
            )
        except Exception as exc:
            for item in batch:
                if not item.future.done():
                    item.future.set_exception(exc)
            raise

        for item, result in zip(batch, results, strict=True):
            if item.future.done():
                continue
            if isinstance(result, BaseException):
                item.future.set_exception(result)
            else:
                item.future.set_result(result)

    async def _fail_pending(self, exc: Exception) -> None:
        async with self._lock:
            pending = self._pending
            self._pending = []
            self._flush_task = None
            self._flush_now = None

        for item in pending:
            if not item.future.done():
                item.future.set_exception(exc)
