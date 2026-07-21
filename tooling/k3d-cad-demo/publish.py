"""Publish the grade-scores bundle to the shared CAS dir and emit worker env.

Run from the repo root (uv venv has cryptography via the [store] extra)::

    CAS_DIR=/tmp/julep-cad-cas ENV_OUT=/tmp/julep-cad-env.json \
        uv run python tooling/k3d-cad-demo/publish.py

Writes the signed CAS bundle (manifest + flowJson + pure source + detached
signature) into ``$CAS_DIR`` and prints/saves the env the generic worker needs:
``JULEP_BUNDLES`` (``<bundleHash>:<signatureDigest>``) and the signer public key.
The k3d node bind-mounts ``$CAS_DIR`` at ``/cas``; the pod reads it there.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "examples"))

from cryptography.hazmat.primitives import serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: E402

import grade_scores_flow  # noqa: E402
from julep import _env  # noqa: E402
from julep.cas import LocalDirCAS  # noqa: E402

# DEMO KEY — a fixed ed25519 seed so the demo is reproducible. This is NOT a
# secret; a real deployment generates a seed and keeps it out of the repo.
DEMO_SEED = _env.get(_env.JULEP_BUNDLE_SIGNING_KEY, "c0de" * 16)


def _public_key(seed: str) -> str:
    return (
        Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed))
        .public_key()
        .public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        .hex()
    )


def main() -> None:
    cas_dir = os.environ.get("CAS_DIR", "/tmp/julep-cad-cas")
    Path(cas_dir).mkdir(parents=True, exist_ok=True)
    store = LocalDirCAS(cas_dir)

    deployment = grade_scores_flow.build()
    rec = deployment.publish(store, signing_key=DEMO_SEED)

    env = {
        _env.JULEP_BUNDLES: f"{rec['bundleHash']}:{rec['signatureDigest']}",
        _env.JULEP_BUNDLE_ALLOWED_SIGNERS: _public_key(DEMO_SEED),
        "publishedArtifactHash": rec["publishedArtifactHash"],
        "pures": sorted(deployment.artifact_components["pureSourceHashes"]),
    }
    print(json.dumps(env, indent=2))

    env_out = os.environ.get("ENV_OUT")
    if env_out:
        Path(env_out).write_text(json.dumps(env), encoding="utf-8")


if __name__ == "__main__":
    main()
