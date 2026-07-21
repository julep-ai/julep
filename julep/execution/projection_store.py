"""Durable execution-store seam and Temporal projection egress activities.

Projection events are produced deterministically inside a workflow, but all
redaction, content hashing, and database IO happen at this activity boundary.
The Postgres driver is imported only when a Postgres-backed method is used, so
the module remains importable in installations without psycopg.
"""

from __future__ import annotations

import hashlib
import logging
import os
import threading
import time
from collections.abc import Mapping, Sequence
from typing import Any, Callable, Optional, Protocol, TypeVar

try:
    from temporalio import activity as _temporal_activity
except ImportError:  # The in-memory store remains usable without the Temporal extra.
    _temporal_activity = None  # type: ignore[assignment]

from ..ir import canonical_json
from ..trajectory import (
    _REDACTION_DROP,
    redact_for_capture,
    redact_secret_shaped,
)
from . import effects
from .projection_sql import apply_projection_schema

logger = logging.getLogger("julep.execution.projection_store")

MAX_INLINE_VALUE_BYTES = 64 * 1024
MAX_READ_EVENTS_LIMIT = 1_000
TERMINAL_RUN_STATUSES = frozenset({"completed", "failed", "canceled", "terminated"})

_MISSING = object()
_ActivityCallable = TypeVar("_ActivityCallable", bound=Callable[..., Any])


def _activity_defn(*, name: str) -> Callable[[_ActivityCallable], _ActivityCallable]:
    """Use Temporal's regular activity decorator when the extra is installed."""

    def decorate(fn: _ActivityCallable) -> _ActivityCallable:
        if _temporal_activity is None:
            return fn
        return _temporal_activity.defn(name=name)(fn)

    return decorate


class ExecutionStore(Protocol):
    """Storage operations needed by projection egress in this release."""

    def apply_schema(self) -> None: ...

    def insert_events(self, events: Sequence[Mapping[str, Any]]) -> None: ...

    def put_value(
        self,
        value_ref: str,
        payload: Any,
        byte_len: int,
        oversize: bool,
    ) -> None: ...

    def finalize_run(
        self,
        *,
        run_id: str,
        workflow_id: str,
        segment_seq: int,
        status: str,
        terminal_event: Optional[Mapping[str, Any]],
        result_payload: Any,
        result_byte_len: int,
        result_oversize: bool,
        error: Optional[str],
        finished_at: float,
    ) -> None: ...

    def get_run(self, run_id: str) -> Optional[dict[str, Any]]: ...

    def read_events(
        self,
        run_id: str,
        after_seq: int,
        limit: int,
    ) -> list[dict[str, Any]]: ...

    def get_value(self, value_ref: str) -> Optional[dict[str, Any]]: ...

    def sweep(self, older_than_s: float) -> int: ...

    def close(self) -> None: ...


def _field(
    row: Mapping[str, Any],
    snake_name: str,
    camel_name: Optional[str] = None,
    default: Any = _MISSING,
) -> Any:
    if snake_name in row:
        return row[snake_name]
    if camel_name is not None and camel_name in row:
        return row[camel_name]
    if default is not _MISSING:
        return default
    raise KeyError(snake_name)


