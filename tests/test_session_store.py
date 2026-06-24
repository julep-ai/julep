"""Tests for the optional first-class SessionStore (design note "Optional: a
first-class SessionStore", invariants 1-3 of
``docs/design/durable-session-store.md``).

The store is pure (no Temporal); async methods are driven via ``asyncio.run``
inside sync test functions — the repo has no asyncio pytest plugin (see
tests/test_blobstore.py for the pattern).
"""

from __future__ import annotations

import asyncio
import json

import pytest

from composable_agents import agent_loop as al
from composable_agents.execution.blobstore import (
    BlobIntegrityError,
    InMemoryBlobStore,
)
from composable_agents.execution.session_store import (
    CursorConflict,
    InMemorySessionStore,
    SessionStoreError,
    value_fingerprint,
)


def _state(round: int, last: object) -> al.AgentState:
    return al.AgentState(round=round, spent=float(round), last=last)


# --------------------------------------------------------------------------- #
# generic JSON carrier fingerprint
# --------------------------------------------------------------------------- #
def test_value_fingerprint_matches_agent_state_fingerprint() -> None:
    state = _state(2, {"answer": [1, 2, 3]})
    state.trace.append(al.TraceEntry(decision="plan", ref="think", output_ref="out"))
    state.call_counts["think"] = 1

    assert value_fingerprint(state.to_json()) == al.state_fingerprint(state)


# --------------------------------------------------------------------------- #
# load
# --------------------------------------------------------------------------- #
def test_load_unknown_cursor_zero_returns_fresh_state() -> None:
    store = InMemorySessionStore()

    async def go() -> al.AgentState:
        return await store.load("s1", 0)

    fresh = asyncio.run(go())
    # A fresh AgentState: round 0, no spend, no trace, empty call counts.
    assert fresh.round == 0
    assert fresh.spent == 0.0
    assert fresh.last is None
    assert fresh.trace == []
    assert fresh.call_counts == {}


def test_load_unknown_session_nonzero_cursor_raises() -> None:
    store = InMemorySessionStore()

    async def go() -> al.AgentState:
        return await store.load("nope", 7)

    with pytest.raises(SessionStoreError):
        asyncio.run(go())


# --------------------------------------------------------------------------- #
# commit from base 0 -> cursor 1, then load it back
# --------------------------------------------------------------------------- #
def test_first_commit_from_base_zero_returns_cursor_one() -> None:
    store = InMemorySessionStore()
    state = _state(1, {"answer": 42})
    h = al.state_fingerprint(state)

    async def go() -> tuple[int, al.AgentState]:
        cursor = await store.commit("s1", 0, state, h)
        loaded = await store.load("s1", cursor)
        return cursor, loaded

    cursor, loaded = asyncio.run(go())
    assert cursor == 1
    assert loaded.round == 1
    assert loaded.last == {"answer": 42}
    assert al.state_fingerprint(loaded) == h


# --------------------------------------------------------------------------- #
# sequential commits 0 -> 1 -> 2
# --------------------------------------------------------------------------- #
def test_sequential_commits_advance_cursor() -> None:
    store = InMemorySessionStore()
    s1 = _state(1, "one")
    s2 = _state(2, "two")

    async def go() -> tuple[int, int, al.AgentState]:
        c1 = await store.commit("s1", 0, s1, al.state_fingerprint(s1))
        c2 = await store.commit("s1", c1, s2, al.state_fingerprint(s2))
        loaded = await store.load("s1", c2)
        return c1, c2, loaded

    c1, c2, loaded = asyncio.run(go())
    assert c1 == 1
    assert c2 == 2
    assert loaded.last == "two"
    assert loaded.round == 2


def test_load_intermediate_cursor_returns_that_revision() -> None:
    store = InMemorySessionStore()
    s1 = _state(1, "one")
    s2 = _state(2, "two")

    async def go() -> al.AgentState:
        c1 = await store.commit("s1", 0, s1, al.state_fingerprint(s1))
        await store.commit("s1", c1, s2, al.state_fingerprint(s2))
        return await store.load("s1", 1)

    loaded = asyncio.run(go())
    assert loaded.last == "one"
    assert loaded.round == 1


# --------------------------------------------------------------------------- #
# idempotent replay (invariant 2): same (base, state_hash) -> same cursor
# --------------------------------------------------------------------------- #
def test_idempotent_replay_returns_same_cursor_and_one_revision() -> None:
    store = InMemorySessionStore()
    state = _state(1, "x")
    h = al.state_fingerprint(state)

    async def go() -> tuple[int, int]:
        first = await store.commit("s1", 0, state, h)
        # Temporal retried a committed write: same base, same hash.
        second = await store.commit("s1", 0, state, h)
        return first, second

    first, second = asyncio.run(go())
    assert first == 1
    assert second == 1
    # Only one revision was actually appended.

    async def head() -> al.AgentState:
        return await store.load("s1", 2)

    with pytest.raises(SessionStoreError):
        asyncio.run(head())


# --------------------------------------------------------------------------- #
# CursorConflict (invariant 1): stale base + different hash
# --------------------------------------------------------------------------- #
def test_cursor_conflict_on_stale_base_with_different_hash() -> None:
    store = InMemorySessionStore()
    s1 = _state(1, "one")
    s_fork = _state(1, "different")

    async def go() -> None:
        await store.commit("s1", 0, s1, al.state_fingerprint(s1))
        # head is now 1; committing against stale base 0 with a different hash forks.
        await store.commit("s1", 0, s_fork, al.state_fingerprint(s_fork))

    with pytest.raises(CursorConflict):
        asyncio.run(go())


