"""Bundle manifest and pureRuntimeRefs helpers for the P1(b) spike."""

from __future__ import annotations

import hashlib
from typing import Any

from composable_agents.ir import canonical_json

ABI_PYTHON_SOURCE_JSON_V1 = "python-source/json-v1"


def canonical_bytes(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


def full_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def registry_text_hash(source: str) -> str:
    return f"pure:{hashlib.sha256(source.encode('utf-8')).hexdigest()[:16]}"


def artifact_hash_for_components(components: dict[str, Any]) -> str:
    digest = full_sha256(canonical_bytes(components))
    return f"sha256:{digest}"


def make_bundle_manifest(
    *,
    artifact_hash: str,
    artifact_components_digest: str,
    flow_digest: str,
    pures: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "artifactHash": artifact_hash,
        "artifactComponents": artifact_components_digest,
        "flow": flow_digest,
        "pures": pures,
        "signature": None,
    }


def make_pure_runtime_refs(
    manifest: dict[str, Any],
    *,
    bundle_hash: str,
    executor_tier: str = "wasm",
) -> dict[str, dict[str, str]]:
    refs: dict[str, dict[str, str]] = {}
    for pure in manifest["pures"]:
        refs[pure["name"]] = {
            "sourceHash": pure["sourceHash"],
            "abi": pure["abi"],
            "bundleHash": bundle_hash,
            "executorTier": executor_tier,
        }
    return refs


def join_pure_runtime_refs(
    components: dict[str, Any],
    refs: dict[str, dict[str, str]] | None,
) -> dict[str, Any]:
    joined = dict(components)
    if refs:
        joined["pureRuntimeRefs"] = refs
    return joined
