from __future__ import annotations

import uuid

import pytest

from julep.execution.projection_store import InMemoryExecutionStore, PostgresExecutionStore


def _create_run(
    store: InMemoryExecutionStore | PostgresExecutionStore,
    *,
    run_id: str,
    idempotency_key: str,
    started_at: float,
    owner: str = "alice",
) -> str | dict[str, object]:
    return store.create_run(
        run_id=run_id,
        idempotency_key=idempotency_key,
        workflow_id=f"run-{run_id}",
        session_id=f"run-{run_id}",
        release_hash="sha256:" + "a" * 64,
        pipeline="summary",
        application="memory",
        principal={"key": owner},
        input_ref=None,
        started_at=started_at,
    )


def test_in_memory_run_idempotency_status_and_pagination() -> None:
    store = InMemoryExecutionStore()
    assert _create_run(store, run_id="a", idempotency_key="idem-a", started_at=1.0) == (
        "created"
    )
    assert _create_run(store, run_id="b", idempotency_key="idem-b", started_at=2.0) == (
        "created"
    )

    duplicate = _create_run(store, run_id="different", idempotency_key="idem-a", started_at=3.0)
    assert isinstance(duplicate, dict)
    assert duplicate["run_id"] == "a"
    assert _create_run(store, run_id="a", idempotency_key="other", started_at=4.0) == (
        store.get_run("a")
    )

    store.set_run_status("a", "accepted", temporal_run_id="temporal-a")
    accepted = store.get_run("a")
    assert accepted is not None
    assert accepted["status"] == "accepted"
    assert accepted["temporal_run_id"] == "temporal-a"
    assert store.get_run_by_idempotency_key("idem-a") == accepted
    assert store.list_runs_by_status("accepted") == [accepted]

    page, cursor = store.list_runs(principal_subset={"key": "alice"}, cursor=None, limit=1)
    assert [row["run_id"] for row in page] == ["b"]
    assert cursor is not None
    next_page, next_cursor = store.list_runs(
        principal_subset={"key": "alice"}, cursor=cursor, limit=1
    )
    assert [row["run_id"] for row in next_page] == ["a"]
    assert next_cursor is None
    hidden, _ = store.list_runs(principal_subset={"key": "bob"}, cursor=None, limit=10)
    assert hidden == []


def test_finalize_preserves_submission_fields() -> None:
    store = InMemoryExecutionStore()
    assert _create_run(store, run_id="preserved", idempotency_key="idem", started_at=1.0) == (
        "created"
    )

    store.finalize_run(
        run_id="preserved",
        workflow_id="run-preserved",
        segment_seq=0,
        status="completed",
        terminal_event=None,
        result_payload=None,
        result_byte_len=0,
        result_oversize=False,
        error=None,
        finished_at=2.0,
    )

    row = store.get_run("preserved")
    assert row is not None
    assert row["idempotency_key"] == "idem"
    assert row["pipeline"] == "summary"
    assert row["release_hash"] == "sha256:" + "a" * 64
    assert row["principal"] == {"key": "alice"}
    assert row["status"] == "completed"

    # A workflow can finish before the HTTP submitter records acceptance.
    # The late update must never regress a terminal row back to accepted.
    store.set_run_status("preserved", "accepted", temporal_run_id="late-temporal-id")
    late = store.get_run("preserved")
    assert late is not None
    assert late["status"] == "completed"
    assert late["temporal_run_id"] == "late-temporal-id"


def test_first_projection_event_marks_an_accepted_run_running() -> None:
    store = InMemoryExecutionStore()
    assert _create_run(store, run_id="active", idempotency_key="active", started_at=1.0) == (
        "created"
    )
    store.set_run_status("active", "accepted", temporal_run_id="temporal-active")
    store.insert_events(
        [
            {
                "workflow_id": "run-active",
                "segment_seq": 0,
                "event_id": "event-active",
                "run_id": "active",
                "type": "WILL",
                "node": "root",
                "cid": "cid-active",
                "ts": 1.5,
                "causes": [],
                "attrs": {},
            }
        ]
    )
    row = store.get_run("active")
    assert row is not None
    assert row["status"] == "running"