def _normalise_event(
    event: Mapping[str, Any],
    *,
    run_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    segment_seq: Optional[int] = None,
    value_ref: Any = _MISSING,
) -> dict[str, Any]:
    """Return the database row shape, accepting event-JSON camelCase aliases."""
    event_type = _field(event, "type")
    if hasattr(event_type, "value"):
        event_type = event_type.value

    raw_causes = _field(event, "causes", default=[])
    raw_attrs = _field(event, "attrs", default={})
    resolved_value_ref = (
        _field(event, "value_ref", "valueRef", None)
        if value_ref is _MISSING
        else value_ref
    )

    return {
        "workflow_id": str(
            workflow_id
            if workflow_id is not None
            else _field(event, "workflow_id", "workflowId")
        ),
        "segment_seq": int(
            segment_seq
            if segment_seq is not None
            else _field(event, "segment_seq", "segmentSeq")
        ),
        "event_id": str(_field(event, "event_id", "eventId")),
        "run_id": str(
            run_id if run_id is not None else _field(event, "run_id", "runId")
        ),
        "type": str(event_type),
        "node": str(_field(event, "node")),
        "cid": str(_field(event, "cid")),
        "ts": float(_field(event, "ts")),
        "causes": list(raw_causes or []),
        "value_ref": None if resolved_value_ref is None else str(resolved_value_ref),
        "shape": _field(event, "shape", default=None),
        "cost": _field(event, "cost", default=None),
        "error": _field(event, "error", default=None),
        "attrs": dict(raw_attrs or {}),
    }


def _event_key(event: Mapping[str, Any]) -> tuple[str, int, str]:
    return (
        str(event["workflow_id"]),
        int(event["segment_seq"]),
        str(event["event_id"]),
    )


def _bounded_limit(limit: int) -> int:
    return max(0, min(int(limit), MAX_READ_EVENTS_LIMIT))


