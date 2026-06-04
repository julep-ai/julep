from __future__ import annotations

import asyncio

import pytest

from composable_agents import (
    CapabilityManifest,
    EnforcementMode,
    blocking,
    call,
    deploy,
    mcp,
)
from composable_agents.errors import ValidationError
from conftest import read_snapshot


def _bad_flow():
    return call(mcp("srv", "b"))


def _clean_flow():
    return call(mcp("srv", "a"))


def _capabilities() -> CapabilityManifest:
    return CapabilityManifest.from_dict(
        {
            "tools": [{"name": "srv/a", "effect": "read", "idempotency": "native"}],
            "mcp_servers": {"srv": None},
        }
    )


def test_dev_mode_does_not_raise_and_exposes_prod_gap() -> None:
    dep = deploy(_bad_flow(), read_snapshot("a", "b"), capabilities=_capabilities(), mode="dev")

    assert dep.mode is EnforcementMode.DEV
    assert dep.prod_gap
    assert dep.prod_gap == blocking(dep.diagnostics)
    assert "ungranted tool" in dep.prod_gap_summary()


def test_strict_default_still_raises() -> None:
    with pytest.raises(ValidationError):
        deploy(_bad_flow(), read_snapshot("a", "b"), capabilities=_capabilities())


def test_strict_false_is_unchanged_and_collects_gap() -> None:
    dep = deploy(
        _bad_flow(),
        read_snapshot("a", "b"),
        capabilities=_capabilities(),
        strict=False,
    )

    assert dep.mode is EnforcementMode.STRICT
    assert dep.prod_gap


def test_clean_dev_mode_has_no_prod_gap() -> None:
    dep = deploy(_clean_flow(), read_snapshot("a"), capabilities=_capabilities(), mode="dev")

    assert dep.prod_gap == []
    assert dep.prod_gap_summary() == "no prod gap"


def test_dev_mode_deployment_run_rejects_before_temporal_import() -> None:
    dep = deploy(_clean_flow(), read_snapshot("a"), capabilities=_capabilities(), mode="dev")

    with pytest.raises(ValueError, match="dev-mode deployment.*prod_gap"):
        asyncio.run(dep.run(object(), session_id="x"))


def test_prod_alias_behaves_as_strict() -> None:
    with pytest.raises(ValidationError):
        deploy(_bad_flow(), read_snapshot("a", "b"), capabilities=_capabilities(), mode="prod")


def test_mode_is_not_part_of_artifact_hash() -> None:
    strict_dep = deploy(
        _clean_flow(),
        read_snapshot("a"),
        capabilities=_capabilities(),
        mode="strict",
    )
    dev_dep = deploy(
        _clean_flow(),
        read_snapshot("a"),
        capabilities=_capabilities(),
        mode="dev",
    )

    assert "mode" not in strict_dep.artifact_components
    assert "mode" not in dev_dep.artifact_components
    assert strict_dep.artifact_components == dev_dep.artifact_components
    assert strict_dep.artifact_hash == dev_dep.artifact_hash


def test_refresh_carries_dev_mode() -> None:
    snap = read_snapshot("a", "b")
    dep = deploy(
        _bad_flow(),
        snap,
        capabilities=_capabilities(),
        mode=EnforcementMode.DEV,
        freeze_timing="per_run",
        snapshot_source=lambda: snap,
    )

    refreshed = dep.refresh()

    assert refreshed.mode is EnforcementMode.DEV
    assert refreshed.prod_gap
