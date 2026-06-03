"""Determinism checks for the unpinned §13 golden corpus."""

from __future__ import annotations

import pytest

from .fixtures import FIXTURE_BUILDERS
from .snapshot import snapshot_fixture


@pytest.mark.parametrize("name", sorted(FIXTURE_BUILDERS))
def test_golden_fixture_is_deterministic(name: str) -> None:
    first_fixture = FIXTURE_BUILDERS[name]()
    if first_fixture.skip_reason:
        pytest.skip(first_fixture.skip_reason)

    second_fixture = FIXTURE_BUILDERS[name]()
    first = snapshot_fixture(first_fixture)
    second = snapshot_fixture(second_fixture)

    assert first.canonical_json == second.canonical_json
    assert first.hashes == second.hashes


# PHASE 4: pin known-value hashes here once Phase 2a hash-chain changes settle.
@pytest.mark.skip(reason="PHASE 4: known-value golden hashes are intentionally unpinned")
@pytest.mark.parametrize("name", sorted(FIXTURE_BUILDERS))
def test_phase4_known_value_hashes(name: str) -> None:
    expected_hashes: dict[str, str] = {}
    snapshot = snapshot_fixture(FIXTURE_BUILDERS[name]())
    assert snapshot.hashes == expected_hashes
