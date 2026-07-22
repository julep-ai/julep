from __future__ import annotations

from julep.errors import (
    POLICY_ERRORS,
    ToolSurfaceDrift,
    tool_surface_drift_from_cause,
)


def test_tool_surface_drift_is_non_retryable_policy_error() -> None:
    assert ToolSurfaceDrift in POLICY_ERRORS


def test_drift_cause_helper_preserves_direct_typed_error() -> None:
    drift = ToolSurfaceDrift("srv", "search", "tool_not_found")

    assert tool_surface_drift_from_cause(drift) is drift


def test_drift_cause_helper_reconstructs_temporal_style_nested_type() -> None:
    class ApplicationFailure(Exception):
        type = "ToolSurfaceDrift"

    activity = RuntimeError("activity failed")
    activity.__cause__ = ApplicationFailure(
        "ToolSurfaceDrift: MCP tool surface drift for srv/search: input_schema_rejected"
    )

    drift = tool_surface_drift_from_cause(activity)

    assert drift is not None
    assert drift.to_json() == {
        "server": "srv",
        "tool": "search",
        "reason": "input_schema_rejected",
    }


def test_drift_cause_helper_ignores_unrelated_activity_failure() -> None:
    assert tool_surface_drift_from_cause(RuntimeError("network timeout")) is None
