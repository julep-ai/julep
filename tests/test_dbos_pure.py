"""DBOS-backend logic that needs no database: shape scan, error envelope,
retry-variant choice. Needs dbos importable (decorators at module import)."""
from __future__ import annotations

import asyncio

import pytest

from julep.execution import HAVE_DBOS

pytestmark = pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")

if HAVE_DBOS:
    from julep import call, seq, think
    from julep.derived import delay, race
    from julep.dsl import app
    from julep.errors import CapabilityDenied, UnsupportedShapeError
    from julep.execution.dbos_backend import (
        DbosEnv,
        assert_dbos_executable,
        callToolIdempotent,
        callToolNoRetry,
        decode_policy_error,
        encode_policy_error,
    )
    from julep.execution.harness import ExecutionPolicy
    from julep.projection import InMemoryProjection, ProjectionEmitter


def test_scan_accepts_pipeline_shapes():
    flow = seq(call("kb/search"), seq(think("triage"), delay(seconds=5)))
    assert_dbos_executable(flow)  # no raise


def test_scan_rejects_race():
    flow = race(call("kb/a"), call("kb/b"))
    with pytest.raises(UnsupportedShapeError, match="race"):
        assert_dbos_executable(flow)


def test_scan_accepts_app():
    flow = app("triage_controller")
    assert_dbos_executable(flow)  # no raise: app runs via the julep_agent chain


def test_run_call_step_names_are_durable_identities():
    """DBOS persists step names per function_id; recovery raises
    DBOSUnexpectedStepError on mismatch. These names are wire-frozen: changing
    either breaks replay of in-flight workflows. ``callToolNoRetry`` keeps its
    pre-retry-algebra persisted name ``callToolWrite`` on purpose."""
    assert callToolNoRetry.dbos_function_name == "callToolWrite"
    assert callToolIdempotent.dbos_function_name == "callToolIdempotent"


def test_policy_error_envelope_roundtrip():
    env = encode_policy_error(CapabilityDenied("tool 'x' exceeded maxCalls=2"))
    with pytest.raises(CapabilityDenied, match="maxCalls=2"):
        decode_policy_error(env)


def test_decode_passes_plain_values_through():
    assert decode_policy_error({"hits": 3}) == {"hits": 3}
    assert decode_policy_error(None) is None
    assert decode_policy_error([1, 2]) == [1, 2]


def test_dbos_env_preserves_native_parent_count_and_uses_wire_alias_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from julep.execution import dbos_backend

    submitted = []

    async def fake_run_agent_chain(payload, *, base_id):  # noqa: ANN001
        submitted.append((payload, base_id))
        return {
            "status": "done",
            "output": "ok",
            "callCounts": {"search": 1, "srv/search": 1},
        }

    monkeypatch.setattr(dbos_backend, "_run_agent_chain", fake_run_agent_chain)
    env = DbosEnv(
        manifest={},
        emitter=ProjectionEmitter(InMemoryProjection()),
        session_id="dbos-alias",
        manifest_json={},
        policy=ExecutionPolicy(),
        max_call_limits={"search": 10, "srv/search": 1},
        call_counts={"search": 1},
    )
    reply_schema = {"type": "object"}

    out = asyncio.run(
        env.run_agent(
            "controller",
            {},
            "cid",
            {
                "tools": ["search"],
                "toolAliases": {"search": "srv/search"},
                "toolContracts": {"search": {"maxCalls": 5}},
                "replySchema": reply_schema,
                "outputRetries": 3,
            },
        )
    )

    payload, base_id = submitted[0]
    assert base_id == "dbos-alias-agent-cid"
    assert payload["grantedContracts"] == {"search": {"maxCalls": 1}}
    assert payload["state"]["callCounts"] == {"search": 1}
    assert payload["config"]["replySchema"] == reply_schema
    assert payload["config"]["outputRetries"] == 3
    assert out["output"] == "ok"
    assert env.call_counts_snapshot() == {"search": 1, "srv/search": 1}
