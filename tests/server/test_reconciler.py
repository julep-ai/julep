from __future__ import annotations

import asyncio

from julep.execution.projection_store import InMemoryExecutionStore
from julep.server.routes.runs import reconcile_runs_once

from .conftest import FakeTemporalGateway


def _submitting(store: InMemoryExecutionStore, run_id: str) -> str:
    workflow_id = f"run-{run_id}"
    assert store.create_run(
        run_id=run_id,
        idempotency_key=f"idem-{run_id}",
        workflow_id=workflow_id,
        session_id=workflow_id,
        release_hash="sha256:" + "a" * 64,
        pipeline="summary",
        application="memory",
        principal={"key": "alice"},
        input_ref=None,
        started_at=1.0,
    ) == "created"
    return workflow_id


def test_reconciler_resolves_submitting_orphans_idempotently() -> None:
    missing_store = InMemoryExecutionStore()
    missing_gateway = FakeTemporalGateway()
    missing_workflow = _submitting(missing_store, "missing")
    missing_gateway.descriptions[missing_workflow] = "not_found"

    asyncio.run(reconcile_runs_once(missing_store, missing_gateway))
    missing = missing_store.get_run("missing")
    assert missing is not None
    assert missing["status"] == "start_failed"
    assert missing["finished_at"] is not None
    asyncio.run(reconcile_runs_once(missing_store, missing_gateway))
    assert missing_store.get_run("missing")["status"] == "start_failed"

    running_store = InMemoryExecutionStore()
    running_gateway = FakeTemporalGateway()
    running_workflow = _submitting(running_store, "running")
    running_gateway.descriptions[running_workflow] = "running"

    asyncio.run(reconcile_runs_once(running_store, running_gateway))
    assert running_store.get_run("running")["status"] == "accepted"
    asyncio.run(reconcile_runs_once(running_store, running_gateway))
    assert running_store.get_run("running")["status"] == "accepted"


def test_reconciler_repairs_accepted_and_running_terminal_rows() -> None:
    store = InMemoryExecutionStore()
    gateway = FakeTemporalGateway()
    accepted_workflow = _submitting(store, "accepted")
    failed_workflow = _submitting(store, "failed")
    store.set_run_status("accepted", "accepted")
    store.set_run_status("failed", "accepted")
    store.set_run_status("failed", "running")
    gateway.descriptions[accepted_workflow] = "terminated"
    gateway.descriptions[failed_workflow] = "timed_out"

    asyncio.run(reconcile_runs_once(store, gateway))

    assert store.get_run("accepted")["status"] == "terminated"
    assert store.get_run("failed")["status"] == "failed"
    assert store.get_run("accepted")["finished_at"] is not None
    assert store.get_run("failed")["finished_at"] is not None
