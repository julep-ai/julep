"""Build and publish signed CAS bundle manifests for deployments."""

from __future__ import annotations

import inspect
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .cas import CASStore
from .ir import canonical_json
from .registry import DEFAULT_REGISTRY, Registry, _text_hash

if TYPE_CHECKING:
    from .deploy import Deployment

ABI_PYTHON_SOURCE_JSON_V1 = "python-source/json-v1"
_SEED_HEX = re.compile(r"^[0-9a-fA-F]{64}$")


class BundleError(Exception):
    pass


class BundleSigningError(BundleError):
    pass


class BundlePureSourceError(BundleError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


def _signing_seed(value: str | None) -> bytes:
    raw = value if value is not None else os.environ.get("CA_BUNDLE_SIGNING_KEY")
    if raw is None or raw.strip() == "":
        raise BundleSigningError(
            "bundle signing requires a signing_key parameter or CA_BUNDLE_SIGNING_KEY"
        )

    text = raw.strip()
    if not _SEED_HEX.fullmatch(text):
        path = Path(text).expanduser()
        try:
            exists = path.exists()
        except OSError:
            exists = False
        if exists:
            text = path.read_text(encoding="utf-8").strip()

    if not _SEED_HEX.fullmatch(text):
        raise BundleSigningError(
            "bundle signing key must be a 64-hex ed25519 seed or a path to a file "
            "containing that seed"
        )
    return bytes.fromhex(text)


def _signature_blob(manifest_bytes: bytes, bundle_hash: str, signing_key: str | None) -> dict[str, str]:
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ModuleNotFoundError as e:
        raise BundleSigningError(
            "bundle signing requires cryptography; install it with pip install "
            "'composable-agents[store]'"
        ) from e

    private_key = Ed25519PrivateKey.from_private_bytes(_signing_seed(signing_key))
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return {
        "algo": "ed25519",
        "bundleHash": bundle_hash,
        "publicKey": public_key.hex(),
        "sig": private_key.sign(manifest_bytes).hex(),
    }


def _custom_pure_sources(
    deployment: Deployment,
    registry: Registry,
) -> list[dict[str, str]]:
    pure_hashes = deployment.artifact_components["pureSourceHashes"]
    if not isinstance(pure_hashes, dict):
        raise BundlePureSourceError("deployment artifact has malformed pureSourceHashes")

    records: list[dict[str, str]] = []
    for name in sorted(pure_hashes):
        if name.startswith("std."):
            continue

        pinned = pure_hashes[name]
        if pinned is None:
            raise BundlePureSourceError(
                f"pure {name!r} must be registered before publish; deploy-time pin is missing"
            )
        if not isinstance(pinned, str):
            raise BundlePureSourceError(f"pure {name!r} has malformed deploy-time pin {pinned!r}")

        entry = registry.pures.get(name)
        current_hash = entry.source_hash if entry is not None else None
        if current_hash is None:
            raise BundlePureSourceError(
                f"pure {name!r} must be registered before publish; no registry entry found"
            )
        assert entry is not None
        if current_hash != pinned:
            raise BundlePureSourceError(
                f"pure {name!r} registration drifted since deploy: "
                f"deploy-time pin {pinned}, registry has {current_hash}"
            )

        if entry.source is not None:
            # A wasm-tier (bundle-sourced) entry already carries its canonical
            # shipped text; never re-inspect a fn (there is no host fn object).
            source = entry.source
        else:
            try:
                source = inspect.getsource(entry.fn)
            except (OSError, TypeError) as e:
                raise BundlePureSourceError(
                    f"pure {name!r} source is not inspectable, so it cannot be shipped; "
                    "register it from an importable source file before publish"
                ) from e

        actual_hash = _text_hash(source)
        if actual_hash != entry.source_hash:
            raise BundlePureSourceError(
                f"pure {name!r} source hash mismatch: inspected source hashes to "
                f"{actual_hash}, registry has {entry.source_hash}"
            )

        records.append({"name": name, "sourceHash": pinned, "source": source})
    return records


def publish_bundle(
    deployment: Deployment,
    store: CASStore,
    *,
    signing_key: str | None = None,
    registry: Registry = DEFAULT_REGISTRY,
) -> dict[str, Any]:
    pure_sources = _custom_pure_sources(deployment, registry)

    manifest_pures: list[dict[str, str]] = []
    for pure_record in pure_sources:
        source_digest = store.put(pure_record["source"].encode("utf-8"))
        manifest_pures.append(
            {
                "abi": ABI_PYTHON_SOURCE_JSON_V1,
                "name": pure_record["name"],
                "source": source_digest,
                "sourceHash": pure_record["sourceHash"],
            }
        )

    flow_digest = store.put(_canonical_bytes(deployment.flow_json))
    artifact_components_digest = store.put(_canonical_bytes(deployment.artifact_components))
    artifact_hash_digest = deployment.artifact_hash.removeprefix("sha256:")
    if artifact_components_digest != artifact_hash_digest:
        raise BundleError(
            "deployment artifact hash does not match canonical artifact components bytes"
        )

    manifest = {
        "artifactHash": deployment.artifact_hash,
        "artifactComponents": artifact_components_digest,
        "flow": flow_digest,
        "pures": manifest_pures,
        "signature": None,
    }
    manifest_bytes = _canonical_bytes(manifest)
    # By construction, the stored manifest CAS digest is the unsigned manifest hash.
    bundle_hash = store.put(manifest_bytes)

    signature_digest = store.put(
        _canonical_bytes(_signature_blob(manifest_bytes, bundle_hash, signing_key))
    )
    # Bundle (register_pure_from_source) pures resolve to the WASM tier on a
    # worker; the published runtime identity must reflect that real executor tier,
    # not 'native'. std.* pures never appear in manifest_pures (they stay baked).
    pure_runtime_refs = {
        pure_record["name"]: {
            "sourceHash": pure_record["sourceHash"],
            "abi": pure_record["abi"],
            "bundleHash": bundle_hash,
            "executorTier": "wasm",
        }
        for pure_record in manifest_pures
    }
    return {
        "bundleHash": bundle_hash,
        "signatureDigest": signature_digest,
        "publishedArtifactHash": deployment.artifact_hash_with_refs(pure_runtime_refs),
        "pureRuntimeRefs": pure_runtime_refs,
    }
