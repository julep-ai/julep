"""DBOS-backend logic that needs no database: shape scan, error envelope,
retry-variant choice. Needs dbos importable (decorators at module import)."""
from __future__ import annotations

import pytest

from composable_agents.execution import HAVE_DBOS

pytestmark = pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")

if HAVE_DBOS:
    from composable_agents import call, seq, think
    from composable_agents.derived import delay, race
    from composable_agents.dsl import app
    from composable_agents.errors import CapabilityDenied, UnsupportedShapeError
    from composable_agents.execution.dbos_backend import (
        assert_dbos_executable,
        callHandIdempotent,
        callHandNoRetry,
        decode_policy_error,
        encode_policy_error,
    )


def test_scan_accepts_pipeline_shapes():
    flow = seq(call("kb/search"), seq(think("triage"), delay(seconds=5)))
    assert_dbos_executable(flow)  # no raise


def test_scan_rejects_race():
    flow = race(call("kb/a"), call("kb/b"))
    with pytest.raises(UnsupportedShapeError, match="race"):
        assert_dbos_executable(flow)


def test_scan_accepts_app():
    flow = app("triage_controller")
    assert_dbos_executable(flow)  # no raise: app runs via the ca_agent chain


def test_call_hand_step_names_are_durable_identities():
    """DBOS persists step names per function_id; recovery raises
    DBOSUnexpectedStepError on mismatch. These names are wire-frozen: changing
    either breaks replay of in-flight workflows. ``callHandNoRetry`` keeps its
    pre-retry-algebra persisted name ``callHandWrite`` on purpose."""
    assert callHandNoRetry.dbos_function_name == "callHandWrite"
    assert callHandIdempotent.dbos_function_name == "callHandIdempotent"


def test_policy_error_envelope_roundtrip():
    env = encode_policy_error(CapabilityDenied("tool 'x' exceeded maxCalls=2"))
    with pytest.raises(CapabilityDenied, match="maxCalls=2"):
        decode_policy_error(env)


def test_decode_passes_plain_values_through():
    assert decode_policy_error({"hits": 3}) == {"hits": 3}
    assert decode_policy_error(None) is None
    assert decode_policy_error([1, 2]) == [1, 2]
