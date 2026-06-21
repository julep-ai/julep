"""Run cross-run brain batching through Anthropic Message Batches on Temporal.

Prereqs (one-time, another terminal):

    temporal server start-dev

Run (source your real keys first):

    source .env
    .venv/bin/python examples/brain_batch_anthropic.py

Watch the runs in the UI: http://localhost:8233.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid

from temporalio.client import Client

from composable_agents import Ann, freeze, manifest_to_json, think
from composable_agents.dotctx import Brain, register_brain
from composable_agents.execution.activities import WorkerContext
from composable_agents.execution.harness import start_flow
from composable_agents.execution.llm import complete_brain
from composable_agents.execution.worker import build_worker
from composable_agents.freeze import McpSnapshot

API_KEY_ENV = "ANTHROPIC_API_KEY"
MODEL = "anthropic:claude-3-5-haiku-latest"
TEMPORAL_HOST = "localhost:7233"
UI = "http://localhost:8233"
RESULT_TIMEOUT_S = 180
N = 4
INPUTS = [
    "I love this!",
    "This is terrible.",
    "It is fine.",
    "Absolutely amazing.",
]


def require_api_key() -> None:
    if os.environ.get(API_KEY_ENV):
        return
    print(f"Missing {API_KEY_ENV}. Run `source .env` or export a real API key first.")
    sys.exit(1)


async def sync_complete_brain(
    brain,
    value,
    principal=None,
    transcript=None,
    dispatch=None,
):
    """Real sync fallback path; the BATCH route uses the provider BatchProvider."""
    del principal

    # complete_brain currently requires any-llm's acompletion as a keyword-only
    # dependency, so this preserves the worker's canonical five-argument seam.
    from any_llm import acompletion

    kwargs = {"acompletion": acompletion, "transcript": transcript}
    if dispatch is not None:
        kwargs["dispatch"] = dispatch
    return await complete_brain(brain, value, **kwargs)


def think_did_from(projection):
    return next(
        event
        for event in projection["events"]
        if event["type"] == "Did" and event["cid"] == "$@1"
    )


async def main() -> None:
    require_api_key()
    assert len(INPUTS) == N

    register_brain(
        Brain(
            name="batch_sentiment",
            model=MODEL,
            system="You are a terse classifier. Reply with one short word.",
            reply_schema=None,
        )
    )

    # This is the exact batchable one-step flow shape used by the E2E tests.
    flow = think("batch_sentiment", ann=Ann(batchable=True))
    frozen = freeze(flow, McpSnapshot())

    client = await Client.connect(TEMPORAL_HOST)
    tq = f"brain-batch-{uuid.uuid4()}"
    ctx = WorkerContext(llm=sync_complete_brain, registry=None)
    worker = build_worker(client, ctx, task_queue=tq)

    print(f"Starting Temporal worker on {TEMPORAL_HOST}; watch {UI}")
    async with worker:
        from composable_agents.execution.brain_batch import (
            BatchDispatchContext,
            get_batch_dispatch_context,
            install_batch_dispatch_context,
        )

        # build_worker installs defaults but does not expose quiet_s/max_wait_s.
        # Reinstall the same client/task queue with a demo-sized flush window.
        install_batch_dispatch_context(
            BatchDispatchContext(
                client=client,
                task_queue=tq,
                quiet_s=2.0,
                max_items=256,
                max_wait_s=30.0,
            )
        )
        batch_ctx = get_batch_dispatch_context()
        print(
            "Batch collector: "
            f"quiet_s={batch_ctx.quiet_s}, max_wait_s={batch_ctx.max_wait_s}, "
            f"task_queue={batch_ctx.task_queue}"
        )

        runs = [(f"brain-batch-{uuid.uuid4()}", input_value) for input_value in INPUTS]
        handles = await asyncio.gather(
            *(
                start_flow(
                    client,
                    frozen.flow.to_json(),
                    manifest_to_json(frozen.manifest),
                    session_id=session_id,
                    input=input_value,
                    task_queue=tq,
                    principal={"qos": "BATCH"},
                )
                for session_id, input_value in runs
            )
        )

        print(
            f"Started {N} runs. Waiting up to {RESULT_TIMEOUT_S}s for results. "
            "Real Batch APIs may take minutes-to-hours; raise RESULT_TIMEOUT_S "
            "if your provider queue is slower."
        )
        results = await asyncio.wait_for(
            asyncio.gather(*(handle.result() for handle in handles)),
            timeout=RESULT_TIMEOUT_S,
        )

        print("\n=== routed replies ===")
        for (session_id, input_value), handle, result in zip(
            runs, handles, results, strict=True
        ):
            projection = await handle.query("projection")
            think_did = think_did_from(projection)
            attrs = think_did["attrs"]
            print(
                f"- {session_id}: input={json.dumps(input_value)} "
                f"reply={json.dumps(result)} "
                f"tier={attrs['tier']} batch_id={attrs.get('batch_id')}"
            )

        assert all(results), "every run should produce a non-empty routed reply"
        print(f"\nPASS: {N} runs produced non-empty routed replies.")


if __name__ == "__main__":
    asyncio.run(main())
