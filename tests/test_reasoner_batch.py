"""Unit tests for cross-run reasoner batch dispatch helpers."""

from __future__ import annotations

import asyncio
import re
import uuid
from typing import Any, Callable, ClassVar

import pytest

from composable_agents import HAVE_TEMPORAL

pytestmark = pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")

if HAVE_TEMPORAL:
    from temporalio import activity, workflow
    from temporalio.testing import WorkflowEnvironment
    from temporalio.worker import Worker

    from composable_agents import Ann, freeze, manifest_to_json, think
    from composable_agents.dotctx import Reasoner, register_reasoner
    from composable_agents.execution.activities import WorkerContext, configure
    from composable_agents.execution.batch_provider import BatchProvider, register_batch_provider
    import composable_agents.execution.reasoner_batch as reasoner_batch
    from composable_agents.execution.reasoner_batch import (
        BatchCollector,
        BatchDispatchContext,
        BatchPoll,
        ReasonerCall,
        FetchBatchResultsInput,
        fetchBatchResults,
        install_batch_dispatch_context,
        pollBatch,
        provider_safe_custom_id,
        submitBatch,
        submit_reasoner_batch,
        submitReasonerBatch,
        SubmitReasonerBatchInput,
        _principal_key,
    )
    from composable_agents.execution.harness import start_flow
    from composable_agents.execution.worker import build_worker
    from composable_agents.freeze import McpSnapshot
    from composable_agents.qos import QoSTier
    from composable_agents.resilience import AttemptRecord
    from test_llm import FakeChoice, FakeCompletion, FakeMessage

    _PROVIDER_CUSTOM_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


    def _expected_provider_custom_id(session: str, segment_seq: int, cid: str) -> str:
        return provider_safe_custom_id(f"{session}:{segment_seq}:{cid}")


    def _assert_provider_custom_id(value: str) -> None:
        assert _PROVIDER_CUSTOM_ID_RE.fullmatch(value)


