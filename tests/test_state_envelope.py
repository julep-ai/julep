"""AgentState schema/version envelope + commit-idempotency fingerprint.

Covers design invariant 3 of ``docs/design/durable-session-store.md``: stored
``AgentState`` carries a schema/version envelope, and ``state_fingerprint`` is a
stable content hash the SessionStore can key commit idempotency on.

Pure module — no Temporal, no asyncio.
"""

from __future__ import annotations

import json

import pytest

from composable_agents.agent_loop import (
    STATE_SCHEMA_VERSION,
    AgentState,
    TraceEntry,
    state_fingerprint,
    terminal_result,
)


def _sample_state() -> AgentState:
    return AgentState(
        round=3,
        spent=4.5,
        last={"answer": 42},
        trace=[
            TraceEntry(decision="call", ref="search", cost=1.0),
            TraceEntry(decision="finish", cost=0.0),
        ],
        call_counts={"search": 2, "fetch": 1},
    )


# --------------------------------------------------------------------------- #
# Version envelope on to_json.
# --------------------------------------------------------------------------- #
def test_schema_version_constant_is_one() -> None:
    assert STATE_SCHEMA_VERSION == 1


def test_to_json_carries_schema_version() -> None:
    out = _sample_state().to_json()
    assert out["schemaVersion"] == STATE_SCHEMA_VERSION == 1


def test_to_json_preserves_other_keys() -> None:
    out = _sample_state().to_json()
    assert out["round"] == 3
    assert out["cost"] == 4.5
    assert out["last"] == {"answer": 42}
    assert out["callCounts"] == {"fetch": 1, "search": 2}
    assert [t["decision"] for t in out["trace"]] == ["call", "finish"]


def test_schema_version_does_not_leak_into_terminal_result() -> None:
    out = terminal_result("ok", _sample_state(), output="done")
    assert "schemaVersion" not in out
    assert out["callCounts"] == {"fetch": 1, "search": 2}


def test_schema_version_does_not_leak_into_trace_entry() -> None:
    entry = TraceEntry(decision="call", ref="search", cost=1.0)
    assert "schemaVersion" not in entry.to_json()


# --------------------------------------------------------------------------- #
# Round-trip + version tolerance on from_json.
# --------------------------------------------------------------------------- #
def test_round_trip_preserves_fields() -> None:
    state = _sample_state()
    restored = AgentState.from_json(state.to_json())
    assert restored.round == state.round
    assert restored.spent == state.spent
    assert restored.last == state.last
    assert restored.call_counts == state.call_counts
    assert [t.to_json() for t in restored.trace] == [t.to_json() for t in state.trace]


def test_from_json_tolerates_missing_schema_version() -> None:
    # Legacy state written before the envelope existed: no schemaVersion key.
    legacy = {
        "round": 1,
        "cost": 2.0,
        "last": "hi",
        "trace": [{"decision": "finish", "cost": 0.0}],
        "callCounts": {"x": 1},
    }
    assert "schemaVersion" not in legacy
    restored = AgentState.from_json(legacy)
    assert restored.round == 1
    assert restored.spent == 2.0
    assert restored.last == "hi"
    assert restored.call_counts == {"x": 1}


def test_from_json_accepts_current_schema_version() -> None:
    d = _sample_state().to_json()
    assert d["schemaVersion"] == 1
    restored = AgentState.from_json(d)
    assert restored.round == 3


def test_from_json_rejects_future_major_version() -> None:
    d = _sample_state().to_json()
    d["schemaVersion"] = 99
    with pytest.raises(ValueError):
        AgentState.from_json(d)


# --------------------------------------------------------------------------- #
# Fingerprint: stable, order-independent, field-sensitive.
# --------------------------------------------------------------------------- #
def test_fingerprint_is_hex_sha256() -> None:
    fp = state_fingerprint(_sample_state())
    assert isinstance(fp, str)
    assert len(fp) == 64
    int(fp, 16)  # raises if not hex


def test_fingerprint_matches_canonical_json_of_to_json() -> None:
    import hashlib

    state = _sample_state()
    canonical = json.dumps(state.to_json(), sort_keys=True, separators=(",", ":"))
    assert state_fingerprint(state) == hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_fingerprint_stable_across_equal_states() -> None:
    assert state_fingerprint(_sample_state()) == state_fingerprint(_sample_state())


def test_fingerprint_order_independent_for_call_counts() -> None:
    a = AgentState(round=1, call_counts={"a": 1, "b": 2})
    b = AgentState(round=1, call_counts={"b": 2, "a": 1})
    assert state_fingerprint(a) == state_fingerprint(b)


def test_fingerprint_changes_when_round_changes() -> None:
    a = _sample_state()
    b = _sample_state()
    b.round += 1
    assert state_fingerprint(a) != state_fingerprint(b)


def test_fingerprint_changes_when_last_changes() -> None:
    a = _sample_state()
    b = _sample_state()
    b.last = {"answer": 43}
    assert state_fingerprint(a) != state_fingerprint(b)


def test_fingerprint_changes_when_trace_changes() -> None:
    a = _sample_state()
    b = _sample_state()
    b.trace.append(TraceEntry(decision="call", ref="extra", cost=1.0))
    assert state_fingerprint(a) != state_fingerprint(b)


def test_fingerprint_changes_when_call_counts_change() -> None:
    a = _sample_state()
    b = _sample_state()
    b.call_counts["search"] += 1
    assert state_fingerprint(a) != state_fingerprint(b)


def test_fingerprint_rejects_non_json_state_loudly() -> None:
    state = _sample_state()
    state.last = b"raw bytes are not JSON"
    with pytest.raises(TypeError, match="JSON"):
        state_fingerprint(state)
