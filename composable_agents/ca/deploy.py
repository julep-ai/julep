from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from composable_agents.ca._resolve_child import _BEGIN, _END
from composable_agents.ca.config import CaConfig
from composable_agents.ca.ledger import DeployRecord, upsert_records


@dataclass(frozen=True)
class FrozenArtifact:
    name: str
    artifact_hash: str = ""
    flow_json: dict[str, Any] = field(default_factory=dict)
    manifest_json: dict[str, Any] = field(default_factory=dict)
    bundle_ref: list[dict[str, Any]] | None = None
    pinned_pures: dict[str, str] = field(default_factory=dict)
    error: str | None = None


def _extract_payload(stdout: str) -> dict[str, Any]:
    start = stdout.rfind(_BEGIN)
    end = stdout.rfind(_END)
    if start == -1 or end == -1 or end < start:
        raise ValueError("resolver produced no payload")
    body = stdout[start + len(_BEGIN) : end].strip()
    data: dict[str, Any] = json.loads(body)
    return data


def _string_keyed_dict(value: dict[Any, Any], name: str) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError(f"{name} key must be a string")
        output[key] = item
    return output


def _dict_field(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name)
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return _string_keyed_dict(value, name)


def _bundle_ref_field(data: dict[str, Any]) -> list[dict[str, Any]] | None:
    value = data.get("bundle_ref")
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError("bundle_ref must be a list or null")

    bundle_ref: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"bundle_ref[{index}] must be a JSON object")
        bundle_ref.append(_string_keyed_dict(item, f"bundle_ref[{index}]"))
    return bundle_ref


def _pinned_pures_field(data: dict[str, Any]) -> dict[str, str]:
    value = data.get("pinned_pures")
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("pinned_pures must be a JSON object or null")
    pinned: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise ValueError("pinned_pures must map string keys to string hashes")
        pinned[key] = item
    return pinned


def _artifact_from_payload(name: str, data: dict[str, Any]) -> FrozenArtifact:
    artifact_hash = data.get("artifact_hash")
    if not isinstance(artifact_hash, str):
        raise ValueError("artifact_hash must be a string")
    return FrozenArtifact(
        name=name,
        artifact_hash=artifact_hash,
        flow_json=_dict_field(data, "flow_json"),
        manifest_json=_dict_field(data, "manifest_json"),
        bundle_ref=_bundle_ref_field(data),
        pinned_pures=_pinned_pures_field(data),
        error=None,
    )


def freeze_agent(cfg: CaConfig, name: str, env: str, *, publish: bool = True) -> FrozenArtifact:
    try:
        env_cfg = cfg.envs[env]
    except KeyError:
        raise ValueError(f"unknown env {env!r}") from None
    cas = env_cfg.cas or str(cfg.root / ".ca" / "cas")
    arg = json.dumps(
        {
            "action": "freeze" if publish else "freeze_check",
            "root": str(cfg.root),
            "src": cfg.src,
            "name": name,
            "cas": cas,
        }
    )
    timeout = 120.0
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "composable_agents.ca._resolve_child", arg],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cfg.root),
        )
    except subprocess.TimeoutExpired:
        return FrozenArtifact(name=name, error=f"freeze timed out after {timeout}s")

    if proc.returncode != 0:
        return FrozenArtifact(name=name, error=proc.stderr.strip() or "freeze failed")

    try:
        data = _extract_payload(proc.stdout)
    except (ValueError, json.JSONDecodeError) as exc:
        detail = proc.stderr.strip()
        return FrozenArtifact(name=name, error=f"{exc}{f': {detail}' if detail else ''}")

    if "error" in data:
        return FrozenArtifact(name=name, error=str(data["error"]))

    try:
        return _artifact_from_payload(name, data)
    except ValueError as exc:
        return FrozenArtifact(name=name, error=f"invalid freeze payload: {exc}")


def deploy_agents(
    cfg: CaConfig,
    names: Sequence[str],
    env: str,
    *,
    now_iso: str,
) -> list[DeployRecord]:
    records: list[DeployRecord] = []
    for name in names:
        artifact = freeze_agent(cfg, name, env)
        if artifact.error is not None:
            raise RuntimeError(f"failed to deploy agent {name!r}: {artifact.error}")
        records.append(
            DeployRecord(
                agent=name,
                artifact_hash=artifact.artifact_hash,
                flow_json=artifact.flow_json,
                manifest_json=artifact.manifest_json,
                bundle_ref=artifact.bundle_ref,
                pinned_pures=artifact.pinned_pures,
                deployed_at=now_iso,
            )
        )

    upsert_records(cfg.root, env, records)
    return records