class InMemoryExecutionStore:
    """Thread-safe, insertion-ordered execution store for tests and local use."""

    def __init__(self) -> None:
        self._runs: dict[str, dict[str, Any]] = {}
        self._events: dict[tuple[str, int, str], dict[str, Any]] = {}
        self._values: dict[str, dict[str, Any]] = {}
        self._next_event_seq = 1
        self._lock = threading.RLock()

    def apply_schema(self) -> None:
        return None

    def insert_events(self, events: Sequence[Mapping[str, Any]]) -> None:
        rows = [_normalise_event(event) for event in events]
        with self._lock:
            for row in rows:
                key = _event_key(row)
                if key in self._events:
                    continue
                stored = dict(row)
                stored["seq"] = self._next_event_seq
                self._next_event_seq += 1
                self._events[key] = stored

    def put_value(
        self,
        value_ref: str,
        payload: Any,
        byte_len: int,
        oversize: bool,
    ) -> None:
        value = {
            "payload": None if oversize else payload,
            "byte_len": int(byte_len),
            "oversize": bool(oversize),
        }
        with self._lock:
            self._values.setdefault(value_ref, value)

    def finalize_run(
        self,
        *,
        run_id: str,
        workflow_id: str,
        segment_seq: int,
        status: str,
        terminal_event: Optional[Mapping[str, Any]],
        result_payload: Any,
        result_byte_len: int,
        result_oversize: bool,
        error: Optional[str],
        finished_at: float,
    ) -> None:
        event_row = (
            None
            if terminal_event is None
            else _normalise_event(
                terminal_event,
                run_id=run_id,
                workflow_id=workflow_id,
                segment_seq=segment_seq,
            )
        )
        result_ref = None if event_row is None else event_row["value_ref"]

        with self._lock:
            # All mutations happen while holding one lock, mirroring the single
            # Postgres transaction in the durable implementation.
            if result_ref is not None:
                self._values.setdefault(
                    str(result_ref),
                    {
                        "payload": None if result_oversize else result_payload,
                        "byte_len": int(result_byte_len),
                        "oversize": bool(result_oversize),
                    },
                )

            if event_row is not None:
                key = _event_key(event_row)
                if key not in self._events:
                    stored_event = dict(event_row)
                    stored_event["seq"] = self._next_event_seq
                    self._next_event_seq += 1
                    self._events[key] = stored_event

            existing = self._runs.get(run_id, {})
            self._runs[run_id] = {
                "run_id": run_id,
                "idempotency_key": existing.get("idempotency_key"),
                "workflow_id": existing.get("workflow_id") or workflow_id,
                "temporal_run_id": existing.get("temporal_run_id"),
                "session_id": existing.get("session_id"),
                "release_hash": existing.get("release_hash"),
                "pipeline": existing.get("pipeline"),
                "application": existing.get("application"),
                "status": status,
                "principal": existing.get("principal"),
                "input_ref": existing.get("input_ref"),
                "result_ref": result_ref,
                "error": error,
                "started_at": existing.get("started_at"),
                "finished_at": float(finished_at),
            }

    def get_run(self, run_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            run = self._runs.get(run_id)
            return None if run is None else dict(run)

    def read_events(
        self,
        run_id: str,
        after_seq: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        bounded = _bounded_limit(limit)
        if bounded == 0:
            return []
        with self._lock:
            matches = (
                event
                for event in self._events.values()
                if event["run_id"] == run_id and int(event["seq"]) > after_seq
            )
            return [dict(event) for event in list(matches)[:bounded]]

    def get_value(self, value_ref: str) -> Optional[dict[str, Any]]:
        with self._lock:
            value = self._values.get(value_ref)
            return None if value is None else dict(value)

    def sweep(self, older_than_s: float) -> int:
        if older_than_s < 0:
            raise ValueError("older_than_s must be non-negative")
        cutoff = time.time() - older_than_s
        with self._lock:
            expired_run_ids = {
                run_id
                for run_id, run in self._runs.items()
                if run.get("status") in TERMINAL_RUN_STATUSES
                and run.get("finished_at") is not None
                and float(run["finished_at"]) < cutoff
            }
            event_keys = [
                key
                for key, event in self._events.items()
                if event["run_id"] in expired_run_ids
            ]
            candidate_refs = {
                str(self._events[key]["value_ref"])
                for key in event_keys
                if self._events[key]["value_ref"] is not None
            }
            candidate_refs.update(
                str(self._runs[run_id]["result_ref"])
                for run_id in expired_run_ids
                if self._runs[run_id].get("result_ref") is not None
            )

            for key in event_keys:
                del self._events[key]
            for run_id in expired_run_ids:
                self._runs[run_id]["result_ref"] = None

            referenced_refs = {
                str(event["value_ref"])
                for event in self._events.values()
                if event["value_ref"] is not None
            }
            referenced_refs.update(
                str(run["result_ref"])
                for run in self._runs.values()
                if run.get("result_ref") is not None
            )
            deleted_values = 0
            for value_ref in candidate_refs - referenced_refs:
                if self._values.pop(value_ref, None) is not None:
                    deleted_values += 1
            return len(event_keys) + deleted_values

    def close(self) -> None:
        return None


class PostgresExecutionStore:
    """psycopg3 execution store backed by a lazily opened connection pool."""

    _INSERT_EVENT_SQL = """
        INSERT INTO projection_events (
            workflow_id, segment_seq, event_id, run_id, type, node, cid, ts,
            causes, value_ref, shape, cost, error, attrs
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (workflow_id, segment_seq, event_id) DO NOTHING
    """
    _INSERT_VALUE_SQL = """
        INSERT INTO projection_values (
            value_ref, payload, byte_len, oversize, created_at
        ) VALUES (%s, %s, %s, %s, EXTRACT(EPOCH FROM clock_timestamp()))
        ON CONFLICT (value_ref) DO NOTHING
    """
    _FINALIZE_RUN_SQL = """
        INSERT INTO runs (
            run_id, workflow_id, status, result_ref, error, finished_at
        ) VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (run_id) DO UPDATE SET
            workflow_id = COALESCE(runs.workflow_id, EXCLUDED.workflow_id),
            status = EXCLUDED.status,
            result_ref = EXCLUDED.result_ref,
            error = EXCLUDED.error,
            finished_at = EXCLUDED.finished_at
    """

    def __init__(self, dsn: str) -> None:
        if not dsn:
            raise ValueError("Postgres execution-store DSN must not be empty")
        self._dsn = dsn
        self._pool: Any = None
        self._pool_lock = threading.Lock()

    def _pool_instance(self) -> Any:
        if self._pool is not None:
            return self._pool
        with self._pool_lock:
            if self._pool is None:
                import psycopg
                from psycopg_pool import ConnectionPool

                self._pool = ConnectionPool(
                    conninfo=self._dsn,
                    kwargs={"row_factory": psycopg.rows.dict_row},
                    open=False,
                )
                self._pool.open()
        return self._pool

    @staticmethod
    def _insert_event(cur: Any, row: Mapping[str, Any]) -> None:
        from psycopg.types.json import Jsonb

        cur.execute(
            PostgresExecutionStore._INSERT_EVENT_SQL,
            (
                row["workflow_id"],
                row["segment_seq"],
                row["event_id"],
                row["run_id"],
                row["type"],
                row["node"],
                row["cid"],
                row["ts"],
                Jsonb(row["causes"]),
                row["value_ref"],
                row["shape"],
                row["cost"],
                row["error"],
                Jsonb(row["attrs"]),
            ),
        )

    @staticmethod
    def _insert_value(
        cur: Any,
        value_ref: str,
        payload: Any,
        byte_len: int,
        oversize: bool,
    ) -> None:
        from psycopg.types.json import Jsonb

        stored_payload = None if oversize else Jsonb(payload)
        cur.execute(
            PostgresExecutionStore._INSERT_VALUE_SQL,
            (value_ref, stored_payload, int(byte_len), bool(oversize)),
        )

    def apply_schema(self) -> None:
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:

                def execute(sql: str) -> None:
                    cur.execute(sql)

                apply_projection_schema(execute)

    def insert_events(self, events: Sequence[Mapping[str, Any]]) -> None:
        rows = [_normalise_event(event) for event in events]
        if not rows:
            return
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                for row in rows:
                    self._insert_event(cur, row)

    def put_value(
        self,
        value_ref: str,
        payload: Any,
        byte_len: int,
        oversize: bool,
    ) -> None:
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                self._insert_value(cur, value_ref, payload, byte_len, oversize)

    def finalize_run(
        self,
        *,
        run_id: str,
        workflow_id: str,
        segment_seq: int,
        status: str,
        terminal_event: Optional[Mapping[str, Any]],
        result_payload: Any,
        result_byte_len: int,
        result_oversize: bool,
        error: Optional[str],
        finished_at: float,
    ) -> None:
        event_row = (
            None
            if terminal_event is None
            else _normalise_event(
                terminal_event,
                run_id=run_id,
                workflow_id=workflow_id,
                segment_seq=segment_seq,
            )
        )
        result_ref = None if event_row is None else event_row["value_ref"]

        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    if result_ref is not None:
                        self._insert_value(
                            cur,
                            str(result_ref),
                            result_payload,
                            result_byte_len,
                            result_oversize,
                        )
                    cur.execute(
                        self._FINALIZE_RUN_SQL,
                        (
                            run_id,
                            workflow_id,
                            status,
                            result_ref,
                            error,
                            float(finished_at),
                        ),
                    )
                    if event_row is not None:
                        self._insert_event(cur, event_row)

    def get_run(self, run_id: str) -> Optional[dict[str, Any]]:
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM runs WHERE run_id = %s", (run_id,))
                row = cur.fetchone()
        return None if row is None else dict(row)

    def read_events(
        self,
        run_id: str,
        after_seq: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        bounded = _bounded_limit(limit)
        if bounded == 0:
            return []
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM projection_events
                    WHERE run_id = %s AND seq > %s
                    ORDER BY seq
                    LIMIT %s
                    """,
                    (run_id, int(after_seq), bounded),
                )
                rows = cur.fetchall()
        return [dict(row) for row in rows]

    def get_value(self, value_ref: str) -> Optional[dict[str, Any]]:
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT payload, oversize, byte_len
                    FROM projection_values
                    WHERE value_ref = %s
                    """,
                    (value_ref,),
                )
                row = cur.fetchone()
        return None if row is None else dict(row)

    def sweep(self, older_than_s: float) -> int:
        if older_than_s < 0:
            raise ValueError("older_than_s must be non-negative")
        cutoff = time.time() - older_than_s
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT DISTINCT value_ref
                        FROM (
                            SELECT event.value_ref
                            FROM projection_events AS event
                            JOIN runs AS run ON run.run_id = event.run_id
                            WHERE run.status = ANY(%s)
                              AND run.finished_at < %s
                              AND event.value_ref IS NOT NULL
                            UNION
                            SELECT result_ref AS value_ref
                            FROM runs
                            WHERE status = ANY(%s)
                              AND finished_at < %s
                              AND result_ref IS NOT NULL
                        ) AS expired_refs
                        """,
                        (
                            list(TERMINAL_RUN_STATUSES),
                            cutoff,
                            list(TERMINAL_RUN_STATUSES),
                            cutoff,
                        ),
                    )
                    candidate_refs = [row["value_ref"] for row in cur.fetchall()]
                    cur.execute(
                        """
                        DELETE FROM projection_events
                        WHERE run_id IN (
                            SELECT run_id FROM runs
                            WHERE status = ANY(%s) AND finished_at < %s
                        )
                        """,
                        (list(TERMINAL_RUN_STATUSES), cutoff),
                    )
                    deleted_events = int(cur.rowcount)
                    cur.execute(
                        """
                        UPDATE runs SET result_ref = NULL
                        WHERE status = ANY(%s) AND finished_at < %s
                        """,
                        (list(TERMINAL_RUN_STATUSES), cutoff),
                    )

                    deleted_values = 0
                    if candidate_refs:
                        cur.execute(
                            """
                            DELETE FROM projection_values AS value
                            WHERE value.value_ref = ANY(%s)
                              AND NOT EXISTS (
                                  SELECT 1 FROM projection_events AS event
                                  WHERE event.value_ref = value.value_ref
                              )
                              AND NOT EXISTS (
                                  SELECT 1 FROM runs AS run
                                  WHERE run.result_ref = value.value_ref
                              )
                            """,
                            (candidate_refs,),
                        )
                        deleted_values = int(cur.rowcount)
        return deleted_events + deleted_values

    def close(self) -> None:
        with self._pool_lock:
            if self._pool is not None:
                self._pool.close()
                self._pool = None


_EXECUTION_STORE: Optional[ExecutionStore] = None
_store_env_checked = False
_warned = False
_store_lock = threading.Lock()


def set_projection_store(store: Optional[ExecutionStore]) -> None:
    """Install the process-wide execution store used by egress activities."""
    global _EXECUTION_STORE
    with _store_lock:
        _EXECUTION_STORE = store


def get_projection_store() -> Optional[ExecutionStore]:
    """Resolve the configured store once, warning once when egress is unwired."""
    global _EXECUTION_STORE, _store_env_checked, _warned
    if _EXECUTION_STORE is not None:
        return _EXECUTION_STORE

    with _store_lock:
        if _EXECUTION_STORE is not None:
            return _EXECUTION_STORE
        if not _store_env_checked:
            _store_env_checked = True
            dsn = os.environ.get("JULEP_EXECUTION_STORE_DSN")
            if dsn:
                try:
                    _EXECUTION_STORE = PostgresExecutionStore(dsn)
                except Exception:
                    if not _warned:
                        logger.warning(
                            "failed to configure projection execution store",
                            exc_info=True,
                        )
                        _warned = True
                return _EXECUTION_STORE
        if not _warned:
            logger.warning(
                "projection egress is enabled but no execution store is configured"
            )
            _warned = True
    return None


class _CapturedValue:
    def __init__(self, value_ref: str, payload: Any, byte_len: int, oversize: bool) -> None:
        self.value_ref = value_ref
        self.payload = payload
        self.byte_len = byte_len
        self.oversize = oversize


def _capture_value(raw_value: Any) -> Optional[_CapturedValue]:
    redactor = effects._CTX.redactor or redact_secret_shaped
    redacted = redact_for_capture(redactor, raw_value)
    if redacted is _REDACTION_DROP:
        return None

    canonical_bytes = canonical_json(redacted).encode("utf-8")
    ref = "val:" + hashlib.sha256(canonical_bytes).hexdigest()[:32]
    oversize = len(canonical_bytes) > MAX_INLINE_VALUE_BYTES
    return _CapturedValue(
        value_ref=ref,
        payload=None if oversize else redacted,
        byte_len=len(canonical_bytes),
        oversize=oversize,
    )


@_activity_defn(name="persistProjectionBatch")
async def persist_projection_batch(inp: dict[str, Any]) -> None:
    """Redact and persist one idempotent batch of workflow projection events."""
    store = get_projection_store()
    if store is None:
        return

    run_id = str(inp["runId"])
    workflow_id = str(inp["workflowId"])
    segment_seq = int(inp["segmentSeq"])
    rewritten_events: list[dict[str, Any]] = []

    for candidate in inp.get("events", []):
        if not isinstance(candidate, Mapping):
            raise TypeError("projection event must be a mapping")
        captured = _capture_value(candidate["rawValue"]) if "rawValue" in candidate else None
        # Never retain an in-workflow hash.  A missing/dropped raw value always
        # rewrites the persisted reference to NULL.
        persisted_ref = None if captured is None else captured.value_ref
        rewritten_events.append(
            _normalise_event(
                candidate,
                run_id=run_id,
                workflow_id=workflow_id,
                segment_seq=segment_seq,
                value_ref=persisted_ref,
            )
        )
        if captured is not None:
            store.put_value(
                captured.value_ref,
                captured.payload,
                captured.byte_len,
                captured.oversize,
            )

    store.insert_events(rewritten_events)


@_activity_defn(name="finalizeProjectionRun")
async def finalize_projection_run(inp: dict[str, Any]) -> None:
    """Atomically persist a terminal run status, event, and redacted result."""
    store = get_projection_store()
    if store is None:
        return

    terminal_candidate = inp.get("terminalEvent")
    if terminal_candidate is not None and not isinstance(terminal_candidate, Mapping):
        raise TypeError("terminal projection event must be a mapping")

    raw_present = "rawValue" in inp or (
        terminal_candidate is not None and "rawValue" in terminal_candidate
    )
    raw_value = (
        inp["rawValue"]
        if "rawValue" in inp
        else terminal_candidate["rawValue"]
        if terminal_candidate is not None and "rawValue" in terminal_candidate
        else None
    )
    captured = _capture_value(raw_value) if raw_present else None
    persisted_ref = None if captured is None else captured.value_ref

    run_id = str(inp["runId"])
    workflow_id = str(inp["workflowId"])
    segment_seq = int(inp["segmentSeq"])
    terminal_event = (
        None
        if terminal_candidate is None
        else _normalise_event(
            terminal_candidate,
            run_id=run_id,
            workflow_id=workflow_id,
            segment_seq=segment_seq,
            value_ref=persisted_ref,
        )
    )
    # Workflow callers may supply their replay-safe server timestamp. Direct
    # activity callers do not have to: activity-side wall time is safe here and
    # avoids treating a projection's logical ``ts`` counter as Unix time.
    finished_at_value = inp.get("finishedAt")
    if finished_at_value is None:
        finished_at_value = time.time()
    store.finalize_run(
        run_id=run_id,
        workflow_id=workflow_id,
        segment_seq=segment_seq,
        status=str(inp["status"]),
        terminal_event=terminal_event,
        result_payload=None if captured is None else captured.payload,
        result_byte_len=0 if captured is None else captured.byte_len,
        result_oversize=False if captured is None else captured.oversize,
        error=None if inp.get("error") is None else str(inp["error"]),
        finished_at=float(finished_at_value),
    )
