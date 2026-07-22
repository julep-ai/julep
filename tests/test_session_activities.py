"""T5 — state + blob activities (durable-session-store design, "Activities").

The session/blob I/O lives in activities because workflow code is deterministic
and ambient I/O in it is replay-unsafe. These tests drive the three activities
through ``temporalio.testing.ActivityEnvironment`` against a ``WorkerContext``
configured with the in-memory reference stores, and assert that:

* ``commitState(base=0)`` returns cursor 1, and ``loadState(cursor=1)`` round-
  trips the committed state JSON;
* ``putBlob`` returns a content-addressed ref that the blob store resolves, and
  the ref matches ``SessionStore.put_blob`` for the same value (shared
  compact canonical JSON serialization);
* each activity fails when its backing store is ``None``; secret-bearing
  ``putBlob`` crosses the activity boundary as a sanitized ``ApplicationError``.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from julep import HAVE_TEMPORAL

pytestmark = pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")

if HAVE_TEMPORAL:
    from temporalio.exceptions import ApplicationError
    from temporalio.testing import ActivityEnvironment

    from julep import agent_loop as al
    from julep.execution import activities
    from julep.execution.activities import (
        CommitStateInput,
        LoadStateInput,
        PutBlobInput,
        WorkerContext,
        commitState,
        loadState,
        putBlob,
    )
    from julep.execution.blobstore import InMemoryBlobStore
    from julep.execution.session_store import InMemorySessionStore


def _run(coro: Any) -> Any:
    return asyncio.new_event_loop().run_until_complete(coro)


async def _drive(fn: Any, inp: Any) -> Any:
    return await ActivityEnvironment().run(fn, inp)


def _make_state() -> "al.AgentState":
    state = al.AgentState(round=2, spent=1.5, last={"answer": 42})
    state.call_counts["search"] = 3
    return state


def test_commit_then_load_round_trips() -> None:
    session_store = InMemorySessionStore()
    blob_store = InMemoryBlobStore()
    activities.configure(WorkerContext(session_store=session_store, blob_store=blob_store))
    try:
        state = _make_state()
        state_hash = al.state_fingerprint(state)

        cursor = _run(
            _drive(
                commitState,
                CommitStateInput(
                    session_id="s1",
                    base=0,
                    state=state.to_json(),
                    state_hash=state_hash,
                ),
            )
        )
        assert cursor == 1

        loaded = _run(_drive(loadState, LoadStateInput(session_id="s1", cursor=1)))
        assert loaded == state.to_json()
    finally:
        activities.configure(WorkerContext())


def test_put_blob_is_content_addressed_and_resolvable() -> None:
    session_store = InMemorySessionStore()
    blob_store = InMemoryBlobStore()
    activities.configure(WorkerContext(session_store=session_store, blob_store=blob_store))
    try:
        value = {"b": 2, "a": [1, 2, 3]}
        ref = _run(_drive(putBlob, PutBlobInput(tenant="acme", value=value)))

        # Content-addressed, tenant-scoped ref shape.
        assert ref.startswith("acme/sha256:")

        # The blob store resolves the ref back to the serialized bytes.
        resolved = _run(blob_store.get("acme", ref))
        assert json.loads(resolved.decode()) == value

        # Same serialization as SessionStore.put_blob -> identical ref.
        store_ref = _run(session_store.put_blob("acme", value))
        assert store_ref == ref
    finally:
        activities.configure(WorkerContext())


def test_load_state_requires_session_store() -> None:
    activities.configure(WorkerContext(blob_store=InMemoryBlobStore()))
    try:
        with pytest.raises(RuntimeError):
            _run(_drive(loadState, LoadStateInput(session_id="s1", cursor=1)))
    finally:
        activities.configure(WorkerContext())


def test_commit_state_requires_session_store() -> None:
    activities.configure(WorkerContext(blob_store=InMemoryBlobStore()))
    try:
        state = _make_state()
        with pytest.raises(RuntimeError):
            _run(
                _drive(
                    commitState,
                    CommitStateInput(
                        session_id="s1",
                        base=0,
                        state=state.to_json(),
                        state_hash=al.state_fingerprint(state),
                    ),
                )
            )
    finally:
        activities.configure(WorkerContext())


def test_put_blob_requires_blob_store() -> None:
    activities.configure(WorkerContext(session_store=InMemorySessionStore()))
    try:
        with pytest.raises(ApplicationError) as captured:
            _run(_drive(putBlob, PutBlobInput(tenant="acme", value={"x": 1})))
        assert captured.value.type == "RuntimeError"
        assert "worker has no blob store configured" in str(captured.value)
    finally:
        activities.configure(WorkerContext())
