"""Durable execution-store seam and Temporal projection egress activities.

Projection events are produced deterministically inside a workflow, but all
redaction, content hashing, and database IO happen at this activity boundary.
The Postgres driver is imported only when a Postgres-backed method is used, so
the module remains importable in installations without psycopg.
"""

from __future__ import annotations

import base64
import binascii
import copy
import hashlib
import json
import logging
import os
import threading
import time
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any, Callable, Literal, Optional, Protocol, TypeVar

try:
    from temporalio import activity as _temporal_activity
except ImportError:  # The in-memory store remains usable without the Temporal extra.
    _temporal_activity = None  # type: ignore[assignment]

from ..ir import canonical_json
from ..trajectory import (
    _REDACTION_DROP,
    redact_for_capture,
)
from . import effects
from .projection_sql import apply_projection_schema

logger = logging.getLogger("julep.execution.projection_store")

MAX_INLINE_VALUE_BYTES = 64 * 1024
MAX_READ_EVENTS_LIMIT = 1_000
MAX_LIST_LIMIT = 100
TERMINAL_RUN_STATUSES = frozenset({"completed", "failed", "canceled", "terminated"})
_RETENTION_RUN_STATUSES = TERMINAL_RUN_STATUSES | {"start_failed"}
_RUN_STATUS_PREDECESSORS: dict[str, frozenset[str]] = {
    "accepted": frozenset({"submitting", "accepted"}),
    "start_failed": frozenset({"submitting", "start_failed"}),
    "running": frozenset({"accepted", "running"}),
    **{
        terminal: frozenset({"submitting", "accepted", "running", terminal})
        for terminal in TERMINAL_RUN_STATUSES
    },
}

_MISSING = object()
_ActivityCallable = TypeVar("_ActivityCallable", bound=Callable[..., Any])


class SecretCipher(Protocol):
    """Small vault cipher seam kept independent of the server package."""

    active_key_id: str

    def encrypt(self, name: str, generation: int, value: str) -> tuple[bytes, str]: ...

    def decrypt(
        self,
        name: str,
        generation: int,
        ciphertext: bytes,
        key_id: str,
    ) -> str: ...


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

    def create_run(
        self,
        *,
        run_id: str,
        idempotency_key: Optional[str],
        workflow_id: str,
        session_id: str,
        release_hash: str,
        pipeline: str,
        application: str,
        principal: Mapping[str, Any],
        input_ref: Optional[str],
        status: str = "submitting",
        started_at: float,
    ) -> Literal["created"] | dict[str, Any]: ...

    def set_run_status(
        self,
        run_id: str,
        status: str,
        *,
        temporal_run_id: Optional[str] = None,
        started_at: Optional[float] = None,
        finished_at: Optional[float] = None,
    ) -> None: ...

    def list_runs(
        self,
        *,
        principal_subset: Optional[Mapping[str, Any]],
        cursor: Optional[str],
        limit: int,
    ) -> tuple[list[dict[str, Any]], Optional[str]]: ...

    def list_runs_by_status(self, status: str) -> list[dict[str, Any]]: ...

    def get_run_by_idempotency_key(
        self,
        key: str,
    ) -> Optional[dict[str, Any]]: ...

    def read_events(
        self,
        run_id: str,
        after_seq: int,
        limit: int,
    ) -> list[dict[str, Any]]: ...

    def get_value(self, value_ref: str) -> Optional[dict[str, Any]]: ...

    def put_release(
        self,
        release_hash: str,
        application: str,
        manifest: Mapping[str, Any],
        created_at: float,
    ) -> None: ...

    def get_release(self, release_hash: str) -> Optional[dict[str, Any]]: ...

    def list_releases(
        self,
        cursor: Optional[str],
        limit: int,
    ) -> tuple[list[dict[str, Any]], Optional[str]]: ...

    def activate_deployment(
        self,
        lane: str,
        release_hash: str,
        activated_at: float,
        activated_by: str,
    ) -> None: ...

    def get_deployment(self, lane: str) -> Optional[dict[str, Any]]: ...

    def list_deployments(self) -> list[dict[str, Any]]: ...

    def put_secret(
        self,
        name: str,
        value: str,
        updated_by: str,
        cipher: SecretCipher,
    ) -> dict[str, Any]: ...

    def get_secret(self, name: str) -> Optional[dict[str, Any]]: ...

    def list_secrets(self) -> list[dict[str, Any]]: ...

    def archive_secret(self, name: str, updated_by: str) -> Optional[dict[str, Any]]: ...

    def delete_secret(self, name: str) -> bool: ...

    def secret_key_counts(self) -> dict[str, int]: ...

    def reencrypt_secrets(
        self,
        cipher: SecretCipher,
        progress: Optional[Callable[[int, int, str], None]] = None,
    ) -> dict[str, Any]: ...

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


