"""Committed deploy ledger for ca CLI deployments."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

__all__ = [
    "DeployRecord",
    "deployed_hashes",
    "ledger_path",
    "read_ledger",
    "upsert_records",
]


@dataclass(frozen=True)
class DeployRecord:
    agent: str
    artifact_hash: str
    flow_json: dict[str, Any]
    manifest_json: dict[str, Any]
    bundle_ref: list[dict[str, Any]] | None
    deployed_at: str

    def to_json(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "artifact_hash": self.artifact_hash,
            "flow_json": self.flow_json,
            "manifest_json": self.manifest_json,
            "bundle_ref": self.bundle_ref,
            "deployed_at": self.deployed_at,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> DeployRecord:
        if not isinstance(data, dict):
            raise ValueError("DeployRecord data must be a JSON object")

        return cls(
            agent=_str_field(data, "agent"),
            artifact_hash=_str_field(data, "artifact_hash"),
            flow_json=_dict_field(data, "flow_json"),
            manifest_json=_dict_field(data, "manifest_json"),
            bundle_ref=_bundle_ref_field(data, "bundle_ref"),
            deployed_at=_str_field(data, "deployed_at"),
        )


def ledger_path(root: str | Path, env: str) -> Path:
    return Path(root) / ".ca" / "deploys" / f"{env}.json"


def read_ledger(root: str | Path, env: str) -> dict[str, DeployRecord]:
    path = ledger_path(root, env)
    if not path.exists():
        return {}

    data: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Deploy ledger is not a JSON object: {path}")

    records: dict[str, DeployRecord] = {}
    for agent, record_data in data.items():
        if not isinstance(agent, str):
            raise ValueError(f"Deploy ledger key is not a string: {path}")
        if not isinstance(record_data, dict):
            raise ValueError(f"Deploy ledger entry is not a JSON object: {agent}")
        records[agent] = DeployRecord.from_json(_string_keyed_dict(record_data, f"record {agent}"))

    return records


def upsert_records(root: str | Path, env: str, records: Iterable[DeployRecord]) -> None:
    path = ledger_path(root, env)
    ledger = read_ledger(root, env)
    for record in records:
        ledger[record.agent] = record

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {agent: record.to_json() for agent, record in ledger.items()}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def deployed_hashes(root: str | Path, env: str) -> dict[str, str]:
    return {agent: record.artifact_hash for agent, record in read_ledger(root, env).items()}


def _field(data: dict[str, Any], name: str) -> Any:
    if name not in data:
        raise ValueError(f"DeployRecord.{name} is required")
    return data[name]


def _str_field(data: dict[str, Any], name: str) -> str:
    value = _field(data, name)
    if not isinstance(value, str):
        raise ValueError(f"DeployRecord.{name} must be a string")
    return value


def _dict_field(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = _field(data, name)
    if not isinstance(value, dict):
        raise ValueError(f"DeployRecord.{name} must be a JSON object")
    return _string_keyed_dict(value, f"DeployRecord.{name}")


def _bundle_ref_field(data: dict[str, Any], name: str) -> list[dict[str, Any]] | None:
    value = _field(data, name)
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError(f"DeployRecord.{name} must be a list or null")

    bundle_ref: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"DeployRecord.{name}[{index}] must be a JSON object")
        bundle_ref.append(_string_keyed_dict(item, f"DeployRecord.{name}[{index}]"))

    return bundle_ref


def _string_keyed_dict(value: dict[Any, Any], name: str) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError(f"{name} key must be a string")
        output[key] = item
    return output
