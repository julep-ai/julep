from __future__ import annotations

import inspect

import pytest

from julep import CapabilityManifest, call, deploy, mcp
from julep.diagnostics import explain
from julep.dsl import set_source_capture
from julep.freeze import freeze
from julep.ir import SourceSpan, canonical_json
from conftest import read_snapshot


@pytest.fixture(autouse=True)
def _reset_source_capture() -> None:
    set_source_capture(False)
    try:
        yield
    finally:
        set_source_capture(False)


def _capabilities() -> CapabilityManifest:
    return CapabilityManifest.from_dict(
        {
            "tools": [{"name": "srv/allowed", "effect": "read", "idempotency": "native"}],
            "mcp_servers": {"srv": None},
        }
    )


def _matching_diagnostic(flow):
    deployment = deploy(
        flow,
        read_snapshot("allowed", "denied"),
        capabilities=_capabilities(),
        mode="dev",
    )
    return next(d for d in deployment.diagnostics if d.code == "CAP_TOOL_DENIED")


def test_capture_on_points_diagnostic_at_user_line() -> None:
    set_source_capture(True)
    expected_line = inspect.currentframe().f_lineno + 1
    flow = call(mcp("srv", "denied"))

    diagnostic = _matching_diagnostic(flow)

    assert isinstance(diagnostic.source, SourceSpan)
    assert diagnostic.source.file.endswith("test_source_map.py")
    assert diagnostic.source.line == expected_line
    rendered = explain([diagnostic])
    assert "-->" in rendered
    assert "test_source_map.py:" in rendered


def test_capture_off_default_has_no_source_pointer() -> None:
    flow = call(mcp("srv", "denied"))

    diagnostic = _matching_diagnostic(flow)

    assert diagnostic.source is None
    assert "-->" not in explain([diagnostic])


def test_source_is_out_of_to_json_and_artifact_hash() -> None:
    set_source_capture(True)
    captured_flow = call(mcp("srv", "allowed"))
    captured = deploy(captured_flow, read_snapshot("allowed"))

    set_source_capture(False)
    uncaptured = deploy(call(mcp("srv", "allowed")), read_snapshot("allowed"))

    assert '"source"' not in canonical_json(captured_flow.to_json())
    assert '"source"' not in canonical_json(captured.artifact_components)
    assert captured.artifact_hash == uncaptured.artifact_hash


def test_freeze_source_map_is_keyed_by_frozen_ids() -> None:
    set_source_capture(True)
    flow = call(mcp("srv", "allowed"))

    result = freeze(flow, read_snapshot("allowed"))

    assert result.source_map
    assert all(key.startswith("$") for key in result.source_map)
