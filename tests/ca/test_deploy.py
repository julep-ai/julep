"""Tests for the subprocess freeze+publish pipeline + deploy_agents ledger writer.

Fully verifiable against a LOCAL CAS: the `sample_module` fixture provides a
`triage` @flow whose snapshot is built from its referenced tools inside the
resolver subprocess (the only place the live agent + tools exist). `deploy_agents`
freezes+publishes each selected agent and upserts the committed deploy ledger.

The S3 path (cas = "s3://...") needs boto3 (the `store` extra) and is NOT
exercised here; only the local path is asserted. The `s3://` branch is gated so a
missing boto3 raises a clear "install the store extra" message.
"""

from __future__ import annotations

from pathlib import Path

from composable_agents.ca.config import load_config
from composable_agents.ca.deploy import deploy_agents, freeze_agent
from composable_agents.ca.ledger import read_ledger

_NOW = "2026-06-23T00:00:00Z"


def _cas_files(root: Path) -> list[Path]:
    cas_root = root / ".ca" / "cas"
    if not cas_root.exists():
        return []
    return [p for p in cas_root.rglob("*") if p.is_file()]


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
    # Publishing wrote the bundle blobs under the local CAS.
    assert _cas_files(sample_module), "expected bundle objects under .ca/cas/"


def test_deploy_agents_writes_ledger_and_bundle(sample_module: Path) -> None:
    cfg = load_config(sample_module)
    records = deploy_agents(cfg, ["triage"], "local", now_iso=_NOW)

    assert len(records) == 1
    record = records[0]
    assert record.agent == "triage"
    assert record.artifact_hash.startswith("sha256:")
    assert record.deployed_at == _NOW
    assert record.flow_json  # frozen IR is embedded in the ledger record

    # Ledger file written at .ca/deploys/local.json and reads back identically.
    ledger_file = sample_module / ".ca" / "deploys" / "local.json"
    assert ledger_file.is_file()
    ledger = read_ledger(sample_module, "local")
    assert set(ledger) == {"triage"}
    assert ledger["triage"].artifact_hash == record.artifact_hash

    # The published bundle landed under .ca/cas/.
    assert _cas_files(sample_module), "expected bundle objects under .ca/cas/"


def test_freeze_agent_unknown_surfaces_error_no_ledger(sample_module: Path) -> None:
    cfg = load_config(sample_module)
    artifact = freeze_agent(cfg, "does_not_exist", "local")
    assert artifact.error is not None
    assert "does_not_exist" in artifact.error
    # No ledger written for a failed freeze.
    assert not (sample_module / ".ca" / "deploys" / "local.json").exists()
