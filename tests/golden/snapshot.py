"""Canonical snapshot helpers for §13 golden-corpus fixtures."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from composable_agents import CapabilityManifest, ToolGrant, manifest_to_json, validate
from composable_agents.ir import Node
from composable_agents.shapes import closed_shape, surface_shape
from composable_agents.validate import Diagnostic

from .fixtures import GoldenFixture


@dataclass(frozen=True)
class GoldenSnapshot:
    """Canonical JSON plus derived hashes for one fixture build."""

    payload: dict[str, Any]
    canonical_json: str
    hashes: dict[str, str]


def canonical_json(value: Any) -> str:
    """Strict canonical JSON for tests; non-JSON values should fail loudly."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_json(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _diagnostic_json(diagnostic: Diagnostic) -> dict[str, str]:
    return {
        "code": diagnostic.code,
        "message": diagnostic.message,
        "nodeId": diagnostic.node_id,
        "severity": diagnostic.severity,
    }


def _tool_grant_json(grant: ToolGrant) -> dict[str, Any]:
    out: dict[str, Any] = {"name": grant.name}
    if grant.effect is not None:
        out["effect"] = grant.effect.value
    if grant.idempotency is not None:
        out["idempotency"] = grant.idempotency.value
    if grant.approval is not None:
        out["approval"] = grant.approval
    if grant.max_calls is not None:
        out["maxCalls"] = grant.max_calls
    return out


def _capability_json(capabilities: CapabilityManifest | None) -> dict[str, Any] | None:
    if capabilities is None:
        return None

    out: dict[str, Any] = {
        "tools": [
            _tool_grant_json(capabilities.tools[name])
            for name in sorted(capabilities.tools)
        ],
        "network": sorted(capabilities.network),
        "mcpServers": {
            server: capabilities.mcp_servers[server]
            for server in sorted(capabilities.mcp_servers)
        },
    }
    if capabilities._has_reasoners:
        out["reasoners"] = sorted(capabilities.reasoners)
    if capabilities._has_models:
        out["models"] = sorted(capabilities.models)
    if capabilities._has_subflows:
        out["subflows"] = sorted(capabilities.subflows)
    if capabilities._has_memory:
        out["memory"] = sorted(scope.value for scope in capabilities.memory)
    if capabilities.budget is not None:
        budget: dict[str, Any] = {}
        if capabilities.budget.cost is not None:
            budget["cost"] = capabilities.budget.cost
        if capabilities.budget.tokens is not None:
            budget["tokens"] = capabilities.budget.tokens
        if capabilities.budget.wall_seconds is not None:
            budget["wallSeconds"] = capabilities.budget.wall_seconds
        out["budget"] = budget
    return out


def _shape_json(flow: Node) -> dict[str, Any]:
    nodes = [
        {
            "closed": closed_shape(node).value,
            "id": node.id,
            "op": node.op.value,
            "surface": surface_shape(node).value,
        }
        for node in flow.walk()
    ]
    return {
        "root": {
            "closed": closed_shape(flow).value,
            "surface": surface_shape(flow).value,
        },
        "nodes": nodes,
    }


def snapshot_fixture(fixture: GoldenFixture) -> GoldenSnapshot:
    deployment = fixture.deploy()
    validate_diagnostics = validate(deployment.flow, deployment.manifest)
    manifest_json = manifest_to_json(deployment.manifest)
    shape_json = _shape_json(deployment.flow)

    payload: dict[str, Any] = {
        "name": fixture.name,
        "flowJson": deployment.flow.to_json(),
        "manifestJson": manifest_json,
        "toolHashes": sorted(deployment.manifest),
        "capabilities": _capability_json(fixture.capabilities),
        "validateDiagnostics": [_diagnostic_json(d) for d in validate_diagnostics],
        "deployDiagnostics": [_diagnostic_json(d) for d in deployment.diagnostics],
        "shapes": shape_json,
    }
    hashes = {
        "flowJson": _sha256_json(payload["flowJson"]),
        "manifestJson": _sha256_json(payload["manifestJson"]),
        "validateDiagnostics": _sha256_json(payload["validateDiagnostics"]),
        "shapes": _sha256_json(payload["shapes"]),
        "snapshot": _sha256_json(payload),
    }
    return GoldenSnapshot(
        payload=payload,
        canonical_json=canonical_json(payload),
        hashes=hashes,
    )
