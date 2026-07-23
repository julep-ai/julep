from __future__ import annotations

import asyncio
from typing import Any

from julep.dotctx import Reasoner
from julep.execution.coalesce import SyncCoalescer
from julep.qos import ReasonerDispatch, QoSTier
from conftest import run


async def _yield_once(delay: float) -> None:
    del delay
    await asyncio.sleep(0)


def _reasoner() -> Reasoner:
    return Reasoner(name="b", model="m", system="s", reply=None)


def test_coalesce_identical_replies_vs_uncoalesced() -> None:
    async def caller(
        reasoner: Reasoner,
        value: Any,
        principal: dict[str, Any] | None,
        transcript: Any,
        dispatch: ReasonerDispatch,
    ) -> dict[str, Any]:
        del reasoner, principal, transcript
        return {"echo": value, "qos": dispatch.qos.value}

    async def scenario() -> None:
        reasoner = _reasoner()
        coalescer = SyncCoalescer(caller, sleep=_yield_once)
        values = list(range(5))

        results = await asyncio.gather(
            *(coalescer.call(reasoner, value) for value in values)
        )
        expected = await asyncio.gather(
            *(caller(reasoner, value, None, None, ReasonerDispatch()) for value in values)
        )

        assert results == expected
        assert {result["echo"]: result for result in results} == {
            result["echo"]: result for result in expected
        }

    run(scenario())


def test_coalesce_batches_concurrent_calls() -> None:
    seen: list[int] = []

    async def caller(
        reasoner: Reasoner,
        value: int,
        principal: dict[str, Any] | None,
        transcript: Any,
        dispatch: ReasonerDispatch,
    ) -> int:
        del reasoner, principal, transcript, dispatch
        seen.append(value)
        return value

    async def scenario() -> None:
        coalescer = SyncCoalescer(caller, window_s=0.01, sleep=_yield_once)

        results = await asyncio.gather(
            *(coalescer.call(_reasoner(), value) for value in range(4))
        )

        assert results == [0, 1, 2, 3]
        assert sorted(seen) == [0, 1, 2, 3]
        assert coalescer.flushes == 1

    run(scenario())


def test_coalesce_per_item_error_isolation() -> None:
    async def caller(
        reasoner: Reasoner,
        value: str,
        principal: dict[str, Any] | None,
        transcript: Any,
        dispatch: ReasonerDispatch,
    ) -> str:
        del reasoner, principal, transcript, dispatch
        if value == "bad":
            raise ValueError("boom")
        return value

    async def scenario() -> None:
        coalescer = SyncCoalescer(caller, sleep=_yield_once)

        results = await asyncio.gather(
            coalescer.call(_reasoner(), "good1"),
            coalescer.call(_reasoner(), "bad"),
            coalescer.call(_reasoner(), "good2"),
            return_exceptions=True,
        )

        assert results[0] == "good1"
        assert isinstance(results[1], ValueError)
        assert str(results[1]) == "boom"
        assert results[2] == "good2"

    run(scenario())


def test_coalesce_respects_max_batch() -> None:
    async def caller(
        reasoner: Reasoner,
        value: int,
        principal: dict[str, Any] | None,
        transcript: Any,
        dispatch: ReasonerDispatch,
    ) -> int:
        del reasoner, principal, transcript, dispatch
        return value

    async def scenario() -> None:
        coalescer = SyncCoalescer(caller, max_batch=2, sleep=_yield_once)

        results = await asyncio.gather(
            *(coalescer.call(_reasoner(), value) for value in range(5))
        )

        assert results == [0, 1, 2, 3, 4]
        assert coalescer.flushes >= 3

    run(scenario())


def test_coalesce_bypasses_batch_dispatch() -> None:
    seen: list[int] = []

    async def caller(
        reasoner: Reasoner,
        value: int,
        principal: dict[str, Any] | None,
        transcript: Any,
        dispatch: ReasonerDispatch,
    ) -> int:
        del reasoner, principal, transcript
        assert dispatch.qos is QoSTier.BATCH
        seen.append(value)
        return value

    async def scenario() -> None:
        coalescer = SyncCoalescer(caller, sleep=_yield_once)
        batch_dispatch = ReasonerDispatch(qos=QoSTier.BATCH)

        results = await asyncio.gather(
            *(
                coalescer.call(_reasoner(), value, dispatch=batch_dispatch)
                for value in range(2)
            )
        )

        assert results == [0, 1]
        assert seen == [0, 1]
        assert coalescer.flushes == 0

    run(scenario())


def test_coalesce_forwards_tools_per_buffered_call() -> None:
    seen: dict[int, list[dict[str, Any]] | None] = {}

    async def caller(
        reasoner: Reasoner,
        value: int,
        principal: dict[str, Any] | None,
        transcript: Any,
        dispatch: ReasonerDispatch,
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> int:
        del reasoner, principal, transcript, dispatch
        seen[value] = tools
        return value

    async def scenario() -> None:
        coalescer = SyncCoalescer(caller, sleep=_yield_once)
        first = [{"type": "function", "function": {"name": "first"}}]
        second = [{"type": "function", "function": {"name": "second"}}]

        results = await asyncio.gather(
            coalescer(_reasoner(), 1, tools=first),
            coalescer.call(_reasoner(), 2, tools=second),
        )

        assert results == [1, 2]
        assert seen == {1: first, 2: second}
        assert coalescer.flushes == 1

    run(scenario())


def test_coalesce_forwards_tools_on_batch_bypass() -> None:
    seen: list[dict[str, Any]] | None = None

    async def caller(
        reasoner: Reasoner,
        value: int,
        principal: dict[str, Any] | None,
        transcript: Any,
        dispatch: ReasonerDispatch,
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> int:
        nonlocal seen
        del reasoner, principal, transcript
        assert dispatch.qos is QoSTier.BATCH
        seen = tools
        return value

    async def scenario() -> None:
        coalescer = SyncCoalescer(caller, sleep=_yield_once)
        tool_defs = [{"type": "function", "function": {"name": "lookup"}}]

        result = await coalescer.call(
            _reasoner(),
            1,
            dispatch=ReasonerDispatch(qos=QoSTier.BATCH),
            tools=tool_defs,
        )

        assert result == 1
        assert seen == tool_defs
        assert coalescer.flushes == 0

    run(scenario())
