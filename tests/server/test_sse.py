from __future__ import annotations

import asyncio
import time

from starlette.testclient import TestClient

from julep.server.sse import terminal_projection_is_persisted
from julep.server.routes.runs import reconcile_runs_once

from .conftest import ALICE_HEADERS


def _event(run_id: str, event_id: str, *, terminal: bool = False) -> dict:
    return {
        "workflow_id": f"run-{run_id}",
        "segment_seq": 0,
        "event_id": event_id,
        "run_id": run_id,
        "type": "DID",
        "node": "root",
        "cid": event_id,
        "ts": time.time(),
        "causes": [],
        "value_ref": None,
        "shape": None,
        "cost": None,
        "error": None,
        "attrs": {"terminal": True, "status": "completed"} if terminal else {},
    }


def _create_run(store, run_id: str, *, accepted: bool = True) -> None:
    assert store.create_run(
        run_id=run_id,
        idempotency_key=f"idem-{run_id}",
        workflow_id=f"run-{run_id}",
        session_id=f"run-{run_id}",
        release_hash="sha256:" + "a" * 64,
        pipeline="summary",
        application="memory",
        principal={"key": "alice"},
        input_ref=None,
        started_at=time.time(),
    ) == "created"
    if accepted:
        store.set_run_status(run_id, "accepted")


def test_sse_resume_heartbeat_and_stored_terminal_event(server_factory) -> None:
    harness = server_factory()
    run_id = "sse-run"
    _create_run(harness.store, run_id)
    harness.store.insert_events([_event(run_id, "one"), _event(run_id, "two")])
    harness.store.finalize_run(
        run_id=run_id,
        workflow_id=f"run-{run_id}",
        segment_seq=0,
        status="completed",
        terminal_event=_event(run_id, "stored-terminal", terminal=True),
        result_payload=None,
        result_byte_len=4,
        result_oversize=False,
        error=None,
        finished_at=time.time(),
    )
    rows = harness.store.read_events(run_id, 0, 10)
    assert [row["event_id"] for row in rows] == ["one", "two", "stored-terminal"]

    with TestClient(harness.app) as client:
        response = client.get(
            f"/v1/runs/{run_id}/events",
            headers={
                **ALICE_HEADERS,
                "Accept": "text/event-stream",
                "Last-Event-ID": str(rows[0]["seq"]),
            },
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert ": keep-alive" in response.text
    assert f"id: {rows[1]['seq']}" in response.text
    assert f"id: {rows[2]['seq']}" in response.text
    assert '"event_id":"one"' not in response.text
    assert '"event_id":"two"' in response.text
    assert '"event_id":"stored-terminal"' in response.text
    assert response.text.count("event: projection") == 2


def test_start_failed_sse_closes_without_synthesizing_an_event(server_factory) -> None:
    harness = server_factory()
    run_id = "start-failed"
    _create_run(harness.store, run_id, accepted=False)
    harness.store.set_run_status(run_id, "start_failed")
    failed = harness.store.get_run(run_id)
    assert failed is not None
    assert failed["status"] == "start_failed"

    with TestClient(harness.app) as client:
        response = client.get(
            f"/v1/runs/{run_id}/events",
            headers={**ALICE_HEADERS, "Accept": "text/event-stream"},
        )

    assert response.status_code == 200
    assert ": keep-alive" in response.text
    assert "event: projection" not in response.text


def test_reconciled_terminal_status_is_not_projection_evidence(server_factory) -> None:
    harness = server_factory()
    run_id = "reconciled-terminal"
    _create_run(harness.store, run_id)
    harness.store.set_run_status(run_id, "terminated", finished_at=time.time())
    row = harness.store.get_run(run_id)
    assert row is not None
    assert row["finished_at"] is not None
    assert terminal_projection_is_persisted(row, terminal_seen=False) is False
    assert harness.store.read_events(run_id, 0, 1) == []


def test_reconciler_terminal_event_closes_sse(server_factory) -> None:
    harness = server_factory()
    run_id = "reconciled-sse-terminal"
    workflow_id = f"run-{run_id}"
    _create_run(harness.store, run_id)
    harness.gateway.descriptions[workflow_id] = "terminated"

    asyncio.run(reconcile_runs_once(harness.store, harness.gateway))

    with TestClient(harness.app) as client:
        response = client.get(
            f"/v1/runs/{run_id}/events",
            headers={**ALICE_HEADERS, "Accept": "text/event-stream"},
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: projection" in response.text
    assert '"event_id":"__reconciled_terminal__"' in response.text
    assert '"reconciled":true' in response.text
