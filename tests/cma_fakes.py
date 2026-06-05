"""Reusable fakes for Claude Managed Agents execution tests."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Any, Optional

from composable_agents.execution.cma import CMAEvent


class FakeCMASession:
    """A scripted CMA session that records tool callbacks and cancellation."""

    def __init__(
        self,
        events: list[CMAEvent],
        *,
        raise_after: Optional[int] = None,
        exc_factory: Callable[[], Exception] = RuntimeError,
    ) -> None:
        self._events = events
        self._raise_after = raise_after
        self._exc_factory = exc_factory
        self.results: list[tuple[str, Any]] = []
        self.errors: list[tuple[str, str]] = []
        self.cancelled = 0

    async def events(self) -> AsyncIterator[CMAEvent]:
        for idx, event in enumerate(self._events):
            if self._raise_after is not None and idx >= self._raise_after:
                raise self._exc_factory()
            yield event
        if self._raise_after is not None and self._raise_after >= len(self._events):
            raise self._exc_factory()

    async def tool_result(self, call_id: str, result: Any) -> None:
        self.results.append((call_id, result))

    async def tool_error(self, call_id: str, reason: str) -> None:
        self.errors.append((call_id, reason))

    async def cancel(self) -> None:
        self.cancelled += 1


class FakeCMAClient:
    """A CMA client fake that returns a prebuilt session and records creation."""

    def __init__(self, session: FakeCMASession) -> None:
        self.session = session
        self.agent: Optional[dict[str, Any]] = None
        self.environment: Any = None
        self.session_cid: Optional[str] = None

    async def create_session(
        self,
        *,
        agent: dict[str, Any],
        environment: Any,
        session_cid: str,
    ) -> FakeCMASession:
        self.agent = agent
        self.environment = environment
        self.session_cid = session_cid
        return self.session
