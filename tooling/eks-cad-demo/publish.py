"""Publish the grade-scores bundle to an S3 CAS and emit worker env.

Run from the repo root (needs AWS creds in the environment + the [store] extra
for boto3 and ed25519 signing)::

    STORE_URL=s3://bucket/prefix ENV_OUT=/tmp/eks-cad-env.json \
        uv run --extra dev --extra store python tooling/eks-cad-demo/publish.py

Writes the signed CAS bundle (manifest + flowJson + pure source + detached
signature) into the S3 bucket and prints/saves the env the generic worker needs:
``JULEP_BUNDLES`` (``<bundleHash>:<signatureDigest>``) and the signer public key.
The worker pod is given the same ``STORE_URL`` and reads the bundle from S3 at
startup -- zero docker in the per-flow loop: the flow ships as data, not an image.

Both the k3d and EKS demos use the single runtime image definition at
``tooling/runtime-image/Dockerfile``.
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
from julep.cas import cas_from_url  # noqa: E402

# DEMO KEY — a fixed ed25519 seed so the demo is reproducible. NOT a secret; a
# real deployment generates a seed and keeps it out of the repo.
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
    store_url = os.environ.get("STORE_URL")
    if not store_url:
        raise SystemExit("STORE_URL is required, e.g. s3://my-bucket/cad")
    store = cas_from_url(store_url)

    deployment = grade_scores_flow.build()
    rec = deployment.publish(store, signing_key=DEMO_SEED)

    env = {
        "STORE_URL": store_url,
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
