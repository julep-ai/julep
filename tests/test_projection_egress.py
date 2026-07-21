"""Temporal failure-injection coverage for projection event egress."""

from __future__ import annotations

import asyncio
import uuid
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

import pytest

from julep import HAVE_TEMPORAL, register_pure
from julep.continuation import continue_with
from julep.errors import JulepError

pytestmark = pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")


def _increment(value: int) -> int:
    return value + 1


def _double(value: int) -> int:
    return value * 2


def _continue_once(value: dict[str, int]) -> Any:
    if value["n"] == 0:
        return continue_with({"n": 1})
    return {"done": value["n"]}


def _fail(_value: Any) -> Any:
    raise JulepError("intentional projection failure")


register_pure("projection_egress.increment", _increment)
register_pure("projection_egress.double", _double)
register_pure("projection_egress.continue_once", _continue_once)
register_pure("projection_egress.fail", _fail)


if HAVE_TEMPORAL:
    from temporalio.client import WorkflowFailureError
    from temporalio.testing import WorkflowEnvironment

    from julep import arr, freeze, manifest_to_json, seq
    from julep.execution.effects import WorkerContext
    from julep.execution.harness import run_flow
    from julep.execution.projection_store import (
        InMemoryExecutionStore,
        set_projection_store,
    )
    from julep.execution.worker import build_worker
    from julep.freeze import McpSnapshot


    def _field(row: dict[str, Any], snake: str, camel: str) -> Any:
        return row[snake] if snake in row else row[camel]


    def _event_identity(row: dict[str, Any]) -> tuple[Any, Any, Any]:
        return (
            _field(row, "workflow_id", "workflowId"),
            _field(row, "segment_seq", "segmentSeq"),
            _field(row, "event_id", "eventId"),
        )


    class RecordingStore(InMemoryExecutionStore):
        def __init__(self) -> None:
            super().__init__()
            self.finalize_calls: list[dict[str, Any]] = []

        def finalize_run(self, **kwargs: Any) -> None:
            self.finalize_calls.append(dict(kwargs))
            super().finalize_run(**kwargs)


    class DoubleInsertStore(RecordingStore):
        """Simulate an activity delivery whose write is applied twice."""

        def insert_events(
            self, events: Sequence[Mapping[str, Any]]
        ) -> None:
            super().insert_events(events)
            super().insert_events(events)


    class FailFirstInsertStore(RecordingStore):
        """A transient database outage on the first batch write."""

        def __init__(self) -> None:
            super().__init__()
            self.insert_attempts = 0

        def insert_events(
            self, events: Sequence[Mapping[str, Any]]
        ) -> None:
            self.insert_attempts += 1
            if self.insert_attempts == 1:
                raise RuntimeError("injected Postgres outage")
            super().insert_events(events)


    async def _execute(
        env: WorkflowEnvironment,
        *,
        flow: Any,
        value: Any,
        store: InMemoryExecutionStore,
        emit_projection: bool = True,
        batch_size: int = 2,
        queue_suffix: str,
    ) -> tuple[str, Any]:
        frozen = freeze(flow, McpSnapshot())
        session_id = f"projection-wf-{queue_suffix}-{uuid.uuid4().hex}"
        run_id = f"projection-run-{queue_suffix}-{uuid.uuid4().hex}"
        task_queue = f"projection-egress-{queue_suffix}-{uuid.uuid4().hex}"
        set_projection_store(store)
        async with build_worker(
            env.client,
            WorkerContext(),
            task_queue=task_queue,
        ):
            result = await run_flow(
                env.client,
                frozen.flow.to_json(),
                manifest_to_json(frozen.manifest),
                session_id=session_id,
                run_id=run_id,
                input=value,
                task_queue=task_queue,
                emit_projection=emit_projection,
                projection_batch_size=batch_size,
                projection_batch_interval_s=0.05,
            )
        return run_id, result


    async def _completed_flow(env: WorkflowEnvironment) -> None:
        store = RecordingStore()
        flow = seq(
            arr("projection_egress.increment"),
            arr("projection_egress.double"),
        )
        run_id, result = await _execute(
            env,
            flow=flow,
            value=2,
            store=store,
            queue_suffix="complete",
        )

        assert result == 6
        run = store.get_run(run_id)
        assert run is not None and run["status"] == "completed"
        rows = store.read_events(run_id, after_seq=0, limit=100)
        # Three successfully evaluated nodes each emit Planned + Did, followed
        # by one transactional terminal marker.
        assert len(rows) == 7
        assert Counter(_field(row, "type", "type") for row in rows) == {
            "Planned": 3,
            "Did": 4,
        }
        assert len({_event_identity(row) for row in rows}) == len(rows)
        assert len(store.finalize_calls) == 1


    async def _continue_as_new_flow(env: WorkflowEnvironment) -> None:
        store = RecordingStore()
        run_id, result = await _execute(
            env,
            flow=arr("projection_egress.continue_once"),
            value={"n": 0},
            store=store,
            batch_size=2,
            queue_suffix="continue",
        )

        assert result == {"done": 1}
        rows = store.read_events(run_id, after_seq=0, limit=100)
        by_segment = Counter(
            _field(row, "segment_seq", "segmentSeq") for row in rows
        )
        assert by_segment == {0: 2, 1: 3}
        assert len({_event_identity(row) for row in rows}) == len(rows)
        # The continue-as-new unwind drains segment zero but must not finalize it.
        assert len(store.finalize_calls) == 1
        assert store.finalize_calls[0]["segment_seq"] == 1


    async def _failed_flow(env: WorkflowEnvironment) -> None:
        store = RecordingStore()
        flow = freeze(arr("projection_egress.fail"), McpSnapshot())
        session_id = f"projection-wf-fail-{uuid.uuid4().hex}"
        run_id = f"projection-run-fail-{uuid.uuid4().hex}"
        task_queue = f"projection-egress-fail-{uuid.uuid4().hex}"
        set_projection_store(store)

        async with build_worker(
            env.client,
            WorkerContext(),
            task_queue=task_queue,
        ):
            with pytest.raises(WorkflowFailureError):
                await run_flow(
                    env.client,
                    flow.flow.to_json(),
                    manifest_to_json(flow.manifest),
                    session_id=session_id,
                    run_id=run_id,
                    input={"x": 1},
                    task_queue=task_queue,
                    emit_projection=True,
                    projection_batch_size=2,
                    projection_batch_interval_s=0.05,
                )

        run = store.get_run(run_id)
        assert run is not None and run["status"] == "failed"
        assert "intentional projection failure" in (run.get("error") or "")
        rows = store.read_events(run_id, after_seq=0, limit=100)
        assert len(rows) == 3
        assert sum(_field(row, "type", "type") == "Failed" for row in rows) == 2
        assert len({_event_identity(row) for row in rows}) == len(rows)
        assert len(store.finalize_calls) == 1


    async def _duplicate_delivery_flow(env: WorkflowEnvironment) -> None:
        store = DoubleInsertStore()
        flow = seq(
            arr("projection_egress.increment"),
            arr("projection_egress.double"),
        )
        run_id, result = await _execute(
            env,
            flow=flow,
            value=3,
            store=store,
            queue_suffix="duplicate",
        )

        assert result == 8
        rows = store.read_events(run_id, after_seq=0, limit=100)
        assert len(rows) == 7
        assert len({_event_identity(row) for row in rows}) == len(rows)


    async def _transient_outage_flow(env: WorkflowEnvironment) -> None:
        store = FailFirstInsertStore()
        flow = seq(
            arr("projection_egress.increment"),
            arr("projection_egress.double"),
        )
        run_id, result = await _execute(
            env,
            flow=flow,
            value=4,
            store=store,
            batch_size=100,
            queue_suffix="outage",
        )

        assert result == 10
        assert store.insert_attempts >= 2
        rows = store.read_events(run_id, after_seq=0, limit=100)
        assert len(rows) == 7
        assert len({_event_identity(row) for row in rows}) == len(rows)


    async def _egress_disabled_flow(env: WorkflowEnvironment) -> None:
        store = RecordingStore()
        run_id, result = await _execute(
            env,
            flow=arr("projection_egress.increment"),
            value=9,
            store=store,
            emit_projection=False,
            queue_suffix="disabled",
        )

        assert result == 10
        assert store.read_events(run_id, after_seq=0, limit=100) == []
        assert store.get_run(run_id) is None
        assert store.finalize_calls == []


    async def _run_all() -> None:
        try:
            env = await WorkflowEnvironment.start_time_skipping()
        except Exception as exc:  # pragma: no cover - depends on download/network
            pytest.skip(f"Temporal test server unavailable: {exc}")

        try:
            await _completed_flow(env)
            await _continue_as_new_flow(env)
            await _failed_flow(env)
            await _duplicate_delivery_flow(env)
            await _transient_outage_flow(env)
            await _egress_disabled_flow(env)
        finally:
            set_projection_store(None)
            await env.shutdown()


def test_projection_egress_end_to_end() -> None:
    asyncio.run(asyncio.wait_for(_run_all(), timeout=180))
