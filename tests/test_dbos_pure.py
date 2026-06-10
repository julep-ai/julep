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


def test_scan_rejects_app():
    flow = app("triage_controller")
    with pytest.raises(UnsupportedShapeError, match="app"):
        assert_dbos_executable(flow)


def test_policy_error_envelope_roundtrip():
    env = encode_policy_error(CapabilityDenied("tool 'x' exceeded maxCalls=2"))
    with pytest.raises(CapabilityDenied, match="maxCalls=2"):
        decode_policy_error(env)


def test_decode_passes_plain_values_through():
    assert decode_policy_error({"hits": 3}) == {"hits": 3}
    assert decode_policy_error(None) is None
    assert decode_policy_error([1, 2]) == [1, 2]