def test_cursor_conflict_is_a_session_store_error() -> None:
    assert issubclass(CursorConflict, SessionStoreError)


# --------------------------------------------------------------------------- #
# defensive: state_hash must match the state's own fingerprint
# --------------------------------------------------------------------------- #
def test_commit_rejects_mismatched_state_hash() -> None:
    store = InMemorySessionStore()
    state = _state(1, "x")

    async def go() -> int:
        return await store.commit("s1", 0, state, "deadbeef")

    with pytest.raises(SessionStoreError):
        asyncio.run(go())


# --------------------------------------------------------------------------- #
# generic JSON carrier load/commit
# --------------------------------------------------------------------------- #
def test_commit_value_round_trips_arbitrary_json_carrier() -> None:
    store = InMemorySessionStore()
    value = {
        "channel_buffers": {"human": [{"seq": 1, "msg": "hi"}]},
        "s": [1, 2, 3],
    }

    async def go() -> tuple[int, object]:
        cursor = await store.commit_value("s1", 0, value, value_fingerprint(value))
        loaded = await store.load_value("s1", cursor)
        return cursor, loaded

    cursor, loaded = asyncio.run(go())
    assert cursor == 1
    assert loaded == value


def test_commit_value_idempotent_replay_returns_same_cursor_and_one_revision() -> None:
    store = InMemorySessionStore()
    value = {"channel_buffers": {"human": [{"seq": 1, "msg": "hi"}]}}
    h = value_fingerprint(value)

    async def go() -> tuple[int, int]:
        first = await store.commit_value("s1", 0, value, h)
        second = await store.commit_value("s1", 0, value, h)
        return first, second

    first, second = asyncio.run(go())
    assert first == 1
    assert second == 1

    async def head() -> object:
        return await store.load_value("s1", 2)

    with pytest.raises(SessionStoreError):
        asyncio.run(head())


def test_commit_value_cursor_conflict_on_stale_base_with_different_hash() -> None:
    store = InMemorySessionStore()

    async def go() -> None:
        await store.commit_value("s1", 0, {"x": 1}, value_fingerprint({"x": 1}))
        await store.commit_value("s1", 0, {"x": 2}, value_fingerprint({"x": 2}))

    with pytest.raises(CursorConflict):
        asyncio.run(go())


def test_agent_state_round_trips_via_typed_caller() -> None:
    store = InMemorySessionStore()
    state = _state(3, {"status": "ok"})
    h = al.state_fingerprint(state)

    async def go() -> al.AgentState:
        cursor = await store.commit("s1", 0, state, h)
        return await store.load("s1", cursor)

    loaded = asyncio.run(go())
    assert loaded == state


def test_commit_value_rejects_non_json_carrier() -> None:
    store = InMemorySessionStore()
    value = {"x": object()}

    async def go() -> int:
        return await store.commit_value("s1", 0, value, "deadbeef")

    with pytest.raises(TypeError):
        asyncio.run(go())


def test_commit_value_validates_configured_json_schema() -> None:
    pytest.importorskip("jsonschema")
    store = InMemorySessionStore(state_schema={"type": "object", "required": ["x"]})
    valid = {"x": 1}
    invalid = {"y": 1}

    async def commit_valid() -> int:
        return await store.commit_value("s1", 0, valid, value_fingerprint(valid))

    cursor = asyncio.run(commit_valid())
    assert cursor == 1

    async def commit_invalid() -> int:
        return await store.commit_value(
            "s1", cursor, invalid, value_fingerprint(invalid)
        )

    with pytest.raises(SessionStoreError):
        asyncio.run(commit_invalid())


# --------------------------------------------------------------------------- #
# blob round-trip + integrity
# --------------------------------------------------------------------------- #
def test_put_get_blob_value_round_trip() -> None:
    store = InMemorySessionStore()
    value = {"b": 2, "a": [1, 2, 3], "nested": {"k": "v"}}

    async def go() -> object:
        ref = await store.put_blob("acme", value)
        return await store.get_blob("acme", ref)

    assert asyncio.run(go()) == value


def test_put_blob_uses_sorted_keys_for_dedup() -> None:
    blobs = InMemoryBlobStore()
    store = InMemorySessionStore(blobs)

    async def go() -> tuple[str, str]:
        ref1 = await store.put_blob("acme", {"a": 1, "b": 2})
        ref2 = await store.put_blob("acme", {"b": 2, "a": 1})
        return ref1, ref2

    ref1, ref2 = asyncio.run(go())
    # sort_keys makes key order irrelevant: identical content-addressed ref.
    assert ref1 == ref2


def test_get_blob_raises_on_corrupted_underlying_blob() -> None:
    blobs = InMemoryBlobStore()
    store = InMemorySessionStore(blobs)
    value = {"trust": "me"}

    ref = asyncio.run(store.put_blob("acme", value))
    # Corrupt the backing bytes via the blob store's test seam.
    blobs._blobs[ref] = b"corrupted-not-json"

    async def go() -> object:
        return await store.get_blob("acme", ref)

    with pytest.raises(BlobIntegrityError):
        asyncio.run(go())


def test_get_blob_returns_json_decoded_value() -> None:
    blobs = InMemoryBlobStore()
    store = InMemorySessionStore(blobs)

    async def go() -> tuple[str, object]:
        ref = await store.put_blob("acme", [1, 2, 3])
        # The ref must address the canonical sorted-keys JSON bytes.
        raw = await blobs.get("acme", ref)
        return ref, json.loads(raw)

    ref, decoded = asyncio.run(go())
    assert decoded == [1, 2, 3]
