"""dbos>=2.18 API conformance: every dbos API the backend uses, exercised raw.

Needs: ``pip install 'composable-agents[dbos]'`` and a Postgres reachable via
``DBOS_TEST_DATABASE_URL``. Local one-liner:
``docker run -d --name ca-dbos-pg -e POSTGRES_PASSWORD=ca -p 5433:5432 postgres:16``.
Skipped otherwise. If this file fails after a dbos upgrade, fix
``dbos_backend.py`` to match before anything else.
"""

# API corrections vs the plan's draft:
# - Last verified against installed dbos 2.23.0 on 2026-06-09 (constraint:
#   >=2.18).
# - No dbos API name/signature/config-key corrections were needed for the
#   installed package: DBOS.step, DBOS.workflow, DBOS.sleep_async,
#   DBOS.recv_async, DBOS.send_async, DBOS.start_workflow_async,
#   Queue.enqueue_async, WorkflowHandleAsync.get_result, SetWorkflowID, and
#   DBOSConfig(system_database_url=...) all matched the draft.
# - Runtime harness correction: DBOS async methods set the current event loop's
#   default executor to DBOS's executor. Repeated asyncio.run() calls close that
#   executor after the first test, so these tests reuse one module-scoped loop.

from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import Awaitable, Callable, Iterator
from typing import Any
from typing import TypeVar

import pytest

from composable_agents.execution import HAVE_DBOS

DB_URL = os.environ.get("DBOS_TEST_DATABASE_URL")
T = TypeVar("T")
pytestmark = pytest.mark.skipif(
    not HAVE_DBOS or not DB_URL,
    reason="dbos not installed or DBOS_TEST_DATABASE_URL not set",
)

if HAVE_DBOS and DB_URL:
    from dbos import DBOS, DBOSConfig, Queue, SetWorkflowID

    spike_queue = Queue("ca_spike", concurrency=2)

    @DBOS.step(retries_allowed=True, max_attempts=3)
    async def double(x: int) -> int:
        return x * 2

    @DBOS.workflow()
    async def spike_gather(xs: list[int]) -> list[int]:
        # Concurrent steps from one async workflow must be supported.
        return list(await asyncio.gather(*(double(x) for x in xs)))

    @DBOS.workflow()
    async def spike_sleep_recv(timeout_s: float) -> dict[str, Any]:
        await DBOS.sleep_async(0.1)
        msg = await DBOS.recv_async(topic="spike", timeout_seconds=timeout_s)
        return {"msg": msg}


@pytest.fixture(scope="module")
def run_async() -> Iterator[Callable[[Awaitable[T]], T]]:
    loop = asyncio.new_event_loop()

    def run(awaitable: Awaitable[T]) -> T:
        return loop.run_until_complete(awaitable)

    yield run
    loop.close()


@pytest.fixture(scope="module")
def dbos_runtime(run_async: Callable[[Awaitable[Any]], Any]) -> Iterator[None]:
    DBOS(
        config=DBOSConfig(
            name=f"ca-spike-{uuid.uuid4().hex[:8]}",
            system_database_url=DB_URL,
        )
    )
    DBOS.launch()
    yield
    DBOS.destroy()


def test_async_workflow_with_concurrent_steps(
    dbos_runtime: None, run_async: Callable[[Awaitable[list[int]]], list[int]]
) -> None:
    async def main() -> list[int]:
        with SetWorkflowID(f"spike-gather-{uuid.uuid4().hex[:8]}"):
            handle = await DBOS.start_workflow_async(spike_gather, [1, 2, 3, 4])
        return await handle.get_result()

    assert run_async(main()) == [2, 4, 6, 8]


def test_sleep_send_recv(
    dbos_runtime: None, run_async: Callable[[Awaitable[dict[str, Any]]], dict[str, Any]]
) -> None:
    async def main() -> dict[str, Any]:
        wfid = f"spike-recv-{uuid.uuid4().hex[:8]}"
        with SetWorkflowID(wfid):
            handle = await DBOS.start_workflow_async(spike_sleep_recv, 10.0)
        await asyncio.sleep(0.5)
        await DBOS.send_async(wfid, {"ok": True}, topic="spike")
        return await handle.get_result()

    assert run_async(main()) == {"msg": {"ok": True}}


def test_recv_times_out_to_none(
    dbos_runtime: None, run_async: Callable[[Awaitable[dict[str, Any]]], dict[str, Any]]
) -> None:
    async def main() -> dict[str, Any]:
        with SetWorkflowID(f"spike-timeout-{uuid.uuid4().hex[:8]}"):
            handle = await DBOS.start_workflow_async(spike_sleep_recv, 1.0)
        return await handle.get_result()

    assert run_async(main()) == {"msg": None}


def test_queue_enqueue(
    dbos_runtime: None, run_async: Callable[[Awaitable[list[int]]], list[int]]
) -> None:
    async def main() -> list[int]:
        with SetWorkflowID(f"spike-q-{uuid.uuid4().hex[:8]}"):
            handle = await spike_queue.enqueue_async(spike_gather, [5])
        return await handle.get_result()

    assert run_async(main()) == [10]
