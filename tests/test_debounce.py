"""E2E tests for the debounce dispatch helper (Temporal time-skipping server).

Skipped entirely when ``temporalio`` is not installed. Auto time-skipping is
disabled while submissions are in flight so the quiet window cannot fire
between two signals of the same burst; the window is then released with an
explicit ``env.sleep``.
"""

from __future__ import annotations

import asyncio
import uuid

import pytest

from composable_agents import HAVE_TEMPORAL

pytestmark = pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")

if HAVE_TEMPORAL:
    from temporalio.testing import WorkflowEnvironment

    from composable_agents import call, each, freeze, manifest_to_json, mcp
    from composable_agents.contracts import McpAnnotations
    from composable_agents.execution.activities import WorkerContext
    from composable_agents.execution.debounce import submit_debounced
    from composable_agents.execution.worker import build_worker
    from composable_agents.freeze import McpServerSnapshot, McpSnapshot, McpToolSpec


def _snapshot():
    ann = McpAnnotations(read_only_hint=True, idempotent_hint=True)
    return McpSnapshot(servers={"srv": McpServerSnapshot(server="srv", version="1", tools={
        "inc": McpToolSpec(input_schema={}, annotations=ann),
    })})


async def _mcp(server, tool, value, idempotency_key):
    assert tool == "inc"
    return value + 1


def _frozen_each():
    fr = freeze(each(call(mcp("srv", "inc"))), _snapshot())
    return fr.flow.to_json(), manifest_to_json(fr.manifest)


def _worker(env, *, task_queue):
    ctx = WorkerContext(mcp_call=_mcp, llm=None)
    return build_worker(env.client, ctx, task_queue=task_queue)


async def _quiet_window_collates_a_burst(env):
    flow_json, manifest_json = _frozen_each()
    key = f"burst-{uuid.uuid4()}"
    async with _worker(env, task_queue="ca-debounce"):
        with env.auto_time_skipping_disabled():
            handle = None
            for item in (1, 2, 3):
                handle = await submit_debounced(
                    env.client, flow_json, manifest_json,
                    key=key, item=item, quiet_s=600, task_queue="ca-debounce",
                )
            assert sorted(await handle.query("pending")) == [1, 2, 3]
        await env.sleep(601)
        out = await handle.result()
    assert out["items"] == 3, out
    assert out["result"] == [2, 3, 4], out
    assert out["batchId"].endswith(":b0"), out


async def _max_items_fires_without_quiet(env):
    flow_json, manifest_json = _frozen_each()
    key = f"full-{uuid.uuid4()}"
    async with _worker(env, task_queue="ca-debounce-full"):
        with env.auto_time_skipping_disabled():
            for item in (10, 20):
                handle = await submit_debounced(
                    env.client, flow_json, manifest_json,
                    key=key, item=item, quiet_s=600, max_items=2,
                    task_queue="ca-debounce-full",
                )
            out = await handle.result()
    assert out["items"] == 2, out
    assert out["result"] == [11, 21], out


async def _new_batch_after_completion(env):
    flow_json, manifest_json = _frozen_each()
    key = f"reuse-{uuid.uuid4()}"
    async with _worker(env, task_queue="ca-debounce-reuse"):
        first = await submit_debounced(
            env.client, flow_json, manifest_json,
            key=key, item=1, quiet_s=1, max_items=1, task_queue="ca-debounce-reuse",
        )
        assert (await first.result())["result"] == [2]
        second = await submit_debounced(
            env.client, flow_json, manifest_json,
            key=key, item=5, quiet_s=1, max_items=1, task_queue="ca-debounce-reuse",
        )
        out = await second.result()
    assert out["result"] == [6], out


async def _run_all():
    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _quiet_window_collates_a_burst(env)
        await _max_items_fires_without_quiet(env)
        await _new_batch_after_completion(env)


def test_debounce_end_to_end():
    asyncio.run(asyncio.wait_for(_run_all(), timeout=120))
