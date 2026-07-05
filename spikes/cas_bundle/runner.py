"""Reproduce with: uv run python spikes/cas_bundle/runner.py"""

from __future__ import annotations

import asyncio
import inspect
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SPIKE_DIR = Path(__file__).resolve().parent

if str(SPIKE_DIR) not in sys.path:
    sys.path.insert(0, str(SPIKE_DIR))

from authoring_flow import AUTHORING_INPUT, FLOW, PURE_NAMES  # noqa: E402
from bundle import (  # noqa: E402
    ABI_PYTHON_SOURCE_JSON_V1,
    artifact_hash_for_components,
    canonical_bytes,
    join_pure_runtime_refs,
    make_bundle_manifest,
    make_pure_runtime_refs,
)
from cas import LocalDirCas  # noqa: E402
from julep import McpSnapshot, deploy  # noqa: E402
from julep.execution.interpreter import InMemoryEnv, interpret  # noqa: E402
from julep.projection import InMemoryProjection, ProjectionEmitter  # noqa: E402
from julep.purity import source_hash_of  # noqa: E402
from julep.registry import DEFAULT_REGISTRY  # noqa: E402


async def baked_run(deployment: Any) -> Any:
    env = InMemoryEnv(deployment.manifest, ProjectionEmitter(InMemoryProjection()))
    result = await interpret(deployment.flow, AUTHORING_INPUT, env)
    return result.value


def source_for_pure(name: str) -> str:
    return inspect.getsource(DEFAULT_REGISTRY.pures[name].fn)


def publish_bundle(deployment: Any, cas: LocalDirCas) -> tuple[str, dict[str, Any]]:
    artifact_components_digest = cas.put(canonical_bytes(deployment.artifact_components))
    flow_digest = cas.put(canonical_bytes(deployment.flow_json))
    pures = []
    for name in PURE_NAMES:
        source = source_for_pure(name)
        source_digest = cas.put(source.encode("utf-8"))
        pures.append(
            {
                "name": name,
                "sourceHash": source_hash_of(name),
                "source": source_digest,
                "abi": ABI_PYTHON_SOURCE_JSON_V1,
            }
        )
    manifest = make_bundle_manifest(
        artifact_hash=deployment.artifact_hash,
        artifact_components_digest=artifact_components_digest,
        flow_digest=flow_digest,
        pures=pures,
    )
    manifest_digest = cas.put(canonical_bytes(manifest))
    return manifest_digest, manifest


def prove_pure_runtime_refs_join(
    deployment: Any,
    refs: dict[str, dict[str, str]],
) -> tuple[str, str, str]:
    absent_hash = artifact_hash_for_components(
        join_pure_runtime_refs(deployment.artifact_components, None)
    )
    empty_hash = artifact_hash_for_components(
        join_pure_runtime_refs(deployment.artifact_components, {})
    )
    present_hash = artifact_hash_for_components(
        join_pure_runtime_refs(deployment.artifact_components, refs)
    )
    if absent_hash != deployment.artifact_hash:
        raise AssertionError(f"refs-absent hash drifted: {absent_hash} != {deployment.artifact_hash}")
    if empty_hash != deployment.artifact_hash:
        raise AssertionError(f"refs-empty hash drifted: {empty_hash} != {deployment.artifact_hash}")
    if present_hash == deployment.artifact_hash:
        raise AssertionError("refs-present hash unexpectedly matched existing artifact hash")
    return absent_hash, empty_hash, present_hash


def run_worker(cas_dir: Path, manifest_digest: str) -> dict[str, Any]:
    proc = subprocess.run(
        [
            sys.executable,
            str(SPIKE_DIR / "worker_main.py"),
            str(cas_dir),
            manifest_digest,
            json.dumps(AUTHORING_INPUT, sort_keys=True, separators=(",", ":")),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"worker failed with exit {proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return json.loads(proc.stdout)


def main() -> int:
    cas_dir = SPIKE_DIR / ".cas"
    cas = LocalDirCas(cas_dir)
    deployment = deploy(FLOW, McpSnapshot())
    baked_output = asyncio.run(baked_run(deployment))
    manifest_digest, manifest = publish_bundle(deployment, cas)
    refs = make_pure_runtime_refs(manifest, bundle_hash=manifest_digest)
    absent_hash, empty_hash, present_hash = prove_pure_runtime_refs_join(deployment, refs)
    worker = run_worker(cas_dir, manifest_digest)
    if worker["output"] != baked_output:
        raise AssertionError(f"worker output {worker['output']!r} != baked {baked_output!r}")

    transcript = {
        "status": "PASS",
        "casDir": str(cas_dir.relative_to(ROOT)),
        "artifactHash": deployment.artifact_hash,
        "manifestDigest": manifest_digest,
        "flowDigest": manifest["flow"],
        "pureSourceDigests": {pure["name"]: pure["source"] for pure in manifest["pures"]},
        "pureSourceHashes": {pure["name"]: pure["sourceHash"] for pure in manifest["pures"]},
        "pureRuntimeRefs": refs,
        "artifactHashProof": {
            "absentRefs": absent_hash,
            "emptyRefs": empty_hash,
            "presentRefs": present_hash,
        },
        "bakedOutput": baked_output,
        "workerOutput": worker["output"],
        "workerVerifiedPures": worker["verifiedPures"],
        "workerDidNotImportAuthoringFlow": True,
    }
    print(json.dumps(transcript, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
