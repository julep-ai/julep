"""Determinism and known-value checks for the pinned §13 golden corpus."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from .fixtures import FIXTURE_BUILDERS
from .snapshot import snapshot_fixture

GOLDEN_HASHES_PATH = Path(__file__).with_name("golden_hashes.json")
HASH_COMPONENTS = (
    "flowJson",
    "manifestJson",
    "validateDiagnostics",
    "shapes",
    "snapshot",
)


def _load_golden_hashes() -> dict[str, Any]:
    with GOLDEN_HASHES_PATH.open(encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        raise TypeError(f"{GOLDEN_HASHES_PATH} must contain a JSON object")
    return loaded


GOLDEN_HASHES = _load_golden_hashes()


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


@pytest.mark.parametrize("name", sorted(FIXTURE_BUILDERS))
def test_phase4_known_value_hashes(name: str) -> None:
    assert set(GOLDEN_HASHES) == set(FIXTURE_BUILDERS)

    fixture = FIXTURE_BUILDERS[name]()
    if fixture.skip_reason:
        pytest.skip(fixture.skip_reason)

    snapshot = snapshot_fixture(fixture)
    expected = GOLDEN_HASHES[name]
    expected_hashes = {component: expected[component] for component in HASH_COMPONENTS}

    assert snapshot.hashes == expected_hashes
    assert snapshot.payload["shapes"] == expected["shapeValues"]
    assert len(snapshot.payload["toolHashes"]) == expected["toolHashesCount"]
