"""Fresh-process worker for the CAS bundle round-trip spike."""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from cas import LocalDirCas
from julep.contracts import manifest_from_json
from julep.execution.interpreter import InMemoryEnv, interpret
from julep.ir import Node, canonical_json
from julep.projection import InMemoryProjection, ProjectionEmitter
from julep.purity import source_hash_of
from source_registration import assert_authoring_flow_not_loaded, register_pure_source_linecache


def canonical_bytes(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


def full_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def run_from_bundle(cas_dir: Path, manifest_digest: str, input_value: Any) -> dict[str, Any]:
    assert_authoring_flow_not_loaded()
    cas = LocalDirCas(cas_dir)

    manifest = json.loads(cas.get(manifest_digest).decode("utf-8"))
    if manifest_digest != full_sha256(canonical_bytes(manifest)):
        raise RuntimeError("manifest digest does not match canonical JSON bytes")

    artifact_components = json.loads(cas.get(manifest["artifactComponents"]).decode("utf-8"))
    artifact_digest = full_sha256(canonical_bytes(artifact_components))
    if manifest["artifactHash"] != f"sha256:{artifact_digest}":
        raise RuntimeError("artifactHash does not match artifactComponents CAS blob")
    pinned_pures = artifact_components["pureSourceHashes"]

    verified_pures = {}
    for pure in manifest["pures"]:
        source_bytes = cas.get(pure["source"])
        if full_sha256(source_bytes) != pure["source"]:
            raise RuntimeError(f"source CAS digest mismatch for {pure['name']}")
        source = source_bytes.decode("utf-8")
        actual = register_pure_source_linecache(pure["name"], source)
        if actual != pure["sourceHash"]:
            raise RuntimeError(f"sourceHash mismatch for {pure['name']}: {actual}")
        if actual != pinned_pures[pure["name"]]:
            raise RuntimeError(f"artifact pure pin mismatch for {pure['name']}: {actual}")
        if actual != source_hash_of(pure["name"]):
            raise RuntimeError(f"registry readback mismatch for {pure['name']}")
        verified_pures[pure["name"]] = actual

    flow_json = json.loads(cas.get(manifest["flow"]).decode("utf-8"))
    flow = Node.from_json(flow_json)
    manifest_json = artifact_components.get("manifestJson", {})
    env = InMemoryEnv(
        manifest_from_json(manifest_json),
        ProjectionEmitter(InMemoryProjection()),
    )
    result = await interpret(flow, input_value, env)
    assert_authoring_flow_not_loaded()
    return {
        "output": result.value,
        "verifiedPures": verified_pures,
        "manifestDigest": manifest_digest,
        "artifactHash": manifest["artifactHash"],
    }


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(
            "usage: worker_main.py <cas-dir> <manifest-digest> <input-json>",
            file=sys.stderr,
        )
        return 2
    cas_dir = Path(argv[1])
    manifest_digest = argv[2]
    input_value = json.loads(argv[3])
    out = asyncio.run(run_from_bundle(cas_dir, manifest_digest, input_value))
    print(json.dumps(out, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