def test_in_memory_release_and_deployment_records() -> None:
    store = InMemoryExecutionStore()
    first_hash = "sha256:" + "1" * 64
    second_hash = "sha256:" + "2" * 64
    store.put_release(first_hash, "memory", {"schemaVersion": 2}, 1.0)
    store.put_release(second_hash, "memory", {"schemaVersion": 2}, 2.0)
    store.put_release(first_hash, "changed", {"schemaVersion": 999}, 9.0)

    first = store.get_release(first_hash)
    assert first is not None
    assert first["application"] == "memory"
    releases, cursor = store.list_releases(None, 1)
    assert [row["release_hash"] for row in releases] == [second_hash]
    assert cursor is not None
    releases, cursor = store.list_releases(cursor, 1)
    assert [row["release_hash"] for row in releases] == [first_hash]
    assert cursor is None

    store.activate_deployment("summary", first_hash, 3.0, "alice")
    store.activate_deployment("summary", second_hash, 4.0, "admin")
    deployment = store.get_deployment("summary")
    assert deployment is not None
    assert deployment["release_hash"] == second_hash
    assert store.list_deployments() == [deployment]


def test_sweep_clears_and_deletes_expired_input_claims() -> None:
    store = InMemoryExecutionStore()
    input_ref = "val:input"
    store.put_value(input_ref, {"secret": "expired"}, 20, False)
    assert store.create_run(
        run_id="expired-input",
        idempotency_key="expired-input",
        workflow_id="run-expired-input",
        session_id="run-expired-input",
        release_hash="sha256:" + "a" * 64,
        pipeline="summary",
        application="memory",
        principal={"key": "alice"},
        input_ref=input_ref,
        started_at=0.5,
    ) == "created"
    store.finalize_run(
        run_id="expired-input",
        workflow_id="run-expired-input",
        segment_seq=0,
        status="completed",
        terminal_event=None,
        result_payload=None,
        result_byte_len=0,
        result_oversize=False,
        error=None,
        finished_at=1.0,
    )

    assert store.sweep(0) == 1
    assert store.get_value(input_ref) is None
    row = store.get_run("expired-input")
    assert row is not None
    assert row["input_ref"] is None


def test_sweep_includes_start_failed_input_claims() -> None:
    store = InMemoryExecutionStore()
    input_ref = "val:failed-input"
    store.put_value(input_ref, {"secret": "never-started"}, 24, False)
    assert store.create_run(
        run_id="failed-input",
        idempotency_key="failed-input",
        workflow_id="run-failed-input",
        session_id="run-failed-input",
        release_hash="sha256:" + "a" * 64,
        pipeline="summary",
        application="memory",
        principal={"key": "alice"},
        input_ref=input_ref,
        started_at=0.5,
    ) == "created"
    store.set_run_status("failed-input", "start_failed", finished_at=1.0)

    assert store.sweep(0) == 1
    assert store.get_value(input_ref) is None
    row = store.get_run("failed-input")
    assert row is not None
    assert row["input_ref"] is None


@pytest.mark.skipif(
    not __import__("os").environ.get("JULEP_TEST_PG_DSN"),
    reason="JULEP_TEST_PG_DSN is not set",
)
def test_postgres_create_run_idempotency_and_pagination() -> None:
    import os

    import psycopg

    dsn = os.environ["JULEP_TEST_PG_DSN"]
    store = PostgresExecutionStore(dsn)
    store.apply_schema()
    prefix = f"server-test-{uuid.uuid4().hex}"
    run_ids = [f"{prefix}-a", f"{prefix}-b"]
    keys = [f"{prefix}-idem-a", f"{prefix}-idem-b"]
    try:
        assert _create_run(
            store,
            run_id=run_ids[0],
            idempotency_key=keys[0],
            started_at=1.0,
            owner=prefix,
        ) == "created"
        assert _create_run(
            store,
            run_id=run_ids[1],
            idempotency_key=keys[1],
            started_at=2.0,
            owner=prefix,
        ) == "created"
        duplicate = _create_run(
            store,
            run_id=f"{prefix}-duplicate",
            idempotency_key=keys[0],
            started_at=3.0,
            owner=prefix,
        )
        assert isinstance(duplicate, dict)
        assert duplicate["run_id"] == run_ids[0]
        first_page, cursor = store.list_runs(
            principal_subset={"key": prefix}, cursor=None, limit=1
        )
        assert cursor is not None
        second_page, _ = store.list_runs(
            principal_subset={"key": prefix}, cursor=cursor, limit=1
        )
        observed = {row["run_id"] for row in first_page + second_page}
        assert set(run_ids).issubset(observed)
    finally:
        store.close()
        with psycopg.connect(dsn) as conn:
            conn.execute("DELETE FROM runs WHERE run_id LIKE %s", (f"{prefix}%",))
