"""Tests for the committed deploy ledger (.julep/deploys/<env>.json).

The ledger is self-describing: each DeployRecord embeds the frozen flow_json +
manifest_json so `julep run --env` can replay the deployed artifact with no
re-freeze. JSON written to disk must be stable/sorted so the committed file
diffs cleanly.
"""

from __future__ import annotations

import json
from pathlib import Path

from julep.cli.ledger import (
    DeployRecord,
    deployed_hashes,
    ledger_path,
    read_ledger,
    upsert_records,
)


def _rec(agent: str, h: str, *, deployed_at: str = "2026-06-23T00:00:00+00:00") -> DeployRecord:
    return DeployRecord(
        agent=agent,
        artifact_hash=h,
        flow_json={"name": agent, "nodes": [agent]},
        manifest_json={"agent": agent, "caps": []},
        bundle_ref=[{"path": f"{agent}.py", "hash": h}],
        deployed_at=deployed_at,
    )


def test_ledger_path(tmp_path: Path) -> None:
    p = ledger_path(tmp_path, "local")
    assert p == tmp_path / ".julep" / "deploys" / "local.json"
    p2 = ledger_path(str(tmp_path), "staging")
    assert p2 == tmp_path / ".julep" / "deploys" / "staging.json"


def test_read_missing_ledger_is_empty(tmp_path: Path) -> None:
    assert read_ledger(tmp_path, "local") == {}
    # missing ledger must not create any files
    assert not (tmp_path / ".julep").exists()


def test_upsert_two_records_then_read_back(tmp_path: Path) -> None:
    recs = [_rec("triage", "sha256:aaa"), _rec("escalate", "sha256:bbb")]
    upsert_records(tmp_path, "local", recs)

    out = read_ledger(tmp_path, "local")
    assert set(out) == {"triage", "escalate"}
    assert isinstance(out["triage"], DeployRecord)
    assert out["triage"].artifact_hash == "sha256:aaa"
    assert out["triage"].flow_json == {"name": "triage", "nodes": ["triage"]}
    assert out["triage"].manifest_json == {"agent": "triage", "caps": []}
    assert out["triage"].bundle_ref == [{"path": "triage.py", "hash": "sha256:aaa"}]
    assert out["escalate"].artifact_hash == "sha256:bbb"


def test_upsert_merges_updates_one_keeps_other(tmp_path: Path) -> None:
    upsert_records(tmp_path, "local", [_rec("triage", "sha256:aaa"), _rec("escalate", "sha256:bbb")])
    # re-deploy only triage with a new hash + timestamp
    upsert_records(
        tmp_path,
        "local",
        [_rec("triage", "sha256:ccc", deployed_at="2026-06-23T12:00:00+00:00")],
    )

    out = read_ledger(tmp_path, "local")
    assert set(out) == {"triage", "escalate"}
    assert out["triage"].artifact_hash == "sha256:ccc"
    assert out["triage"].deployed_at == "2026-06-23T12:00:00+00:00"
    # escalate untouched
    assert out["escalate"].artifact_hash == "sha256:bbb"
    assert out["escalate"].deployed_at == "2026-06-23T00:00:00+00:00"


def test_bundle_ref_may_be_none(tmp_path: Path) -> None:
    rec = DeployRecord(
        agent="triage",
        artifact_hash="sha256:aaa",
        flow_json={"name": "triage"},
        manifest_json={"agent": "triage"},
        bundle_ref=None,
        deployed_at="2026-06-23T00:00:00+00:00",
    )
    upsert_records(tmp_path, "local", [rec])
    out = read_ledger(tmp_path, "local")
    assert out["triage"].bundle_ref is None


def test_deployed_hashes(tmp_path: Path) -> None:
    assert deployed_hashes(tmp_path, "local") == {}
    upsert_records(tmp_path, "local", [_rec("triage", "sha256:aaa"), _rec("escalate", "sha256:bbb")])
    assert deployed_hashes(tmp_path, "local") == {
        "triage": "sha256:aaa",
        "escalate": "sha256:bbb",
    }


def test_envs_are_isolated_files(tmp_path: Path) -> None:
    upsert_records(tmp_path, "local", [_rec("triage", "sha256:local")])
    upsert_records(tmp_path, "staging", [_rec("triage", "sha256:staging")])
    assert deployed_hashes(tmp_path, "local") == {"triage": "sha256:local"}
    assert deployed_hashes(tmp_path, "staging") == {"triage": "sha256:staging"}
    assert (tmp_path / ".julep" / "deploys" / "local.json").is_file()
    assert (tmp_path / ".julep" / "deploys" / "staging.json").is_file()


def test_written_json_is_stable_and_sorted(tmp_path: Path) -> None:
    # insert in non-sorted key order to prove the writer sorts.
    upsert_records(
        tmp_path,
        "local",
        [_rec("zeta", "sha256:z"), _rec("alpha", "sha256:a"), _rec("mid", "sha256:m")],
    )
    raw = (tmp_path / ".julep" / "deploys" / "local.json").read_text(encoding="utf-8")

    data = json.loads(raw)
    # top-level agent keys sorted
    assert list(data.keys()) == ["alpha", "mid", "zeta"]

    # pretty-printed (indented) and ends with a trailing newline for clean diffs
    assert "\n" in raw
    assert raw.endswith("\n")

    # deterministic: re-serializing the parsed data with sort_keys reproduces the
    # file body byte-for-byte (i.e. the writer used sort_keys + indent=2).
    expected = json.dumps(data, indent=2, sort_keys=True) + "\n"
    assert raw == expected


def test_write_is_idempotent_byte_for_byte(tmp_path: Path) -> None:
    recs = [_rec("triage", "sha256:aaa"), _rec("escalate", "sha256:bbb")]
    upsert_records(tmp_path, "local", recs)
    first = (tmp_path / ".julep" / "deploys" / "local.json").read_text(encoding="utf-8")
    # writing the same records again must not change the file bytes.
    upsert_records(tmp_path, "local", recs)
    second = (tmp_path / ".julep" / "deploys" / "local.json").read_text(encoding="utf-8")
    assert first == second