def _bounded_list_limit(limit: int) -> int:
    return max(0, min(int(limit), MAX_LIST_LIMIT))


def _encode_cursor(timestamp: Optional[float], identifier: str) -> str:
    payload = canonical_json([timestamp, identifier]).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii")


def _decode_cursor(cursor: str) -> tuple[Optional[float], str]:
    try:
        raw: Any = json.loads(base64.urlsafe_b64decode(cursor.encode("ascii")))
    except (binascii.Error, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("invalid execution-store cursor") from exc
    if not isinstance(raw, list) or len(raw) != 2:
        raise ValueError("invalid execution-store cursor")
    timestamp = raw[0]
    identifier = raw[1]
    if timestamp is not None and (
        not isinstance(timestamp, (int, float)) or isinstance(timestamp, bool)
    ):
        raise ValueError("invalid execution-store cursor")
    if not isinstance(identifier, str):
        raise ValueError("invalid execution-store cursor")
    return None if timestamp is None else float(timestamp), identifier


def _row_is_after_cursor(
    timestamp: Optional[float],
    identifier: str,
    cursor_timestamp: Optional[float],
    cursor_identifier: str,
) -> bool:
    """Return whether a row follows a cursor in descending timestamp/id order."""
    if cursor_timestamp is None:
        return timestamp is None and identifier < cursor_identifier
    if timestamp is None:
        return True
    return timestamp < cursor_timestamp or (
        timestamp == cursor_timestamp and identifier < cursor_identifier
    )


def _principal_contains(
    principal: Any,
    subset: Mapping[str, Any],
) -> bool:
    return isinstance(principal, Mapping) and all(
        key in principal and principal[key] == value for key, value in subset.items()
    )


def _secret_metadata(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return the write-only vault record shape without ciphertext."""

    return {
        "name": str(row["name"]),
        "key_id": str(row["key_id"]),
        "generation": int(row["generation"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "updated_by": str(row["updated_by"]),
        "archived_at": row.get("archived_at"),
    }


class InMemoryExecutionStore:
    """Thread-safe, insertion-ordered execution store for tests and local use."""

    def __init__(self) -> None:
        self._runs: dict[str, dict[str, Any]] = {}
        self._events: dict[tuple[str, int, str], dict[str, Any]] = {}
        self._values: dict[str, dict[str, Any]] = {}
        self._releases: dict[str, dict[str, Any]] = {}
        self._deployments: dict[str, dict[str, Any]] = {}
        self._secrets: dict[str, dict[str, Any]] = {}
        self._next_event_seq = 1
        self._lock = threading.RLock()

    def apply_schema(self) -> None:
        return None

    def insert_events(self, events: Sequence[Mapping[str, Any]]) -> None:
        rows = [_normalise_event(event) for event in events]
        with self._lock:
            for row in rows:
                key = _event_key(row)
                if key not in self._events:
                    stored = copy.deepcopy(row)
                    stored["seq"] = self._next_event_seq
                    self._next_event_seq += 1
                    self._events[key] = stored
                run = self._runs.get(str(row["run_id"]))
                if run is not None and run.get("status") == "accepted":
                    # A persisted workflow event is stronger evidence than a
                    # Temporal describe poll: this execution is actively running.
                    run["status"] = "running"

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
            return None if run is None else copy.deepcopy(run)

    def create_run(
        self,
        *,
        run_id: str,
        idempotency_key: Optional[str],
        workflow_id: str,
        session_id: str,
        release_hash: str,
        pipeline: str,
        application: str,
        principal: Mapping[str, Any],
        input_ref: Optional[str],
        status: str = "submitting",
        started_at: float,
    ) -> Literal["created"] | dict[str, Any]:
        row = {
            "run_id": run_id,
            "idempotency_key": idempotency_key,
            "workflow_id": workflow_id,
            "temporal_run_id": None,
            "session_id": session_id,
            "release_hash": release_hash,
            "pipeline": pipeline,
            "application": application,
            "status": status,
            "principal": copy.deepcopy(dict(principal)),
            "input_ref": input_ref,
            "result_ref": None,
            "error": None,
            "started_at": float(started_at),
            "finished_at": None,
        }
        with self._lock:
            existing = self._runs.get(run_id)
            if existing is not None:
                return copy.deepcopy(existing)
            if idempotency_key is not None:
                for candidate in self._runs.values():
                    if candidate.get("idempotency_key") == idempotency_key:
                        return copy.deepcopy(candidate)
            self._runs[run_id] = row
        return "created"

    def set_run_status(
        self,
        run_id: str,
        status: str,
        *,
        temporal_run_id: Optional[str] = None,
        started_at: Optional[float] = None,
        finished_at: Optional[float] = None,
    ) -> None:
        predecessors = _RUN_STATUS_PREDECESSORS.get(status)
        if predecessors is None:
            raise ValueError(f"unsupported run status transition target {status!r}")
        with self._lock:
            run = self._runs.get(run_id)
            if run is None:
                return
            if run.get("status") in predecessors:
                run["status"] = status
            if temporal_run_id is not None:
                run["temporal_run_id"] = temporal_run_id
            if started_at is not None:
                run["started_at"] = float(started_at)
            if finished_at is not None and run.get("finished_at") is None:
                run["finished_at"] = float(finished_at)

    def list_runs(
        self,
        *,
        principal_subset: Optional[Mapping[str, Any]],
        cursor: Optional[str],
        limit: int,
    ) -> tuple[list[dict[str, Any]], Optional[str]]:
        bounded = _bounded_list_limit(limit)
        if bounded == 0:
            return [], None
        decoded_cursor = None if cursor is None else _decode_cursor(cursor)
        with self._lock:
            candidates = [
                run
                for run in self._runs.values()
                if principal_subset is None
                or _principal_contains(run.get("principal"), principal_subset)
            ]
            candidates.sort(
                key=lambda run: (
                    run.get("started_at") is not None,
                    0.0
                    if run.get("started_at") is None
                    else float(run["started_at"]),
                    str(run["run_id"]),
                ),
                reverse=True,
            )
            if decoded_cursor is not None:
                cursor_timestamp, cursor_run_id = decoded_cursor
                candidates = [
                    run
                    for run in candidates
                    if _row_is_after_cursor(
                        None
                        if run.get("started_at") is None
                        else float(run["started_at"]),
                        str(run["run_id"]),
                        cursor_timestamp,
                        cursor_run_id,
                    )
                ]
            page = candidates[: bounded + 1]
            has_more = len(page) > bounded
            page = page[:bounded]
            rows = [copy.deepcopy(run) for run in page]
            next_cursor = None
            if has_more:
                last = page[-1]
                last_started_at = last.get("started_at")
                next_cursor = _encode_cursor(
                    None if last_started_at is None else float(last_started_at),
                    str(last["run_id"]),
                )
        return rows, next_cursor

    def list_runs_by_status(self, status: str) -> list[dict[str, Any]]:
        with self._lock:
            candidates = [
                run for run in self._runs.values() if run.get("status") == status
            ]
            candidates.sort(
                key=lambda run: (
                    run.get("started_at") is not None,
                    0.0
                    if run.get("started_at") is None
                    else float(run["started_at"]),
                    str(run["run_id"]),
                ),
                reverse=True,
            )
            return [copy.deepcopy(run) for run in candidates]

    def get_run_by_idempotency_key(
        self,
        key: str,
    ) -> Optional[dict[str, Any]]:
        with self._lock:
            for run in self._runs.values():
                if run.get("idempotency_key") == key:
                    return copy.deepcopy(run)
        return None

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

    def put_release(
        self,
        release_hash: str,
        application: str,
        manifest: Mapping[str, Any],
        created_at: float,
    ) -> None:
        row = {
            "release_hash": release_hash,
            "application": application,
            "manifest": copy.deepcopy(dict(manifest)),
            "created_at": float(created_at),
        }
        with self._lock:
            self._releases.setdefault(release_hash, row)

    def get_release(self, release_hash: str) -> Optional[dict[str, Any]]:
        with self._lock:
            release = self._releases.get(release_hash)
            return None if release is None else copy.deepcopy(release)

    def list_releases(
        self,
        cursor: Optional[str],
        limit: int,
    ) -> tuple[list[dict[str, Any]], Optional[str]]:
        bounded = _bounded_list_limit(limit)
        if bounded == 0:
            return [], None
        decoded_cursor = None if cursor is None else _decode_cursor(cursor)
        with self._lock:
            candidates = sorted(
                self._releases.values(),
                key=lambda release: (
                    float(release["created_at"]),
                    str(release["release_hash"]),
                ),
                reverse=True,
            )
            if decoded_cursor is not None:
                cursor_timestamp, cursor_release_hash = decoded_cursor
                if cursor_timestamp is None:
                    raise ValueError("invalid release cursor")
                candidates = [
                    release
                    for release in candidates
                    if _row_is_after_cursor(
                        float(release["created_at"]),
                        str(release["release_hash"]),
                        cursor_timestamp,
                        cursor_release_hash,
                    )
                ]
            page = candidates[: bounded + 1]
            has_more = len(page) > bounded
            page = page[:bounded]
            rows = [copy.deepcopy(release) for release in page]
            next_cursor = None
            if has_more:
                last = page[-1]
                next_cursor = _encode_cursor(
                    float(last["created_at"]),
                    str(last["release_hash"]),
                )
        return rows, next_cursor

    def activate_deployment(
        self,
        lane: str,
        release_hash: str,
        activated_at: float,
        activated_by: str,
    ) -> None:
        row = {
            "lane": lane,
            "release_hash": release_hash,
            "activated_at": float(activated_at),
            "activated_by": activated_by,
        }
        with self._lock:
            self._deployments[lane] = row

    def get_deployment(self, lane: str) -> Optional[dict[str, Any]]:
        with self._lock:
            deployment = self._deployments.get(lane)
            return None if deployment is None else dict(deployment)

    def list_deployments(self) -> list[dict[str, Any]]:
        with self._lock:
            return [
                dict(self._deployments[lane]) for lane in sorted(self._deployments)
            ]

    def put_secret(
        self,
        name: str,
        value: str,
        updated_by: str,
        cipher: SecretCipher,
    ) -> dict[str, Any]:
        with self._lock:
            previous = self._secrets.get(name)
            generation = 1 if previous is None else int(previous["generation"]) + 1
            ciphertext, key_id = cipher.encrypt(name, generation, value)
            now = datetime.now(timezone.utc)
            row = {
                "name": name,
                "ciphertext": bytes(ciphertext),
                "key_id": key_id,
                "generation": generation,
                "created_at": now if previous is None else previous["created_at"],
                "updated_at": now,
                "updated_by": updated_by,
                "archived_at": None,
            }
            self._secrets[name] = row
            return _secret_metadata(row)

    def get_secret(self, name: str) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self._secrets.get(name)
            return None if row is None else copy.deepcopy(row)

    def list_secrets(self) -> list[dict[str, Any]]:
        with self._lock:
            return [
                _secret_metadata(self._secrets[name])
                for name in sorted(self._secrets)
            ]

    def archive_secret(self, name: str, updated_by: str) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self._secrets.get(name)
            if row is None:
                return None
            now = datetime.now(timezone.utc)
            row.update(
                ciphertext=None,
                archived_at=now,
                updated_at=now,
                updated_by=updated_by,
            )
            return _secret_metadata(row)

    def delete_secret(self, name: str) -> bool:
        with self._lock:
            return self._secrets.pop(name, None) is not None

    def secret_key_counts(self) -> dict[str, int]:
        with self._lock:
            counts: dict[str, int] = {}
            for row in self._secrets.values():
                key_id = str(row["key_id"])
                counts[key_id] = counts.get(key_id, 0) + 1
            return dict(sorted(counts.items()))

    def reencrypt_secrets(
        self,
        cipher: SecretCipher,
        progress: Optional[Callable[[int, int, str], None]] = None,
    ) -> dict[str, Any]:
        with self._lock:
            active_runs = sorted(
                run_id
                for run_id, row in self._runs.items()
                if row.get("status") not in _RETENTION_RUN_STATUSES
            )
            if active_runs:
                raise RuntimeError(
                    "cannot re-encrypt secrets while non-terminal runs exist: "
                    + ", ".join(active_runs[:5])
                )
            rows = [self._secrets[name] for name in sorted(self._secrets)]
            total = len(rows)
            reencrypted = 0
            for index, row in enumerate(rows, start=1):
                if row["ciphertext"] is None:
                    # Archived records retain audit metadata but no key-dependent
                    # bytes. Move their marker so the old key can reach zero refs.
                    row["key_id"] = cipher.active_key_id
                else:
                    value = cipher.decrypt(
                        str(row["name"]),
                        int(row["generation"]),
                        bytes(row["ciphertext"]),
                        str(row["key_id"]),
                    )
                    ciphertext, key_id = cipher.encrypt(
                        str(row["name"]), int(row["generation"]), value
                    )
                    row["ciphertext"] = bytes(ciphertext)
                    row["key_id"] = key_id
                    reencrypted += 1
                if progress is not None:
                    progress(index, total, str(row["name"]))
            return {
                "total": total,
                "reencrypted": reencrypted,
                "metadata_updated": total - reencrypted,
                "active_key_id": cipher.active_key_id,
                "remaining_key_ids": self.secret_key_counts(),
            }

    def sweep(self, older_than_s: float) -> int:
        if older_than_s < 0:
            raise ValueError("older_than_s must be non-negative")
        cutoff = time.time() - older_than_s
        with self._lock:
            expired_run_ids = {
                run_id
                for run_id, run in self._runs.items()
                if run.get("status") in _RETENTION_RUN_STATUSES
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
            candidate_refs.update(
                str(self._runs[run_id]["input_ref"])
                for run_id in expired_run_ids
                if self._runs[run_id].get("input_ref") is not None
            )

            for key in event_keys:
                del self._events[key]
            for run_id in expired_run_ids:
                self._runs[run_id]["result_ref"] = None
                self._runs[run_id]["input_ref"] = None

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
            referenced_refs.update(
                str(run["input_ref"])
                for run in self._runs.values()
                if run.get("input_ref") is not None
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
    _CREATE_RUN_SQL = """
        INSERT INTO runs (
            run_id, idempotency_key, workflow_id, temporal_run_id, session_id,
            release_hash, pipeline, application, status, principal, input_ref,
            result_ref, error, started_at, finished_at
        ) VALUES (
            %s, %s, %s, NULL, %s, %s, %s, %s, %s, %s, %s, NULL, NULL, %s, NULL
        )
        ON CONFLICT DO NOTHING
        RETURNING run_id
    """
    _INSERT_RELEASE_SQL = """
        INSERT INTO releases (
            release_hash, application, manifest, created_at
        ) VALUES (%s, %s, %s, %s)
        ON CONFLICT (release_hash) DO NOTHING
    """
    _ACTIVATE_DEPLOYMENT_SQL = """
        INSERT INTO deployments (
            lane, release_hash, activated_at, activated_by
        ) VALUES (%s, %s, %s, %s)
        ON CONFLICT (lane) DO UPDATE SET
            release_hash = EXCLUDED.release_hash,
            activated_at = EXCLUDED.activated_at,
            activated_by = EXCLUDED.activated_by
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
                cur.execute(
                    """
                    UPDATE runs SET status = 'running'
                    WHERE run_id = ANY(%s) AND status = ANY(%s)
                    """,
                    (
                        sorted({str(row["run_id"]) for row in rows}),
                        ["accepted"],
                    ),
                )

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

    def create_run(
        self,
        *,
        run_id: str,
        idempotency_key: Optional[str],
        workflow_id: str,
        session_id: str,
        release_hash: str,
        pipeline: str,
        application: str,
        principal: Mapping[str, Any],
        input_ref: Optional[str],
        status: str = "submitting",
        started_at: float,
    ) -> Literal["created"] | dict[str, Any]:
        from psycopg.types.json import Jsonb

        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(
                        self._CREATE_RUN_SQL,
                        (
                            run_id,
                            idempotency_key,
                            workflow_id,
                            session_id,
                            release_hash,
                            pipeline,
                            application,
                            status,
                            Jsonb(dict(principal)),
                            input_ref,
                            float(started_at),
                        ),
                    )
                    if cur.fetchone() is not None:
                        return "created"
                    if idempotency_key is None:
                        cur.execute(
                            "SELECT * FROM runs WHERE run_id = %s",
                            (run_id,),
                        )
                    else:
                        cur.execute(
                            """
                            SELECT * FROM runs
                            WHERE run_id = %s OR idempotency_key = %s
                            ORDER BY CASE WHEN run_id = %s THEN 0 ELSE 1 END
                            LIMIT 1
                            """,
                            (run_id, idempotency_key, run_id),
                        )
                    existing = cur.fetchone()
        if existing is None:
            raise RuntimeError("run conflict did not resolve to an existing row")
        return dict(existing)

    def set_run_status(
        self,
        run_id: str,
        status: str,
        *,
        temporal_run_id: Optional[str] = None,
        started_at: Optional[float] = None,
        finished_at: Optional[float] = None,
    ) -> None:
        predecessors = _RUN_STATUS_PREDECESSORS.get(status)
        if predecessors is None:
            raise ValueError(f"unsupported run status transition target {status!r}")
        assignments = ["status = CASE WHEN status = ANY(%s) THEN %s ELSE status END"]
        params: list[Any] = [list(predecessors), status]
        if temporal_run_id is not None:
            assignments.append("temporal_run_id = %s")
            params.append(temporal_run_id)
        if started_at is not None:
            assignments.append("started_at = %s")
            params.append(float(started_at))
        if finished_at is not None:
            assignments.append("finished_at = COALESCE(finished_at, %s)")
            params.append(float(finished_at))
        params.append(run_id)
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE runs SET {', '.join(assignments)} WHERE run_id = %s",
                    tuple(params),
                )

    def list_runs(
        self,
        *,
        principal_subset: Optional[Mapping[str, Any]],
        cursor: Optional[str],
        limit: int,
    ) -> tuple[list[dict[str, Any]], Optional[str]]:
        from psycopg.types.json import Jsonb

        bounded = _bounded_list_limit(limit)
        if bounded == 0:
            return [], None
        decoded_cursor = None if cursor is None else _decode_cursor(cursor)
        conditions: list[str] = []
        params: list[Any] = []
        if principal_subset is not None:
            conditions.append(
                "principal IS NOT NULL "
                "AND jsonb_typeof(principal) = 'object' "
                "AND NOT EXISTS ("
                "SELECT 1 FROM jsonb_each(%s::jsonb) AS expected(key, value) "
                "WHERE principal -> expected.key IS DISTINCT FROM expected.value"
                ")"
            )
            params.append(Jsonb(dict(principal_subset)))
        if decoded_cursor is not None:
            cursor_timestamp, cursor_run_id = decoded_cursor
            if cursor_timestamp is None:
                conditions.append("started_at IS NULL AND run_id < %s")
                params.append(cursor_run_id)
            else:
                conditions.append(
                    "(started_at < %s OR (started_at = %s AND run_id < %s) "
                    "OR started_at IS NULL)"
                )
                params.extend((cursor_timestamp, cursor_timestamp, cursor_run_id))
        where_clause = "" if not conditions else " WHERE " + " AND ".join(conditions)
        params.append(bounded + 1)
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM runs"
                    + where_clause
                    + " ORDER BY started_at DESC NULLS LAST, run_id DESC LIMIT %s",
                    tuple(params),
                )
                fetched = cur.fetchall()
        has_more = len(fetched) > bounded
        fetched = fetched[:bounded]
        rows = [dict(row) for row in fetched]
        next_cursor = None
        if has_more:
            last = fetched[-1]
            last_started_at = last["started_at"]
            next_cursor = _encode_cursor(
                None if last_started_at is None else float(last_started_at),
                str(last["run_id"]),
            )
        return rows, next_cursor

    def list_runs_by_status(self, status: str) -> list[dict[str, Any]]:
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM runs
                    WHERE status = %s
                    ORDER BY started_at DESC NULLS LAST, run_id DESC
                    """,
                    (status,),
                )
                rows = cur.fetchall()
        return [dict(row) for row in rows]

    def get_run_by_idempotency_key(
        self,
        key: str,
    ) -> Optional[dict[str, Any]]:
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM runs WHERE idempotency_key = %s",
                    (key,),
                )
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

    def put_release(
        self,
        release_hash: str,
        application: str,
        manifest: Mapping[str, Any],
        created_at: float,
    ) -> None:
        from psycopg.types.json import Jsonb

        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    self._INSERT_RELEASE_SQL,
                    (
                        release_hash,
                        application,
                        Jsonb(dict(manifest)),
                        float(created_at),
                    ),
                )

    def get_release(self, release_hash: str) -> Optional[dict[str, Any]]:
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM releases WHERE release_hash = %s",
                    (release_hash,),
                )
                row = cur.fetchone()
        return None if row is None else dict(row)

    def list_releases(
        self,
        cursor: Optional[str],
        limit: int,
    ) -> tuple[list[dict[str, Any]], Optional[str]]:
        bounded = _bounded_list_limit(limit)
        if bounded == 0:
            return [], None
        decoded_cursor = None if cursor is None else _decode_cursor(cursor)
        params: list[Any] = []
        where_clause = ""
        if decoded_cursor is not None:
            cursor_timestamp, cursor_release_hash = decoded_cursor
            if cursor_timestamp is None:
                raise ValueError("invalid release cursor")
            where_clause = (
                " WHERE created_at < %s "
                "OR (created_at = %s AND release_hash < %s)"
            )
            params.extend((cursor_timestamp, cursor_timestamp, cursor_release_hash))
        params.append(bounded + 1)
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM releases"
                    + where_clause
                    + " ORDER BY created_at DESC, release_hash DESC LIMIT %s",
                    tuple(params),
                )
                fetched = cur.fetchall()
        has_more = len(fetched) > bounded
        fetched = fetched[:bounded]
        rows = [dict(row) for row in fetched]
        next_cursor = None
        if has_more:
            last = fetched[-1]
            next_cursor = _encode_cursor(
                float(last["created_at"]),
                str(last["release_hash"]),
            )
        return rows, next_cursor

    def activate_deployment(
        self,
        lane: str,
        release_hash: str,
        activated_at: float,
        activated_by: str,
    ) -> None:
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    self._ACTIVATE_DEPLOYMENT_SQL,
                    (lane, release_hash, float(activated_at), activated_by),
                )

    def get_deployment(self, lane: str) -> Optional[dict[str, Any]]:
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM deployments WHERE lane = %s",
                    (lane,),
                )
                row = cur.fetchone()
        return None if row is None else dict(row)

    def list_deployments(self) -> list[dict[str, Any]]:
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM deployments ORDER BY lane")
                rows = cur.fetchall()
        return [dict(row) for row in rows]

    def put_secret(
        self,
        name: str,
        value: str,
        updated_by: str,
        cipher: SecretCipher,
    ) -> dict[str, Any]:
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    # Serialize writers for one logical name even before its first row
                    # exists. Generation is authenticated AAD, so selecting it and
                    # encrypting must be one atomic operation.
                    cur.execute(
                        "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                        (name,),
                    )
                    cur.execute(
                        "SELECT generation FROM secrets WHERE name = %s FOR UPDATE",
                        (name,),
                    )
                    previous = cur.fetchone()
                    generation = (
                        1 if previous is None else int(previous["generation"]) + 1
                    )
                    ciphertext, key_id = cipher.encrypt(name, generation, value)
                    cur.execute(
                        """
                        INSERT INTO secrets (
                            name, ciphertext, key_id, generation, created_at,
                            updated_at, updated_by, archived_at
                        ) VALUES (
                            %s, %s, %s, %s, clock_timestamp(),
                            clock_timestamp(), %s, NULL
                        )
                        ON CONFLICT (name) DO UPDATE SET
                            ciphertext = EXCLUDED.ciphertext,
                            key_id = EXCLUDED.key_id,
                            generation = EXCLUDED.generation,
                            updated_at = EXCLUDED.updated_at,
                            updated_by = EXCLUDED.updated_by,
                            archived_at = NULL
                        RETURNING *
                        """,
                        (name, ciphertext, key_id, generation, updated_by),
                    )
                    row = cur.fetchone()
        assert row is not None
        return _secret_metadata(dict(row))

    def get_secret(self, name: str) -> Optional[dict[str, Any]]:
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM secrets WHERE name = %s", (name,))
                row = cur.fetchone()
        return None if row is None else dict(row)

    def list_secrets(self) -> list[dict[str, Any]]:
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM secrets ORDER BY name")
                rows = cur.fetchall()
        return [_secret_metadata(dict(row)) for row in rows]

    def archive_secret(self, name: str, updated_by: str) -> Optional[dict[str, Any]]:
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE secrets SET
                        ciphertext = NULL,
                        archived_at = clock_timestamp(),
                        updated_at = clock_timestamp(),
                        updated_by = %s
                    WHERE name = %s
                    RETURNING *
                    """,
                    (updated_by, name),
                )
                row = cur.fetchone()
        return None if row is None else _secret_metadata(dict(row))

    def delete_secret(self, name: str) -> bool:
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM secrets WHERE name = %s", (name,))
                return bool(cur.rowcount)

    def secret_key_counts(self) -> dict[str, int]:
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT key_id, count(*) AS count
                    FROM secrets
                    GROUP BY key_id
                    ORDER BY key_id
                    """
                )
                rows = cur.fetchall()
        return {str(row["key_id"]): int(row["count"]) for row in rows}

    def reencrypt_secrets(
        self,
        cipher: SecretCipher,
        progress: Optional[Callable[[int, int, str], None]] = None,
    ) -> dict[str, Any]:
        pool = self._pool_instance()
        with pool.connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    # This is intentionally a maintenance-window operation. The
                    # lock blocks both run submissions and vault writes for the
                    # complete sweep; operators stop submitters before invoking it.
                    cur.execute(
                        "LOCK TABLE runs, secrets IN ACCESS EXCLUSIVE MODE"
                    )
                    cur.execute(
                        """
                        SELECT run_id FROM runs
                        WHERE NOT (status = ANY(%s))
                        ORDER BY run_id
                        LIMIT 5
                        """,
                        (sorted(_RETENTION_RUN_STATUSES),),
                    )
                    active_runs = [str(row["run_id"]) for row in cur.fetchall()]
                    if active_runs:
                        raise RuntimeError(
                            "cannot re-encrypt secrets while non-terminal runs exist: "
                            + ", ".join(active_runs)
                        )
                    cur.execute(
                        """
                        SELECT name, ciphertext, key_id, generation
                        FROM secrets
                        ORDER BY name
                        """
                    )
                    rows = cur.fetchall()
                    total = len(rows)
                    reencrypted = 0
                    for index, row in enumerate(rows, start=1):
                        name = str(row["name"])
                        generation = int(row["generation"])
                        if row["ciphertext"] is None:
                            cur.execute(
                                """
                                UPDATE secrets SET key_id = %s
                                WHERE name = %s AND generation = %s
                                """,
                                (cipher.active_key_id, name, generation),
                            )
                        else:
                            value = cipher.decrypt(
                                name,
                                generation,
                                bytes(row["ciphertext"]),
                                str(row["key_id"]),
                            )
                            ciphertext, key_id = cipher.encrypt(
                                name, generation, value
                            )
                            cur.execute(
                                """
                                UPDATE secrets SET ciphertext = %s, key_id = %s
                                WHERE name = %s AND generation = %s
                                """,
                                (ciphertext, key_id, name, generation),
                            )
                            reencrypted += 1
                        if progress is not None:
                            progress(index, total, name)
                    cur.execute(
                        """
                        SELECT key_id, count(*) AS count
                        FROM secrets
                        GROUP BY key_id
                        ORDER BY key_id
                        """
                    )
                    remaining = {
                        str(row["key_id"]): int(row["count"])
                        for row in cur.fetchall()
                    }
        return {
            "total": total,
            "reencrypted": reencrypted,
            "metadata_updated": total - reencrypted,
            "active_key_id": cipher.active_key_id,
            "remaining_key_ids": remaining,
        }

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
                            UNION
                            SELECT input_ref AS value_ref
                            FROM runs
                            WHERE status = ANY(%s)
                              AND finished_at < %s
                              AND input_ref IS NOT NULL
                        ) AS expired_refs
                        """,
                        (
                            list(_RETENTION_RUN_STATUSES),
                            cutoff,
                            list(_RETENTION_RUN_STATUSES),
                            cutoff,
                            list(_RETENTION_RUN_STATUSES),
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
                        (list(_RETENTION_RUN_STATUSES), cutoff),
                    )
                    deleted_events = int(cur.rowcount)
                    cur.execute(
                        """
                        UPDATE runs SET result_ref = NULL, input_ref = NULL
                        WHERE status = ANY(%s) AND finished_at < %s
                        """,
                        (list(_RETENTION_RUN_STATUSES), cutoff),
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
                              AND NOT EXISTS (
                                  SELECT 1 FROM runs AS run
                                  WHERE run.input_ref = value.value_ref
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


def _capture_value(
    raw_value: Any,
    secrets: Optional[Mapping[str, str]] = None,
) -> Optional[_CapturedValue]:
    redactor = effects._scoped_redactor(secrets)
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


def _redact_projection_metadata(
    event: Mapping[str, Any],
    secrets: Optional[Mapping[str, str]],
) -> dict[str, Any]:
    """Scrub non-value diagnostic fields before projection persistence."""
    out = dict(event)
    redactor = effects._scoped_redactor(secrets)
    for key in ("error", "attrs"):
        if key not in out:
            continue
        redacted = redact_for_capture(redactor, out[key])
        out[key] = None if redacted is _REDACTION_DROP else redacted
    return out


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
        candidate = _redact_projection_metadata(candidate, inp.get("secrets"))
        captured = (
            _capture_value(candidate["rawValue"], inp.get("secrets"))
            if "rawValue" in candidate
            else None
        )
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
    if terminal_candidate is not None:
        terminal_candidate = _redact_projection_metadata(
            terminal_candidate, inp.get("secrets")
        )

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
    captured = _capture_value(raw_value, inp.get("secrets")) if raw_present else None
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
    raw_error = inp.get("error")
    if raw_error is not None:
        raw_error = redact_for_capture(
            effects._scoped_redactor(inp.get("secrets")), str(raw_error)
        )
        if raw_error is _REDACTION_DROP:
            raw_error = None
    store.finalize_run(
        run_id=run_id,
        workflow_id=workflow_id,
        segment_seq=segment_seq,
        status=str(inp["status"]),
        terminal_event=terminal_event,
        result_payload=None if captured is None else captured.payload,
        result_byte_len=0 if captured is None else captured.byte_len,
        result_oversize=False if captured is None else captured.oversize,
        error=None if raw_error is None else str(raw_error),
        finished_at=float(finished_at_value),
    )
