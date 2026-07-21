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

from julep import HAVE_TEMPORAL

pytestmark = pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")

if HAVE_TEMPORAL:
    from temporalio.testing import WorkflowEnvironment

    from julep import call, each, freeze, manifest_to_json, mcp
    from julep.contracts import McpAnnotations
    from julep.execution.activities import WorkerContext
    from julep.execution.debounce import submit_debounced
    from julep.execution.worker import build_worker
    from julep.freeze import McpServerSnapshot, McpSnapshot, McpToolSpec


BUNDLE_REF = [{"bundleHash": "a" * 64, "signatureDigest": "b" * 64}]


def _snapshot():
    ann = McpAnnotations(read_only_hint=True, idempotent_hint=True)
    return McpSnapshot(servers={"srv": McpServerSnapshot(server="srv", version="1", tools={
        "inc": McpToolSpec(input_schema={}, annotations=ann),
        "slow_inc": McpToolSpec(input_schema={}, annotations=ann),
    })})


async def _mcp(server, tool, value, idempotency_key):
    if tool == "slow_inc":
        await asyncio.sleep(2)  # real time: activities are never time-skipped
        return value + 1
    assert tool == "inc"
    return value + 1


def _frozen_each(tool="inc"):
    fr = freeze(each(call(mcp("srv", tool))), _snapshot())
    return fr.flow.to_json(), manifest_to_json(fr.manifest)


def _worker(env, *, task_queue):
    ctx = WorkerContext(mcp_call=_mcp, llm=None)
    return build_worker(env.client, ctx, task_queue=task_queue)


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_submit_debounced_forwards_bundle_to_start_input():
    captured = {}

    class FakeClient:
        async def start_workflow(self, fn, inp, **kwargs):
            captured["input"] = inp
            captured["kwargs"] = kwargs
            return "handle"

    out = asyncio.run(
        submit_debounced(
            FakeClient(),
            {"op": "id"},
            {},
            key="k",
            item=1,
            quiet_s=1,
            bundle=BUNDLE_REF,
        )
    )

    assert out == "handle"
    assert captured["input"].bundle == BUNDLE_REF


async def _quiet_window_collates_a_burst(env):
    flow_json, manifest_json = _frozen_each()
    key = f"burst-{uuid.uuid4()}"
    async with _worker(env, task_queue="julep-debounce"):
        with env.auto_time_skipping_disabled():
            handle = None
            for item in (1, 2, 3):
                handle = await submit_debounced(
                    env.client, flow_json, manifest_json,
                    key=key, item=item, quiet_s=600, task_queue="julep-debounce",
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
    async with _worker(env, task_queue="julep-debounce-full"):
        with env.auto_time_skipping_disabled():
            for item in (10, 20):
                handle = await submit_debounced(
                    env.client, flow_json, manifest_json,
                    key=key, item=item, quiet_s=600, max_items=2,
                    task_queue="julep-debounce-full",
                )
            out = await handle.result()
    assert out["items"] == 2, out
    assert out["result"] == [11, 21], out


async def _new_batch_after_completion(env):
    flow_json, manifest_json = _frozen_each()
    key = f"reuse-{uuid.uuid4()}"
    async with _worker(env, task_queue="julep-debounce-reuse"):
        first = await submit_debounced(
            env.client, flow_json, manifest_json,
            key=key, item=1, quiet_s=1, max_items=1, task_queue="julep-debounce-reuse",
        )
        assert (await first.result())["result"] == [2]
        second = await submit_debounced(
            env.client, flow_json, manifest_json,
            key=key, item=5, quiet_s=1, max_items=1, task_queue="julep-debounce-reuse",
        )
        out = await second.result()
    assert out["result"] == [6], out


async def _max_items_caps_the_batch_and_carries_surplus(env):
    # The slow child keeps the collector alive while the third item lands, so
    # the surplus deterministically rolls into a continue-as-new segment with
    # its clocks carried (it fires after one window, not two).
    flow_json, manifest_json = _frozen_each("slow_inc")
    key = f"cap-{uuid.uuid4()}"
    async with _worker(env, task_queue="julep-debounce-cap"):
        with env.auto_time_skipping_disabled():
            for item in (1, 2, 3):
                handle = await submit_debounced(
                    env.client, flow_json, manifest_json,
                    key=key, item=item, quiet_s=600, max_items=2,
                    task_queue="julep-debounce-cap",
                )
        await env.sleep(601)
        out = await handle.result()  # follows continue-as-new to the last segment
    assert out["items"] == 1, out
    assert out["result"] == [4], out
    assert out["batchId"].endswith(":b1"), out


async def _run_all():
    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _quiet_window_collates_a_burst(env)
        await _max_items_fires_without_quiet(env)
        await _max_items_caps_the_batch_and_carries_surplus(env)
        await _new_batch_after_completion(env)


def test_debounce_end_to_end():
    asyncio.run(asyncio.wait_for(_run_all(), timeout=120))
