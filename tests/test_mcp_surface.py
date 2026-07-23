from __future__ import annotations

import pytest

from julep import (
    McpSurfaceMismatchError,
    assert_mcp_surface,
    call,
    canonical_surface_digest,
    compare_mcp_surface,
    freeze,
    mcp,
    snapshot_from_listings,
)


VERSION = '{"protocol":"2025-03-26","server":"2.4.0"}'


def _snapshot(*, schema_type: str = "object", annotations: dict | None = None):
    return snapshot_from_listings(
        {
            "srv": {
                "search": {
                    "inputSchema": {"type": schema_type},
                    "annotations": annotations or {"readOnlyHint": True},
                },
                "unreferenced": {"inputSchema": {}},
            }
        },
        versions={"srv": VERSION},
    )


def test_pin_uses_normalized_definition_hash_and_ignores_extra_tools() -> None:
    frozen = freeze(call(mcp("srv", "search")), _snapshot())
    fresh = _snapshot(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": True,
            "openWorldHint": True,
            "idempotentHint": False,
        }
    )

    assert compare_mcp_surface(frozen.manifest, fresh, policy="pin") == ()
    assert canonical_surface_digest(frozen.manifest).startswith("sha256:")


@pytest.mark.parametrize(
    "fresh",
    [
        _snapshot(schema_type="array"),
        _snapshot(annotations={"readOnlyHint": False}),
    ],
)
def test_pin_reports_machine_readable_hash_and_diff(fresh) -> None:
    frozen = freeze(call(mcp("srv", "search")), _snapshot())

    (mismatch,) = compare_mcp_surface(frozen.manifest, fresh, policy="pin")

    assert mismatch.reason == "definition_hash"
    assert mismatch.frozen_definition_hash.startswith("sha256:")
    assert mismatch.fresh_definition_hash is not None
    assert "--- frozen" in (mismatch.diff or "")
    with pytest.raises(McpSurfaceMismatchError) as raised:
        assert_mcp_surface(frozen.manifest, fresh, policy="pin")
    assert raised.value.details == [mismatch.to_json()]


def test_names_and_off_are_explicit_escape_hatches() -> None:
    frozen = freeze(call(mcp("srv", "search")), _snapshot())
    changed = _snapshot(schema_type="array")
    missing = snapshot_from_listings({}, versions={})

    assert compare_mcp_surface(frozen.manifest, changed, policy="names") == ()
    assert compare_mcp_surface(frozen.manifest, missing, policy="off") == ()
    (mismatch,) = compare_mcp_surface(frozen.manifest, missing, policy="names")
    assert mismatch.reason == "missing_server"


def test_surface_policy_rejects_unknown_values() -> None:
    frozen = freeze(call(mcp("srv", "search")), _snapshot())
    with pytest.raises(ValueError, match="pin.*names.*off"):
        compare_mcp_surface(frozen.manifest, _snapshot(), policy="compatible")
