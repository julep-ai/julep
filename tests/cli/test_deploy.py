"""Tests for the subprocess freeze+publish pipeline + deploy_agents ledger writer.

Fully verifiable against a LOCAL artifact-store: the `sample_module` fixture provides a
`triage` @flow whose snapshot is built from its referenced tools inside the
resolver subprocess (the only place the live agent + tools exist). `deploy_agents`
freezes+publishes each selected agent and upserts the committed deploy ledger.

The S3 path (artifacts = "s3://...") needs boto3 (the `store` extra) and is NOT
exercised here; only the local path is asserted. The `s3://` branch is gated so a
missing boto3 raises a clear "install the store extra" message.
"""

from __future__ import annotations

from pathlib import Path

from julep.cli.config import load_config
from julep.cli.deploy import deploy_agents, freeze_agent
from julep.cli.ledger import read_ledger

_NOW = "2026-06-23T00:00:00Z"


def _artifact_files(root: Path) -> list[Path]:
    artifacts_root = root / ".julep" / "artifacts"
    if not artifacts_root.exists():
        return []
    return [p for p in artifacts_root.rglob("*") if p.is_file()]


def test_freeze_agent_returns_hash_and_flow(sample_module: Path) -> None:
    cfg = load_config(sample_module)
    artifact = freeze_agent(cfg, "triage", "local")
    assert artifact.error is None, artifact.error
    assert artifact.artifact_hash.startswith("sha256:")
    assert isinstance(artifact.flow_json, dict)
    assert artifact.flow_json  # non-empty serialized IR
    assert isinstance(artifact.manifest_json, dict)
    # bundle_ref is None for a flow with no pure runtime refs (the sample case).
    assert artifact.bundle_ref is None or isinstance(artifact.bundle_ref, list)
    # Publishing wrote the bundle blobs under the local artifact-store.
    assert _artifact_files(sample_module), "expected bundle objects under .julep/artifacts/"


def test_deploy_agents_writes_ledger_and_bundle(sample_module: Path) -> None:
    cfg = load_config(sample_module)
    records = deploy_agents(cfg, ["triage"], "local", now_iso=_NOW)

    assert len(records) == 1
    record = records[0]
    assert record.agent == "triage"
    assert record.artifact_hash.startswith("sha256:")
    assert record.deployed_at == _NOW
    assert record.flow_json  # frozen IR is embedded in the ledger record

    # Ledger file written at .julep/deploys/local.json and reads back identically.
    ledger_file = sample_module / ".julep" / "deploys" / "local.json"
    assert ledger_file.is_file()
    ledger = read_ledger(sample_module, "local")
    assert set(ledger) == {"triage"}
    assert ledger["triage"].artifact_hash == record.artifact_hash

    # The published bundle landed under .julep/artifacts/.
    assert _artifact_files(sample_module), "expected bundle objects under .julep/artifacts/"


def test_freeze_agent_unknown_surfaces_error_no_ledger(sample_module: Path) -> None:
    cfg = load_config(sample_module)
    artifact = freeze_agent(cfg, "does_not_exist", "local")
    assert artifact.error is not None
    assert "does_not_exist" in artifact.error
    # No ledger written for a failed freeze.
    assert not (sample_module / ".julep" / "deploys" / "local.json").exists()


def test_freeze_check_is_read_only_and_hash_matches_publish(sample_module: Path) -> None:
    """publish=False computes the same artifact_hash without mutating the artifact-store."""
    cfg = load_config(sample_module)

    published = freeze_agent(cfg, "triage", "local", publish=True)
    assert published.error is None, published.error
    assert _artifact_files(sample_module), "publish should write artifact-store objects"

    # Wipe all on-disk state, then run the read-only check path.
    import shutil

    shutil.rmtree(sample_module / ".julep", ignore_errors=True)
    checked = freeze_agent(cfg, "triage", "local", publish=False)

    assert checked.error is None, checked.error
    # Same program identity, no publish needed.
    assert checked.artifact_hash == published.artifact_hash
    # The read-only path must not create the artifact-store directory at all.
    assert not (sample_module / ".julep" / "artifacts").exists()


def test_freeze_agent_captures_pinned_pures(sample_module: Path) -> None:
    cfg = load_config(sample_module)
    artifact = freeze_agent(cfg, "triage", "local")
    assert artifact.error is None, artifact.error
    # The sample flow folds env pures (std.*); their source hashes are pinned.
    assert artifact.pinned_pures
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in artifact.pinned_pures.items())


def test_deploy_persists_pinned_pures_in_ledger(sample_module: Path) -> None:
    cfg = load_config(sample_module)
    records = deploy_agents(cfg, ["triage"], "local", now_iso=_NOW)
    assert records[0].pinned_pures
    # Round-trips through the committed ledger.
    ledger = read_ledger(sample_module, "local")
    assert ledger["triage"].pinned_pures == records[0].pinned_pures


def test_freeze_agent_unknown_env_raises_value_error(sample_module: Path) -> None:
    cfg = load_config(sample_module)
    import pytest

    with pytest.raises(ValueError, match="unknown env"):
        freeze_agent(cfg, "triage", "staging")