if HAVE_TEMPORAL:
    @workflow.defn(name="ReasonerBatchReceiver")
    class ReceiverWorkflow:
        def __init__(self) -> None:
            self._inbox: list[dict[str, Any]] = []

        @workflow.signal(name="submitReasonerResult")
        def submit_reasoner_result(self, item: Any) -> None:
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
            reasoner: Any,
            value: Any,
            *,
            transcript: Any = None,
            dispatch: Any = None,
        ) -> dict[str, Any]:
            del reasoner, transcript, dispatch
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


    class BlockingFakeBatch(FakeBatch):
        values: ClassVar[dict[str, Any]] = {}
        requests_by_batch: ClassVar[dict[str, list[dict[str, Any]]]] = {}
        submit_workflow_ids: ClassVar[list[str]] = []
        poll_workflow_ids: ClassVar[list[str]] = []
        release: ClassVar[bool] = False

        @classmethod
        def reset(cls) -> None:
            cls.values.clear()
            cls.requests_by_batch.clear()
            cls.submit_workflow_ids.clear()
            cls.poll_workflow_ids.clear()
            cls.release = False

        async def submit(self, requests: list[dict[str, Any]]) -> str:
            workflow_id = activity.info().workflow_id or ""
            type(self).submit_workflow_ids.append(workflow_id)
            batch_id = f"bx-{len(type(self).submit_workflow_ids)}"
            type(self).requests_by_batch[batch_id] = list(requests)
            return batch_id

        async def poll_status(self, batch_id: str) -> str:
            workflow_id = activity.info().workflow_id or ""
            if workflow_id not in type(self).poll_workflow_ids:
                type(self).poll_workflow_ids.append(workflow_id)
            assert batch_id in type(self).requests_by_batch
            return "completed" if type(self).release else "pending"

        async def results(self, batch_id: str) -> Any:
            assert batch_id in type(self).requests_by_batch
            for request in type(self).requests_by_batch[batch_id]:
                custom_id = str(request["custom_id"])
                value = type(self).values[custom_id]
                yield (
                    custom_id,
                    FakeCompletion(
                        choices=[FakeChoice(FakeMessage(content=str(value)))]
                    ),
                )


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

        def parse(self, raw: Any, reasoner: Any) -> Any:
            del reasoner
            if isinstance(raw, _FakeBatchEntryError):
                raise RuntimeError(f"batch entry {raw.reason}")
            raise RuntimeError("unexpected batch entry")


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_provider_safe_custom_id_contract() -> None:
    raw = "workflow:tenant/$@1:" + ("x" * 100)
    first = provider_safe_custom_id(raw)
    second = provider_safe_custom_id(raw)
    different_session = provider_safe_custom_id("other-session:" + raw)
    same_prefix_different_tail = provider_safe_custom_id(
        "workflow:tenant/$@1:" + ("x" * 100) + ":tail"
    )

    _assert_provider_custom_id(first)
    assert len(first) <= 64
    assert first == second
    assert first != different_session
    assert first != same_prefix_different_tail


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_submit_reasoner_batch_signal_with_starts_keyed_collector() -> None:
    captured = {}

    class FakeClient:
        async def start_workflow(self, fn, inp, **kwargs):  # type: ignore[no-untyped-def]
            captured["fn"] = fn
            captured["input"] = inp
            captured["kwargs"] = kwargs
            return "handle"

    custom_id = _expected_provider_custom_id("r1", 0, "think@1")
    call = ReasonerCall(
        reasoner="b",
        value=1,
        custom_id=custom_id,
        reply_to="r1",
        cid="think@1",
    )

    out = asyncio.run(
        submit_reasoner_batch(
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
    _assert_provider_custom_id(custom_id)
    assert captured["kwargs"]["start_signal_args"][0].custom_id == custom_id
    assert captured["kwargs"]["task_queue"] == "composable-agents"


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_submit_reasoner_batch_activity_uses_installed_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {}

    class FakeClient:
        async def start_workflow(self, fn, inp, **kwargs):  # type: ignore[no-untyped-def]
            captured["fn"] = fn
            captured["input"] = inp
            captured["kwargs"] = kwargs
            return "handle"

    monkeypatch.setattr(reasoner_batch, "_BATCH_CTX", None)
    install_batch_dispatch_context(
        BatchDispatchContext(
            client=FakeClient(),
            quiet_s=2,
            max_items=8,
            max_wait_s=90,
            task_queue="reasoner-batch-test",
        )
    )

    out = asyncio.run(
        submitReasonerBatch(
            SubmitReasonerBatchInput(
                provider="anthropic",
                qos="BATCH",
                principal_key=_principal_key({"storeId": 1}),
                call=ReasonerCall(
                    reasoner="b",
                    value=1,
                    principal={"storeId": 1},
                    custom_id=_expected_provider_custom_id("r1", 0, "think@1"),
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
    assert captured["kwargs"]["task_queue"] == "reasoner-batch-test"


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
    register_reasoner(Reasoner(name="echo_reasoner", model="fake:m", system="", reply_schema=None))

    tq = f"ca-reasoner-batch-{uuid.uuid4()}"
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
        custom_id = _expected_provider_custom_id("run-1", 0, "think@1")
        call = ReasonerCall(
            reasoner="echo_reasoner",
            value=7,
            cid="think@1",
            reply_to="run-1",
            custom_id=custom_id,
        )
        await submit_reasoner_batch(
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
    _assert_provider_custom_id(custom_id)
    assert FakeBatch.requests_by_batch["bx"] == [{"custom_id": custom_id}]


async def _wait_until(
    predicate: Callable[[], bool],
    *,
    timeout_s: float = 10.0,
) -> None:
    deadline = asyncio.get_running_loop().time() + timeout_s
    while not predicate():
        if asyncio.get_running_loop().time() >= deadline:
            raise AssertionError("condition did not become true")
        await asyncio.sleep(0.05)


async def _same_key_fresh_collectors_start_distinct_poll_workflows(
    env: WorkflowEnvironment,
) -> None:
    BlockingFakeBatch.reset()
    register_batch_provider("blockingfake", BlockingFakeBatch)
    reasoner_name = f"blocking_reasoner_{uuid.uuid4().hex}"
    register_reasoner(Reasoner(name=reasoner_name, model="blockingfake:m", system=""))

    tq = f"ca-reasoner-batch-collision-{uuid.uuid4()}"
    principal = {"tenant": "same"}
    collector_id = f"batch:blockingfake:BATCH:{_principal_key(principal)}"

    async with Worker(
        env.client,
        task_queue=tq,
        workflows=[BatchCollector, BatchPoll, ReceiverWorkflow],
        activities=[submitBatch, pollBatch, fetchBatchResults],
    ):
        receiver_a_id = f"receiver-a-{uuid.uuid4()}"
        receiver_b_id = f"receiver-b-{uuid.uuid4()}"
        receiver_a = await env.client.start_workflow(
            ReceiverWorkflow.run,
            id=receiver_a_id,
            task_queue=tq,
        )
        custom_id_a = _expected_provider_custom_id(receiver_a_id, 0, "think@1")
        await submit_reasoner_batch(
            env.client,
            provider="blockingfake",
            qos="BATCH",
            principal=principal,
            call=ReasonerCall(
                reasoner=reasoner_name,
                value="alpha",
                cid="think@1",
                reply_to=receiver_a_id,
                custom_id=custom_id_a,
            ),
            quiet_s=600,
            max_items=1,
            max_wait_s=600,
            task_queue=tq,
        )
        await _wait_until(lambda: len(BlockingFakeBatch.submit_workflow_ids) == 1)
        await env.client.get_workflow_handle(collector_id).terminate(
            reason="force fresh collector run"
        )

        receiver_b = await env.client.start_workflow(
            ReceiverWorkflow.run,
            id=receiver_b_id,
            task_queue=tq,
        )
        custom_id_b = _expected_provider_custom_id(receiver_b_id, 0, "think@1")
        await submit_reasoner_batch(
            env.client,
            provider="blockingfake",
            qos="BATCH",
            principal=principal,
            call=ReasonerCall(
                reasoner=reasoner_name,
                value="beta",
                cid="think@1",
                reply_to=receiver_b_id,
                custom_id=custom_id_b,
            ),
            quiet_s=600,
            max_items=1,
            max_wait_s=600,
            task_queue=tq,
        )
        await _wait_until(lambda: len(BlockingFakeBatch.submit_workflow_ids) == 2)

        assert len(set(BlockingFakeBatch.submit_workflow_ids)) == 2
        assert all(
            workflow_id.startswith(f"{collector_id}:p0:")
            for workflow_id in BlockingFakeBatch.submit_workflow_ids
        )

        BlockingFakeBatch.release = True
        out_a, out_b = await asyncio.gather(receiver_a.result(), receiver_b.result())

    assert out_a == "alpha"
    assert out_b == "beta"
    assert BlockingFakeBatch.requests_by_batch == {
        "bx-1": [{"custom_id": custom_id_a}],
        "bx-2": [{"custom_id": custom_id_b}],
    }


async def _run_all() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _collector_routes_batch_result(env)


async def _run_same_key_fresh_collectors_start_distinct_poll_workflows() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _same_key_fresh_collectors_start_distinct_poll_workflows(env)


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_batch_collector_poll_routes_result_end_to_end() -> None:
    asyncio.run(asyncio.wait_for(_run_all(), timeout=120))


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_same_key_fresh_collectors_start_distinct_poll_workflows() -> None:
    asyncio.run(
        asyncio.wait_for(
            _run_same_key_fresh_collectors_start_distinct_poll_workflows(),
            timeout=120,
        )
    )


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_fetch_batch_results_emits_batch_attempt_record() -> None:
    FakeBatch.values.clear()
    FakeBatch.requests_by_batch.clear()
    register_batch_provider("fakeattempt", FakeBatch)
    reasoner_name = f"batch_attempt_reasoner_{uuid.uuid4().hex}"
    register_reasoner(
        Reasoner(name=reasoner_name, model="fakeattempt:m", system="", reply_schema=None)
    )
    custom_id = "attempt-cid"
    FakeBatch.values[custom_id] = "hello"
    FakeBatch.requests_by_batch["bx"] = [{"custom_id": custom_id}]
    attempts: list[AttemptRecord] = []

    try:
        configure(WorkerContext(on_attempt=attempts.append))
        out = asyncio.run(
            fetchBatchResults(
                FetchBatchResultsInput(
                    provider="fakeattempt",
                    batch_id="bx",
                    calls=[
                        ReasonerCall(
                            reasoner=reasoner_name,
                            value="hello",
                            custom_id=custom_id,
                        )
                    ],
                )
            )
        )
    finally:
        configure(WorkerContext())

    assert out == [{"custom_id": custom_id, "reply": "hello"}]
    assert attempts == [
        AttemptRecord(
            model="fakeattempt:m",
            provider="fakeattempt",
            outcome="ok",
            tier="BATCH",
            batch_id="bx",
        )
    ]


async def _flow_reasoner_rendezvous_through_build_worker(
    env: WorkflowEnvironment,
) -> None:
    FakeBatch.values.clear()
    FakeBatch.requests_by_batch.clear()
    register_batch_provider("fake", FakeBatch)
    reasoner_name = f"batch_reasoner_{uuid.uuid4().hex}"
    register_reasoner(Reasoner(name=reasoner_name, model="fake:m", system="", reply_schema=None))

    flow = think(reasoner_name, ann=Ann(batchable=True))
    frozen = freeze(flow, McpSnapshot())
    tq = f"ca-reasoner-rendezvous-{uuid.uuid4()}"
    llm_calls = 0

    def resolve_qos(
        reasoner: Any,
        ann: Any,
        principal: Any,
        load: Any = None,
    ) -> QoSTier:
        del reasoner, principal, load
        if getattr(ann, "batchable", False):
            return QoSTier.BATCH
        return QoSTier.STANDARD

    async def llm_should_not_run(
        reasoner: Any,
        value: Any,
        principal: Any = None,
        transcript: Any = None,
        dispatch: Any = None,
    ) -> Any:
        nonlocal llm_calls
        del reasoner, value, principal, transcript, dispatch
        llm_calls += 1
        raise AssertionError("BATCH reasoner call fell through to sync LLM")

    ctx = WorkerContext(
        resolve_qos=resolve_qos,
        llm=llm_should_not_run,
        registry=None,
    )
    async with build_worker(env.client, ctx, task_queue=tq):
        sid = f"reasoner-batch-flow-{uuid.uuid4()}"
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
    expected_custom_id = _expected_provider_custom_id(sid, 0, "$@1")
    _assert_provider_custom_id(expected_custom_id)
    assert FakeBatch.requests_by_batch["bx"] == [
        {"custom_id": expected_custom_id}
    ]


async def _two_runs_do_not_misroute(env: WorkflowEnvironment) -> None:
    FakeBatch.values.clear()
    FakeBatch.requests_by_batch.clear()
    register_batch_provider("fake", FakeBatch)
    reasoner_name = f"batch_reasoner_{uuid.uuid4().hex}"
    register_reasoner(Reasoner(name=reasoner_name, model="fake:m", system="", reply_schema=None))

    flow = think(reasoner_name, ann=Ann(batchable=True))
    frozen = freeze(flow, McpSnapshot())
    tq = f"ca-reasoner-rendezvous-{uuid.uuid4()}"
    llm_calls = 0

    def resolve_qos(
        reasoner: Any,
        ann: Any,
        principal: Any,
        load: Any = None,
    ) -> QoSTier:
        del reasoner, principal, load
        if getattr(ann, "batchable", False):
            return QoSTier.BATCH
        return QoSTier.STANDARD

    async def llm_should_not_run(
        reasoner: Any,
        value: Any,
        principal: Any = None,
        transcript: Any = None,
        dispatch: Any = None,
    ) -> Any:
        nonlocal llm_calls
        del reasoner, value, principal, transcript, dispatch
        llm_calls += 1
        raise AssertionError("BATCH reasoner call fell through to sync LLM")

    ctx = WorkerContext(
        resolve_qos=resolve_qos,
        llm=llm_should_not_run,
        registry=None,
    )
    async with build_worker(env.client, ctx, task_queue=tq):
        sid_a = f"reasoner-batch-flow-a-{uuid.uuid4()}"
        sid_b = f"reasoner-batch-flow-b-{uuid.uuid4()}"
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
    custom_id_a = _expected_provider_custom_id(sid_a, 0, "$@1")
    custom_id_b = _expected_provider_custom_id(sid_b, 0, "$@1")
    _assert_provider_custom_id(custom_id_a)
    _assert_provider_custom_id(custom_id_b)
    assert custom_id_a != custom_id_b
    assert custom_id_a in FakeBatch.values
    assert custom_id_b in FakeBatch.values
    assert FakeBatch.values[custom_id_a] == "alpha"
    assert FakeBatch.values[custom_id_b] == "beta"


async def _batch_timeout_promotes_to_sync(env: WorkflowEnvironment) -> None:
    PendingFakeBatch.values.clear()
    PendingFakeBatch.requests_by_batch.clear()
    register_batch_provider("pending", PendingFakeBatch)
    reasoner_name = f"batch_reasoner_{uuid.uuid4().hex}"
    register_reasoner(Reasoner(name=reasoner_name, model="pending:m", system="", reply_schema=None))

    flow = think(reasoner_name, ann=Ann(batchable=True, timeout_s=5))
    frozen = freeze(flow, McpSnapshot())
    tq = f"ca-reasoner-rendezvous-{uuid.uuid4()}"
    llm_calls = 0

    def resolve_qos(
        reasoner: Any,
        ann: Any,
        principal: Any,
        load: Any = None,
        *,
        timeout_s: float | None = None,
        min_batch_window_s: float | None = None,
    ) -> QoSTier:
        del reasoner, principal, load, timeout_s, min_batch_window_s
        if getattr(ann, "batchable", False):
            return QoSTier.BATCH
        return QoSTier.STANDARD

    async def llm_sync_promote(
        reasoner: Any,
        value: Any,
        principal: Any = None,
        transcript: Any = None,
        dispatch: Any = None,
    ) -> Any:
        nonlocal llm_calls
        del reasoner, principal, transcript
        llm_calls += 1
        assert dispatch.qos is QoSTier.STANDARD
        return f"sync:{value}"

    ctx = WorkerContext(
        resolve_qos=resolve_qos,
        llm=llm_sync_promote,
        registry=None,
    )
    async with build_worker(env.client, ctx, task_queue=tq):
        sid = f"reasoner-batch-timeout-{uuid.uuid4()}"
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
    expected_custom_id = _expected_provider_custom_id(sid, 0, "$@1")
    _assert_provider_custom_id(expected_custom_id)
    assert PendingFakeBatch.requests_by_batch["bx"] == [
        {"custom_id": expected_custom_id}
    ]


async def _batch_entry_error_promotes_to_sync(env: WorkflowEnvironment) -> None:
    ErrorFakeBatch.values.clear()
    ErrorFakeBatch.requests_by_batch.clear()
    register_batch_provider("errorfake", ErrorFakeBatch)
    reasoner_name = f"batch_reasoner_{uuid.uuid4().hex}"
    register_reasoner(Reasoner(name=reasoner_name, model="errorfake:m", system="", reply_schema=None))

    flow = think(reasoner_name, ann=Ann(batchable=True, timeout_s=5))
    frozen = freeze(flow, McpSnapshot())
    tq = f"ca-reasoner-rendezvous-{uuid.uuid4()}"
    llm_calls = 0

    def resolve_qos(
        reasoner: Any,
        ann: Any,
        principal: Any,
        load: Any = None,
        *,
        timeout_s: float | None = None,
        min_batch_window_s: float | None = None,
    ) -> QoSTier:
        del reasoner, principal, load, timeout_s, min_batch_window_s
        if getattr(ann, "batchable", False):
            return QoSTier.BATCH
        return QoSTier.STANDARD

    async def llm_sync_promote(
        reasoner: Any,
        value: Any,
        principal: Any = None,
        transcript: Any = None,
        dispatch: Any = None,
    ) -> Any:
        nonlocal llm_calls
        del reasoner, principal, transcript
        llm_calls += 1
        assert dispatch.qos is QoSTier.STANDARD
        return f"sync:{value}"

    ctx = WorkerContext(
        resolve_qos=resolve_qos,
        llm=llm_sync_promote,
        registry=None,
    )
    async with build_worker(env.client, ctx, task_queue=tq):
        sid = f"reasoner-batch-error-{uuid.uuid4()}"
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
    expected_custom_id = _expected_provider_custom_id(sid, 0, "$@1")
    _assert_provider_custom_id(expected_custom_id)
    assert ErrorFakeBatch.requests_by_batch["bx"] == [
        {"custom_id": expected_custom_id}
    ]


async def _whole_batch_failure_promotes_to_sync(env: WorkflowEnvironment) -> None:
    FailedFakeBatch.values.clear()
    FailedFakeBatch.requests_by_batch.clear()
    register_batch_provider("failedfake", FailedFakeBatch)
    reasoner_name = f"batch_reasoner_{uuid.uuid4().hex}"
    register_reasoner(
        Reasoner(name=reasoner_name, model="failedfake:m", system="", reply_schema=None)
    )

    flow = think(reasoner_name, ann=Ann(batchable=True, timeout_s=5))
    frozen = freeze(flow, McpSnapshot())
    tq = f"ca-reasoner-rendezvous-{uuid.uuid4()}"
    llm_calls = 0

    def resolve_qos(
        reasoner: Any,
        ann: Any,
        principal: Any,
        load: Any = None,
        *,
        timeout_s: float | None = None,
        min_batch_window_s: float | None = None,
    ) -> QoSTier:
        del reasoner, principal, load, timeout_s, min_batch_window_s
        if getattr(ann, "batchable", False):
            return QoSTier.BATCH
        return QoSTier.STANDARD

    async def llm_sync_promote(
        reasoner: Any,
        value: Any,
        principal: Any = None,
        transcript: Any = None,
        dispatch: Any = None,
    ) -> Any:
        nonlocal llm_calls
        del reasoner, principal, transcript
        llm_calls += 1
        assert dispatch.qos is QoSTier.STANDARD
        return f"sync:{value}"

    ctx = WorkerContext(
        resolve_qos=resolve_qos,
        llm=llm_sync_promote,
        registry=None,
    )
    async with build_worker(env.client, ctx, task_queue=tq):
        sid = f"reasoner-batch-failed-{uuid.uuid4()}"
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
    expected_custom_id = _expected_provider_custom_id(sid, 0, "$@1")
    _assert_provider_custom_id(expected_custom_id)
    assert FailedFakeBatch.requests_by_batch["bx"] == [
        {"custom_id": expected_custom_id}
    ]


async def _run_flow_rendezvous_all() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _flow_reasoner_rendezvous_through_build_worker(env)


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
def test_flow_reasoner_rendezvous_through_build_worker() -> None:
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
