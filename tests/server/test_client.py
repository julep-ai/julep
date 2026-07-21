from __future__ import annotations

import time

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from starlette.testclient import TestClient

from julep.client import JulepClient, JulepClientError
from julep.projection import EventType, ProjectionEvent


def _seed_run(store, run_id: str) -> None:
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
        status="running",
        started_at=time.time(),
    ) == "created"


def _event(run_id: str, event_id: str, event_type: str) -> dict[str, object]:
    return {
        "workflow_id": f"run-{run_id}",
        "segment_seq": 0,
        "event_id": event_id,
        "run_id": run_id,
        "type": event_type,
        "node": "root",
        "cid": "root-1",
        "ts": time.time(),
        "causes": [],
        "value_ref": None,
        "shape": None,
        "cost": None,
        "error": None,
        "attrs": {},
    }


def test_client_health_runs_events_and_errors(server_factory) -> None:
    harness = server_factory()
    run_id = "client-run"
    _seed_run(harness.store, run_id)
    harness.store.insert_events(
        [_event(run_id, "planned", "Planned"), _event(run_id, "did", "Did")]
    )

    with TestClient(harness.app) as transport_client:
        client = JulepClient(api_key="alice-token", client=transport_client)
        assert client.health() == {"status": "ok"}
        assert client.list_runs()["items"][0]["run_id"] == run_id
        assert client.get_run(run_id)["status"] == "running"
        assert [row["event_id"] for row in client.read_events(run_id)["items"]] == [
            "planned",
            "did",
        ]
        events = client.projection_events(run_id)
        assert all(isinstance(event, ProjectionEvent) for event in events)
        assert events[1].event_id == "did"
        assert events[1].type is EventType.DID
        assert events[1].cid == "root-1"

        with pytest.raises(JulepClientError) as caught:
            client.get_run("missing")
        assert caught.value.status_code == 404


def test_start_run_requires_idempotency_or_run_id() -> None:
    client = JulepClient(client=TestClient(lambda scope, receive, send: None))
    with pytest.raises(ValueError, match="idempotency_key or run_id"):
        client.start_run(pipeline="summary")

