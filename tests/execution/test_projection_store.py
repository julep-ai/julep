"""Execution-store contracts and projection-egress capture tests.

The Postgres cases use an isolated schema and skip unless
``JULEP_TEST_PG_DSN`` is configured.  The activity tests invoke the async
activity bodies directly; they do not need a Temporal server.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import Iterator
from typing import Any

import pytest

from julep.execution.effects import WorkerContext, configure
from julep.execution.projection_store import (
    InMemoryExecutionStore,
    PostgresExecutionStore,
    finalize_projection_run,
    persist_projection_batch,
    set_projection_store,
)
from julep.ir import canonical_json
from julep.projection import value_ref
from julep.secrets import VaultCipher
from julep.trajectory import REDACTED_PLACEHOLDER, redact_secret_shaped


def _event(
    event_id: str,
    *,
    run_id: str = "run-1",
    workflow_id: str = "workflow-1",
    segment_seq: int = 0,
    event_type: str = "Did",
    value_ref_: str | None = None,
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "runId": run_id,
        "workflowId": workflow_id,
        "segmentSeq": segment_seq,
        "eventId": event_id,
        "type": event_type,
        "node": "node-1",
        "cid": "node-1@1",
        "ts": 1.25,
        "causes": [],
    }
    if value_ref_ is not None:
        event["valueRef"] = value_ref_
    return event


def _field(row: dict[str, Any], snake: str, camel: str) -> Any:
    """Accept either DB-column or wire casing from the read helpers."""
    return row[snake] if snake in row else row[camel]


def _close_postgres_store(store: PostgresExecutionStore) -> None:
    close = getattr(store, "close", None)
    if callable(close):
        close()
        return
    pool = getattr(store, "_pool", None)
    if pool is not None:
        pool.close()


@pytest.fixture(params=("memory", "postgres"))
def execution_store(request: pytest.FixtureRequest) -> Iterator[Any]:
    if request.param == "memory":
        yield InMemoryExecutionStore()
        return

    dsn = os.environ.get("JULEP_TEST_PG_DSN")
    if not dsn:
        pytest.skip("JULEP_TEST_PG_DSN is unset")

    import psycopg
    from psycopg import sql
    from psycopg.conninfo import make_conninfo

    schema = f"julep_projection_test_{uuid.uuid4().hex}"
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))

    scoped_dsn = make_conninfo(dsn, options=f"-csearch_path={schema}")
    store = PostgresExecutionStore(scoped_dsn)
    try:
        store.apply_schema()
        yield store
    finally:
        _close_postgres_store(store)
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute(
                sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                    sql.Identifier(schema)
                )
            )


@pytest.fixture(autouse=True)
def _reset_process_seams() -> Iterator[None]:
    set_projection_store(None)
    configure(WorkerContext())
    try:
        yield
    finally:
        set_projection_store(None)
        configure(WorkerContext())


def test_insert_events_is_idempotent(execution_store: Any) -> None:
    event = _event("event-idempotent")

    execution_store.insert_events([event])
    execution_store.insert_events([event])

    rows = execution_store.read_events("run-1", after_seq=0, limit=100)
    assert len(rows) == 1
    assert _field(rows[0], "event_id", "eventId") == "event-idempotent"


def test_vault_record_contract_round_trips_on_execution_store(execution_store: Any) -> None:
    cipher = VaultCipher(
        {"test": bytes.fromhex("44" * 32)}, active_key_id="test"
    )
    metadata = execution_store.put_secret(
        "projection-test-token", "store-secret", "admin", cipher
    )
    assert metadata["generation"] == 1
    assert "ciphertext" not in metadata
    row = execution_store.get_secret("projection-test-token")
    assert row is not None
    assert cipher.decrypt(
        row["name"], row["generation"], bytes(row["ciphertext"]), row["key_id"]
    ) == "store-secret"
    assert execution_store.list_secrets() == [metadata]

    archived = execution_store.archive_secret("projection-test-token", "admin")
    assert archived is not None and archived["archived_at"] is not None
    assert execution_store.get_secret("projection-test-token")["ciphertext"] is None
    assert execution_store.delete_secret("projection-test-token") is True


def test_activity_redacts_before_hashing_and_drops_on_redactor_failure(
    execution_store: Any,
) -> None:
    set_projection_store(execution_store)
    raw = {"password": "do-not-store", "visible": {"answer": 42}}
    redacted = redact_secret_shaped(raw)
    assert redacted == {
        "password": REDACTED_PLACEHOLDER,
        "visible": {"answer": 42},
    }
    expected_ref = value_ref(redacted)
    raw_ref = value_ref(raw)

    asyncio.run(
        persist_projection_batch(
            {
                "runId": "run-redaction",
                "workflowId": "workflow-redaction",
                "segmentSeq": 0,
                "events": [
                    {
                        **_event(
                            "event-redacted",
                            run_id="run-redaction",
                            workflow_id="workflow-redaction",
                            value_ref_=raw_ref,
                        ),
                        "rawValue": raw,
                    }
                ],
            }
        )
    )

    rows = execution_store.read_events("run-redaction", after_seq=0, limit=100)
    assert len(rows) == 1
    assert _field(rows[0], "value_ref", "valueRef") == expected_ref
    assert expected_ref != raw_ref
    assert execution_store.get_value(expected_ref) == {
        "payload": redacted,
        "oversize": False,
        "byte_len": len(canonical_json(redacted).encode("utf-8")),
    }
    assert execution_store.get_value(raw_ref) is None

    def raising_redactor(_value: Any) -> Any:
        raise RuntimeError("redactor unavailable")

    configure(WorkerContext(redactor=raising_redactor))
    dropped_raw = {"token": "must-never-land", "safe": True}
    asyncio.run(
        persist_projection_batch(
            {
                "runId": "run-drop",
                "workflowId": "workflow-drop",
                "segmentSeq": 0,
                "events": [
                    {
                        **_event(
                            "event-drop",
                            run_id="run-drop",
                            workflow_id="workflow-drop",
                            value_ref_=value_ref(dropped_raw),
                        ),
                        "rawValue": dropped_raw,
                    }
                ],
            }
        )
    )

    dropped_rows = execution_store.read_events("run-drop", after_seq=0, limit=100)
    assert len(dropped_rows) == 1
    assert _field(dropped_rows[0], "value_ref", "valueRef") is None
    assert execution_store.get_value(value_ref(dropped_raw)) is None

    # A DID carrying only the workflow-local ref cannot be safely resolved by
    # the activity. It must be cleared rather than persisted as a dangling ref.
    asyncio.run(
        persist_projection_batch(
            {
                "runId": "run-missing-raw",
                "workflowId": "workflow-missing-raw",
                "segmentSeq": 0,
                "events": [
                    _event(
                        "event-missing-raw",
                        run_id="run-missing-raw",
                        workflow_id="workflow-missing-raw",
                        value_ref_="val:workflow-local-only",
                    )
                ],
            }
        )
    )
    missing_rows = execution_store.read_events(
        "run-missing-raw", after_seq=0, limit=100
    )
    assert _field(missing_rows[0], "value_ref", "valueRef") is None
    assert execution_store.get_value("val:workflow-local-only") is None


def test_activity_persists_oversize_tombstone_without_payload(
    execution_store: Any,
) -> None:
    set_projection_store(execution_store)
    raw = {"body": "x" * (64 * 1024)}
    encoded = canonical_json(raw).encode("utf-8")
    expected_ref = value_ref(raw)

    asyncio.run(
        persist_projection_batch(
            {
                "runId": "run-oversize",
                "workflowId": "workflow-oversize",
                "segmentSeq": 0,
                "events": [
                    {
                        **_event(
                            "event-oversize",
                            run_id="run-oversize",
                            workflow_id="workflow-oversize",
                        ),
                        "rawValue": raw,
                    }
                ],
            }
        )
    )

    rows = execution_store.read_events("run-oversize", after_seq=0, limit=100)
    assert _field(rows[0], "value_ref", "valueRef") == expected_ref
    assert execution_store.get_value(expected_ref) == {
        "payload": None,
        "oversize": True,
        "byte_len": len(encoded),
    }


def test_finalize_run_writes_status_terminal_event_and_value(
    execution_store: Any,
) -> None:
    result = {"answer": 42}
    result_ref = value_ref(result)
    terminal = _event(
        "event-terminal",
        run_id="run-final",
        workflow_id="workflow-final",
        segment_seq=3,
        value_ref_=result_ref,
    )

    execution_store.finalize_run(
        run_id="run-final",
        workflow_id="workflow-final",
        segment_seq=3,
        status="completed",
        terminal_event=terminal,
        result_payload=result,
        result_byte_len=len(canonical_json(result).encode("utf-8")),
        result_oversize=False,
        error=None,
        finished_at=123.5,
    )

    run = execution_store.get_run("run-final")
    assert run is not None
    assert run["status"] == "completed"
    assert _field(run, "result_ref", "resultRef") == result_ref
    rows = execution_store.read_events("run-final", after_seq=0, limit=100)
    assert [_field(row, "event_id", "eventId") for row in rows] == [
        "event-terminal"
    ]
    assert execution_store.get_value(result_ref) == {
        "payload": result,
        "oversize": False,
        "byte_len": len(canonical_json(result).encode("utf-8")),
    }


def test_finalize_projection_activity_is_idempotent(execution_store: Any) -> None:
    set_projection_store(execution_store)
    payload = {
        "runId": "run-final-activity",
        "workflowId": "workflow-final-activity",
        "segmentSeq": 0,
        "status": "completed",
        "terminalEvent": {
            **_event(
                "event-final-activity",
                run_id="run-final-activity",
                workflow_id="workflow-final-activity",
            ),
            "rawValue": {"ok": True},
        },
        "rawValue": {"ok": True},
        "error": None,
    }

    asyncio.run(finalize_projection_run(payload))
    asyncio.run(finalize_projection_run(payload))

    rows = execution_store.read_events(
        "run-final-activity", after_seq=0, limit=100
    )
    assert len(rows) == 1
    assert execution_store.get_run("run-final-activity")["status"] == "completed"
