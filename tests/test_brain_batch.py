"""Unit tests for cross-run brain batch dispatch helpers."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, ClassVar

import pytest

from composable_agents import HAVE_TEMPORAL

pytestmark = pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")

if HAVE_TEMPORAL:
    from temporalio import workflow
    from temporalio.testing import WorkflowEnvironment
    from temporalio.worker import Worker

    from composable_agents import Ann, freeze, manifest_to_json, think
    from composable_agents.dotctx import Brain, register_brain
    from composable_agents.execution.activities import WorkerContext
    from composable_agents.execution.batch_provider import BatchProvider, register_batch_provider
    import composable_agents.execution.brain_batch as brain_batch
    from composable_agents.execution.brain_batch import (
        BatchCollector,
        BatchDispatchContext,
        BatchPoll,
        BrainCall,
        fetchBatchResults,
        install_batch_dispatch_context,
        pollBatch,
        submitBatch,
        submit_brain_batch,
        submitBrainBatch,
        SubmitBrainBatchInput,
        _principal_key,
    )
    from composable_agents.execution.harness import start_flow
    from composable_agents.execution.worker import build_worker
    from composable_agents.freeze import McpSnapshot
    from composable_agents.qos import QoSTier
    from test_llm import FakeChoice, FakeCompletion, FakeMessage


if HAVE_TEMPORAL:
    @workflow.defn(name="BrainBatchReceiver")
    class ReceiverWorkflow:
        def __init__(self) -> None:
            self._inbox: list[dict[str, Any]] = []

        @workflow.signal(name="submitBrainResult")
        def submit_brain_result(self, item: Any) -> None:
            self._inbox.append(dict(item))

        @workflow.run
        async def run(self) -> Any:
            await workflow.wait_condition(lambda: bool(self._inbox))
            reply = self._inbox[0]["reply"]
            if isinstance(reply, dict) and "__ca_meta__" in reply:
                return reply["reply"]
            return reply


    class FakeBatch(BatchProvider):
        values: ClassVar[dict[str, Any]] = {}
        requests_by_batch: ClassVar[dict[str, list[dict[str, Any]]]] = {}

        def build_request(
            self,
            custom_id: str,
            brain: Any,
            value: Any,
            *,
            transcript: Any = None,
            dispatch: Any = None,
        ) -> dict[str, Any]:
            del brain, transcript, dispatch
            type(self).values[custom_id] = value
            return {"custom_id": custom_id}

        async def submit(self, requests: list[dict[str, Any]]) -> str:
            type(self).requests_by_batch["bx"] = list(requests)
            return "bx"

        async def poll_status(self, batch_id: str) -> str:
            assert batch_id == "bx"
            return "completed"

        async def results(self, batch_id: str) -> Any:
            assert batch_id == "bx"
            for request in type(self).requests_by_batch[batch_id]:
                custom_id = str(request["custom_id"])
                value = type(self).values[custom_id]
                yield (
                    custom_id,
                    FakeCompletion(
                        choices=[FakeChoice(FakeMessage(content=str(value)))]
                    ),
                )


    class PendingFakeBatch(FakeBatch):
        values: ClassVar[dict[str, Any]] = {}
        requests_by_batch: ClassVar[dict[str, list[dict[str, Any]]]] = {}

        async def poll_status(self, batch_id: str) -> str:
            assert batch_id == "bx"
            return "pending"


    class FailedFakeBatch(FakeBatch):
        values: ClassVar[dict[str, Any]] = {}
        requests_by_batch: ClassVar[dict[str, list[dict[str, Any]]]] = {}

        async def poll_status(self, batch_id: str) -> str:
            assert batch_id == "bx"
            return "failed"


    class _FakeBatchEntryError:
        def __init__(self, reason: str) -> None:
            self.reason = reason


    class ErrorFakeBatch(FakeBatch):
        values: ClassVar[dict[str, Any]] = {}
        requests_by_batch: ClassVar[dict[str, list[dict[str, Any]]]] = {}

        async def results(self, batch_id: str) -> Any:
            assert batch_id == "bx"
            for request in type(self).requests_by_batch[batch_id]:
                yield (str(request["custom_id"]), _FakeBatchEntryError("expired"))

        def parse(self, raw: Any, brain: Any) -> Any:
            del brain
            if isinstance(raw, _FakeBatchEntryError):
                raise RuntimeError(f"batch entry {raw.reason}")
            raise RuntimeError("unexpected batch entry")


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_submit_brain_batch_signal_with_starts_keyed_collector() -> None:
    captured = {}

    class FakeClient:
        async def start_workflow(self, fn, inp, **kwargs):  # type: ignore[no-untyped-def]
            captured["fn"] = fn
            captured["input"] = inp
            captured["kwargs"] = kwargs
            return "handle"

    call = BrainCall(
        brain="b",
        value=1,
        custom_id="r1:think@1",
        reply_to="r1",
        cid="think@1",
    )

    out = asyncio.run(
        submit_brain_batch(
            FakeClient(),
            provider="anthropic",
            qos="BATCH",
            principal={"storeId": 1},
            call=call,
            quiet_s=1,
            max_items=10,
            max_wait_s=60,
        )
    )

    assert out == "handle"
    assert captured["fn"] == "BatchCollector"
    assert captured["input"].provider == "anthropic"
    assert captured["input"].qos == "BATCH"
    assert captured["input"].principal == {"storeId": 1}
    assert captured["kwargs"]["id"] == (
        f"batch:anthropic:BATCH:{_principal_key({'storeId': 1})}"
    )
    assert captured["kwargs"]["start_signal"] == "submit"
    assert captured["kwargs"]["start_signal_args"][0].custom_id == "r1:think@1"
    assert captured["kwargs"]["task_queue"] == "composable-agents"


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_submit_brain_batch_activity_uses_installed_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {}

    class FakeClient:
        async def start_workflow(self, fn, inp, **kwargs):  # type: ignore[no-untyped-def]
            captured["fn"] = fn
            captured["input"] = inp
            captured["kwargs"] = kwargs
            return "handle"

    monkeypatch.setattr(brain_batch, "_BATCH_CTX", None)
    install_batch_dispatch_context(
        BatchDispatchContext(
            client=FakeClient(),
            quiet_s=2,
            max_items=8,
            max_wait_s=90,
            task_queue="brain-batch-test",
        )
    )

    out = asyncio.run(
        submitBrainBatch(
            SubmitBrainBatchInput(
                provider="anthropic",
                qos="BATCH",
                principal_key=_principal_key({"storeId": 1}),
                call=BrainCall(
                    brain="b",
                    value=1,
                    principal={"storeId": 1},
                    custom_id="r1:think@1",
                    reply_to="r1",
                    cid="think@1",
                ),
            )
        )
    )

    assert out is None
    assert captured["fn"] == "BatchCollector"
    assert captured["input"].quiet_s == 2
    assert captured["input"].max_items == 8
    assert captured["input"].max_wait_s == 90
    assert captured["kwargs"]["task_queue"] == "brain-batch-test"


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_principal_key_empty_for_none_and_stable_for_dict() -> None:
    first = _principal_key({"b": 2, "a": 1})
    second = _principal_key({"a": 1, "b": 2})

    assert _principal_key(None) == ""
    assert first == second


async def _collector_routes_batch_result(env: WorkflowEnvironment) -> None:
    FakeBatch.values.clear()
    FakeBatch.requests_by_batch.clear()
    register_batch_provider("fake", FakeBatch)
    register_brain(Brain(name="echo_brain", model="fake:m", system="", reply_schema=None))

    tq = f"ca-brain-batch-{uuid.uuid4()}"
    async with Worker(
        env.client,
        task_queue=tq,
        workflows=[BatchCollector, BatchPoll, ReceiverWorkflow],
        activities=[submitBatch, pollBatch, fetchBatchResults],
    ):
        receiver = await env.client.start_workflow(
            ReceiverWorkflow.run,
            id="run-1",
            task_queue=tq,
        )
        call = BrainCall(
            brain="echo_brain",
            value=7,
            cid="think@1",
            reply_to="run-1",
            custom_id="run-1:think@1",
        )
        await submit_brain_batch(
            env.client,
            provider="fake",
            qos="BATCH",
            principal=None,
            call=call,
            quiet_s=600,
            max_items=1,
            max_wait_s=600,
            task_queue=tq,
        )

        out = await receiver.result()

    assert out == "7"
    assert FakeBatch.requests_by_batch["bx"] == [{"custom_id": "run-1:think@1"}]


async def _run_all() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _collector_routes_batch_result(env)


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_batch_collector_poll_routes_result_end_to_end() -> None:
    asyncio.run(asyncio.wait_for(_run_all(), timeout=120))


async def _flow_brain_rendezvous_through_build_worker(
    env: WorkflowEnvironment,
) -> None:
    FakeBatch.values.clear()
    FakeBatch.requests_by_batch.clear()
    register_batch_provider("fake", FakeBatch)
    brain_name = f"batch_brain_{uuid.uuid4().hex}"
    register_brain(Brain(name=brain_name, model="fake:m", system="", reply_schema=None))

    flow = think(brain_name, ann=Ann(batchable=True))
    frozen = freeze(flow, McpSnapshot())
    tq = f"ca-brain-rendezvous-{uuid.uuid4()}"
    llm_calls = 0

    def resolve_qos(
        brain: Any,
        ann: Any,
        principal: Any,
        load: Any = None,
    ) -> QoSTier:
        del brain, principal, load
        if getattr(ann, "batchable", False):
            return QoSTier.BATCH
        return QoSTier.STANDARD

    async def llm_should_not_run(
        brain: Any,
        value: Any,
        principal: Any = None,
        transcript: Any = None,
        dispatch: Any = None,
    ) -> Any:
        nonlocal llm_calls
        del brain, value, principal, transcript, dispatch
        llm_calls += 1
        raise AssertionError("BATCH brain call fell through to sync LLM")

    ctx = WorkerContext(
        resolve_qos=resolve_qos,
        llm=llm_should_not_run,
        registry=None,
    )
    async with build_worker(env.client, ctx, task_queue=tq):
        sid = f"brain-batch-flow-{uuid.uuid4()}"
        handle = await start_flow(
            env.client,
            frozen.flow.to_json(),
            manifest_to_json(frozen.manifest),
            session_id=sid,
            input="slice3",
            task_queue=tq,
        )
        out = await handle.result()
        projection = await handle.query("projection")

    assert llm_calls == 0
    assert out == "slice3"
    think_did = next(
        event
        for event in projection["events"]
        if event["type"] == "Did" and event["cid"] == "$@1"
    )
    assert think_did["attrs"]["tier"] == "BATCH"
    assert think_did["attrs"]["batch_id"]
    assert FakeBatch.requests_by_batch["bx"] == [
        {"custom_id": f"{sid}:0:$@1"}
    ]


async def _two_runs_do_not_misroute(env: WorkflowEnvironment) -> None:
    FakeBatch.values.clear()
    FakeBatch.requests_by_batch.clear()
    register_batch_provider("fake", FakeBatch)
    brain_name = f"batch_brain_{uuid.uuid4().hex}"
    register_brain(Brain(name=brain_name, model="fake:m", system="", reply_schema=None))

    flow = think(brain_name, ann=Ann(batchable=True))
    frozen = freeze(flow, McpSnapshot())
    tq = f"ca-brain-rendezvous-{uuid.uuid4()}"
    llm_calls = 0

    def resolve_qos(
        brain: Any,
        ann: Any,
        principal: Any,
        load: Any = None,
    ) -> QoSTier:
        del brain, principal, load
        if getattr(ann, "batchable", False):
            return QoSTier.BATCH
        return QoSTier.STANDARD

    async def llm_should_not_run(
        brain: Any,
        value: Any,
        principal: Any = None,
        transcript: Any = None,
        dispatch: Any = None,
    ) -> Any:
        nonlocal llm_calls
        del brain, value, principal, transcript, dispatch
        llm_calls += 1
        raise AssertionError("BATCH brain call fell through to sync LLM")

    ctx = WorkerContext(
        resolve_qos=resolve_qos,
        llm=llm_should_not_run,
        registry=None,
    )
    async with build_worker(env.client, ctx, task_queue=tq):
        sid_a = f"brain-batch-flow-a-{uuid.uuid4()}"
        sid_b = f"brain-batch-flow-b-{uuid.uuid4()}"
        handle_a, handle_b = await asyncio.gather(
            start_flow(
                env.client,
                frozen.flow.to_json(),
                manifest_to_json(frozen.manifest),
                session_id=sid_a,
                input="alpha",
                task_queue=tq,
            ),
            start_flow(
                env.client,
                frozen.flow.to_json(),
                manifest_to_json(frozen.manifest),
                session_id=sid_b,
                input="beta",
                task_queue=tq,
            ),
        )
        out_a = await handle_a.result()
        out_b = await handle_b.result()

    assert llm_calls == 0
    assert out_a == "alpha"
    assert out_b == "beta"
    custom_id_a = f"{sid_a}:0:$@1"
    custom_id_b = f"{sid_b}:0:$@1"
    assert custom_id_a != custom_id_b
    assert custom_id_a in FakeBatch.values
    assert custom_id_b in FakeBatch.values
    assert FakeBatch.values[custom_id_a] == "alpha"
    assert FakeBatch.values[custom_id_b] == "beta"


async def _batch_timeout_promotes_to_sync(env: WorkflowEnvironment) -> None:
    PendingFakeBatch.values.clear()
    PendingFakeBatch.requests_by_batch.clear()
    register_batch_provider("pending", PendingFakeBatch)
    brain_name = f"batch_brain_{uuid.uuid4().hex}"
    register_brain(Brain(name=brain_name, model="pending:m", system="", reply_schema=None))

    flow = think(brain_name, ann=Ann(batchable=True, timeout_s=5))
    frozen = freeze(flow, McpSnapshot())
    tq = f"ca-brain-rendezvous-{uuid.uuid4()}"
    llm_calls = 0

    def resolve_qos(
        brain: Any,
        ann: Any,
        principal: Any,
        load: Any = None,
        *,
        timeout_s: float | None = None,
        min_batch_window_s: float | None = None,
    ) -> QoSTier:
        del brain, principal, load, timeout_s, min_batch_window_s
        if getattr(ann, "batchable", False):
            return QoSTier.BATCH
        return QoSTier.STANDARD

    async def llm_sync_promote(
        brain: Any,
        value: Any,
        principal: Any = None,
        transcript: Any = None,
        dispatch: Any = None,
    ) -> Any:
        nonlocal llm_calls
        del brain, principal, transcript
        llm_calls += 1
        assert dispatch.qos is QoSTier.STANDARD
        return f"sync:{value}"

    ctx = WorkerContext(
        resolve_qos=resolve_qos,
        llm=llm_sync_promote,
        registry=None,
    )
    async with build_worker(env.client, ctx, task_queue=tq):
        sid = f"brain-batch-timeout-{uuid.uuid4()}"
        handle = await start_flow(
            env.client,
            frozen.flow.to_json(),
            manifest_to_json(frozen.manifest),
            session_id=sid,
            input="slice3",
            task_queue=tq,
        )
        out = await handle.result()
        projection = await handle.query("projection")

    assert out == "sync:slice3"
    assert llm_calls == 1
    think_did = next(
        event
        for event in projection["events"]
        if event["type"] == "Did" and event["cid"] == "$@1"
    )
    assert think_did["attrs"]["tier"] == "STANDARD"
    assert think_did["attrs"]["promoted"] is True
    assert think_did["attrs"]["reason"] == "batch_timeout"
    assert PendingFakeBatch.requests_by_batch["bx"] == [
        {"custom_id": f"{sid}:0:$@1"}
    ]


async def _batch_entry_error_promotes_to_sync(env: WorkflowEnvironment) -> None:
    ErrorFakeBatch.values.clear()
    ErrorFakeBatch.requests_by_batch.clear()
    register_batch_provider("errorfake", ErrorFakeBatch)
    brain_name = f"batch_brain_{uuid.uuid4().hex}"
    register_brain(Brain(name=brain_name, model="errorfake:m", system="", reply_schema=None))

    flow = think(brain_name, ann=Ann(batchable=True, timeout_s=5))
    frozen = freeze(flow, McpSnapshot())
    tq = f"ca-brain-rendezvous-{uuid.uuid4()}"
    llm_calls = 0

    def resolve_qos(
        brain: Any,
        ann: Any,
        principal: Any,
        load: Any = None,
        *,
        timeout_s: float | None = None,
        min_batch_window_s: float | None = None,
    ) -> QoSTier:
        del brain, principal, load, timeout_s, min_batch_window_s
        if getattr(ann, "batchable", False):
            return QoSTier.BATCH
        return QoSTier.STANDARD

    async def llm_sync_promote(
        brain: Any,
        value: Any,
        principal: Any = None,
        transcript: Any = None,
        dispatch: Any = None,
    ) -> Any:
        nonlocal llm_calls
        del brain, principal, transcript
        llm_calls += 1
        assert dispatch.qos is QoSTier.STANDARD
        return f"sync:{value}"

    ctx = WorkerContext(
        resolve_qos=resolve_qos,
        llm=llm_sync_promote,
        registry=None,
    )
    async with build_worker(env.client, ctx, task_queue=tq):
        sid = f"brain-batch-error-{uuid.uuid4()}"
        handle = await start_flow(
            env.client,
            frozen.flow.to_json(),
            manifest_to_json(frozen.manifest),
            session_id=sid,
            input="slice3",
            task_queue=tq,
        )
        out = await handle.result()
        projection = await handle.query("projection")

    assert out == "sync:slice3"
    assert llm_calls == 1
    think_did = next(
        event
        for event in projection["events"]
        if event["type"] == "Did" and event["cid"] == "$@1"
    )
    assert think_did["attrs"]["tier"] == "STANDARD"
    assert think_did["attrs"]["promoted"] is True
    assert think_did["attrs"]["reason"] == "batch_error"
    assert ErrorFakeBatch.requests_by_batch["bx"] == [
        {"custom_id": f"{sid}:0:$@1"}
    ]


async def _whole_batch_failure_promotes_to_sync(env: WorkflowEnvironment) -> None:
    FailedFakeBatch.values.clear()
    FailedFakeBatch.requests_by_batch.clear()
    register_batch_provider("failedfake", FailedFakeBatch)
    brain_name = f"batch_brain_{uuid.uuid4().hex}"
    register_brain(
        Brain(name=brain_name, model="failedfake:m", system="", reply_schema=None)
    )

    flow = think(brain_name, ann=Ann(batchable=True, timeout_s=5))
    frozen = freeze(flow, McpSnapshot())
    tq = f"ca-brain-rendezvous-{uuid.uuid4()}"
    llm_calls = 0

    def resolve_qos(
        brain: Any,
        ann: Any,
        principal: Any,
        load: Any = None,
        *,
        timeout_s: float | None = None,
        min_batch_window_s: float | None = None,
    ) -> QoSTier:
        del brain, principal, load, timeout_s, min_batch_window_s
        if getattr(ann, "batchable", False):
            return QoSTier.BATCH
        return QoSTier.STANDARD

    async def llm_sync_promote(
        brain: Any,
        value: Any,
        principal: Any = None,
        transcript: Any = None,
        dispatch: Any = None,
    ) -> Any:
        nonlocal llm_calls
        del brain, principal, transcript
        llm_calls += 1
        assert dispatch.qos is QoSTier.STANDARD
        return f"sync:{value}"

    ctx = WorkerContext(
        resolve_qos=resolve_qos,
        llm=llm_sync_promote,
        registry=None,
    )
    async with build_worker(env.client, ctx, task_queue=tq):
        sid = f"brain-batch-failed-{uuid.uuid4()}"
        handle = await start_flow(
            env.client,
            frozen.flow.to_json(),
            manifest_to_json(frozen.manifest),
            session_id=sid,
            input="slice3",
            task_queue=tq,
        )
        out = await handle.result()
        projection = await handle.query("projection")

    assert out == "sync:slice3"
    assert llm_calls == 1
    think_did = next(
        event
        for event in projection["events"]
        if event["type"] == "Did" and event["cid"] == "$@1"
    )
    assert think_did["attrs"]["tier"] == "STANDARD"
    assert think_did["attrs"]["promoted"] is True
    assert think_did["attrs"]["reason"] == "batch_failed"
    assert FailedFakeBatch.requests_by_batch["bx"] == [
        {"custom_id": f"{sid}:0:$@1"}
    ]


async def _run_flow_rendezvous_all() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _flow_brain_rendezvous_through_build_worker(env)


async def _run_two_runs_do_not_misroute() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _two_runs_do_not_misroute(env)


async def _run_batch_timeout_promotes_to_sync() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _batch_timeout_promotes_to_sync(env)


async def _run_batch_entry_error_promotes_to_sync() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _batch_entry_error_promotes_to_sync(env)


async def _run_whole_batch_failure_promotes_to_sync() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _whole_batch_failure_promotes_to_sync(env)


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_flow_brain_rendezvous_through_build_worker() -> None:
    asyncio.run(asyncio.wait_for(_run_flow_rendezvous_all(), timeout=120))


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_two_runs_do_not_misroute() -> None:
    asyncio.run(asyncio.wait_for(_run_two_runs_do_not_misroute(), timeout=120))


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_batch_timeout_promotes_to_sync() -> None:
    asyncio.run(asyncio.wait_for(_run_batch_timeout_promotes_to_sync(), timeout=120))


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_batch_entry_error_promotes_to_sync() -> None:
    asyncio.run(
        asyncio.wait_for(_run_batch_entry_error_promotes_to_sync(), timeout=120)
    )


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_whole_batch_failure_promotes_to_sync() -> None:
    asyncio.run(
        asyncio.wait_for(_run_whole_batch_failure_promotes_to_sync(), timeout=120)
    )
