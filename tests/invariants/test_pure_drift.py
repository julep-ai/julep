"""Pure source drift checks."""

from __future__ import annotations

from julep.purity import diff_pure_hashes


def test_diff_pure_hashes_reports_changed_and_missing() -> None:
    drift = diff_pure_hashes(
        {
            "route.changed": "pure:before",
            "route.missing": "pure:pinned",
            "route.same": "pure:same",
        },
        {
            "route.changed": "pure:after",
            "route.same": "pure:same",
        },
    )

    assert drift == [
        {
            "name": "route.changed",
            "pinned": "pure:before",
            "actual": "pure:after",
        },
        {
            "name": "route.missing",
            "pinned": "pure:pinned",
            "actual": None,
        },
    ]


def test_diff_pure_hashes_reports_no_drift_when_hashes_match() -> None:
    assert diff_pure_hashes(
        {"route.same": "pure:same"},
        {"route.same": "pure:same", "route.extra": "pure:extra"},
    ) == []
