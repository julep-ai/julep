"""continue-as-new chaining + durable delay, on Temporal's time-skipping server."""
from __future__ import annotations

import asyncio
import uuid

import pytest

from julep import HAVE_TEMPORAL, register_pure
from julep.continuation import continue_with

pytestmark = pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")

if HAVE_TEMPORAL:
    from temporalio.testing import WorkflowEnvironment

    from julep import arr, freeze, manifest_to_json, seq
    from julep.derived import delay
    from julep.execution.activities import WorkerContext
    from julep.execution.harness import run_flow
    from julep.execution.worker import build_worker
    from julep.freeze import McpSnapshot


def _bump_or_finish(value):
    n = value["n"]
    return continue_with({"n": n + 1}) if n < 2 else {"done": n}


register_pure("test.bump_or_finish", _bump_or_finish)


def test_flow_chains_and_sleeps():
    async def main():
        env = await WorkflowEnvironment.start_time_skipping()
        try:
            flow = seq(delay(seconds=300), arr("test.bump_or_finish"))
            frozen = freeze(flow, McpSnapshot())
            worker = build_worker(
                env.client,
                WorkerContext(),
                task_queue="cont-test",
            )
            async with worker:
                out = await run_flow(
                    env.client,
                    frozen.flow.to_json(),
                    manifest_to_json(frozen.manifest),
                    session_id=f"cont-{uuid.uuid4().hex[:8]}",
                    input={"n": 0},
                    task_queue="cont-test",
                )
            assert out == {"done": 2}
        finally:
            await env.shutdown()

    asyncio.run(main())
