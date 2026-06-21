from __future__ import annotations

import asyncio
from typing import Any

from composable_agents.dotctx import Brain
from composable_agents.execution.coalesce import SyncCoalescer
from composable_agents.qos import BrainDispatch, QoSTier
from conftest import run


async def _yield_once(delay: float) -> None:
    del delay
    await asyncio.sleep(0)


def _brain() -> Brain:
    return Brain(name="b", model="m", system="s", reply_schema=None)


def test_coalesce_identical_replies_vs_uncoalesced() -> None:
    async def caller(
        brain: Brain,
        value: Any,
        principal: dict[str, Any] | None,
        transcript: Any,
        dispatch: BrainDispatch,
    ) -> dict[str, Any]:
        del brain, principal, transcript
        return {"echo": value, "qos": dispatch.qos.value}

    async def scenario() -> None:
        brain = _brain()
        coalescer = SyncCoalescer(caller, sleep=_yield_once)
        values = list(range(5))

        results = await asyncio.gather(
            *(coalescer.call(brain, value) for value in values)
        )
        expected = await asyncio.gather(
            *(caller(brain, value, None, None, BrainDispatch()) for value in values)
        )

        assert results == expected
        assert {result["echo"]: result for result in results} == {
            result["echo"]: result for result in expected
        }

    run(scenario())


def test_coalesce_batches_concurrent_calls() -> None:
    seen: list[int] = []

    async def caller(
        brain: Brain,
        value: int,
        principal: dict[str, Any] | None,
        transcript: Any,
        dispatch: BrainDispatch,
    ) -> int:
        del brain, principal, transcript, dispatch
        seen.append(value)
        return value

    async def scenario() -> None:
        coalescer = SyncCoalescer(caller, window_s=0.01, sleep=_yield_once)

        results = await asyncio.gather(
            *(coalescer.call(_brain(), value) for value in range(4))
        )

        assert results == [0, 1, 2, 3]
        assert sorted(seen) == [0, 1, 2, 3]
        assert coalescer.flushes == 1

    run(scenario())


def test_coalesce_per_item_error_isolation() -> None:
    async def caller(
        brain: Brain,
        value: str,
        principal: dict[str, Any] | None,
        transcript: Any,
        dispatch: BrainDispatch,
    ) -> str:
        del brain, principal, transcript, dispatch
        if value == "bad":
            raise ValueError("boom")
        return value

    async def scenario() -> None:
        coalescer = SyncCoalescer(caller, sleep=_yield_once)

        results = await asyncio.gather(
            coalescer.call(_brain(), "good1"),
            coalescer.call(_brain(), "bad"),
            coalescer.call(_brain(), "good2"),
            return_exceptions=True,
        )

        assert results[0] == "good1"
        assert isinstance(results[1], ValueError)
        assert str(results[1]) == "boom"
        assert results[2] == "good2"

    run(scenario())


def test_coalesce_respects_max_batch() -> None:
    async def caller(
        brain: Brain,
        value: int,
        principal: dict[str, Any] | None,
        transcript: Any,
        dispatch: BrainDispatch,
    ) -> int:
        del brain, principal, transcript, dispatch
        return value

    async def scenario() -> None:
        coalescer = SyncCoalescer(caller, max_batch=2, sleep=_yield_once)

        results = await asyncio.gather(
            *(coalescer.call(_brain(), value) for value in range(5))
        )

        assert results == [0, 1, 2, 3, 4]
        assert coalescer.flushes >= 3

    run(scenario())


def test_coalesce_bypasses_batch_dispatch() -> None:
    seen: list[int] = []

    async def caller(
        brain: Brain,
        value: int,
        principal: dict[str, Any] | None,
        transcript: Any,
        dispatch: BrainDispatch,
    ) -> int:
        del brain, principal, transcript
        assert dispatch.qos is QoSTier.BATCH
        seen.append(value)
        return value

    async def scenario() -> None:
        coalescer = SyncCoalescer(caller, sleep=_yield_once)
        batch_dispatch = BrainDispatch(qos=QoSTier.BATCH)

        results = await asyncio.gather(
            *(
                coalescer.call(_brain(), value, dispatch=batch_dispatch)
                for value in range(2)
            )
        )

        assert results == [0, 1]
        assert seen == [0, 1]
        assert coalescer.flushes == 0

    run(scenario())
