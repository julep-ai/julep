from __future__ import annotations

import pytest

from julep import _env


def test_canonical_environment_names_match_rename_table() -> None:
    assert _env.CANONICAL_ENV_VAR_NAMES == frozenset(
        _env.LEGACY_ENV_VAR_RENAMES.values()
    )
    assert len(_env.CANONICAL_ENV_VAR_NAMES) == 15


def test_environment_reads_do_not_fall_back_to_legacy_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy_name = next(
        old
        for old, new in _env.LEGACY_ENV_VAR_RENAMES.items()
        if new == _env.JULEP_BUNDLE_SIGNING_KEY
    )
    monkeypatch.setenv(legacy_name, "legacy-value")
    monkeypatch.delenv(_env.JULEP_BUNDLE_SIGNING_KEY, raising=False)

    assert _env.get(_env.JULEP_BUNDLE_SIGNING_KEY) is None
