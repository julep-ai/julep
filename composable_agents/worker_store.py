"""Startup-preload resolution for CAS bundles.

Bundle resolution deliberately happens at worker init, before any workflow task
is accepted, and never inside workflow code. Temporal workflow code cannot do
I/O. Lazy in-workflow resolution would also break replay on a fresh worker: the
pure must already be registered when history replays.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Sequence
from typing import Any

from .bundle import ABI_PYTHON_SOURCE_JSON_V1, BundleError
from .cas import CASStore, cas_from_url
from .registry import DEFAULT_REGISTRY, Registry, _text_hash

_SHA256_HEX = re.compile(r"^[0-9a-fA-F]{64}$")
_HEX = re.compile(r"^[0-9a-fA-F]+$")


class BundleResolutionError(BundleError):
    pass


def _json_object(data: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise BundleResolutionError(f"{label} is not valid UTF-8 JSON") from e
    if not isinstance(value, dict):
        raise BundleResolutionError(f"{label} must be a JSON object")
    return value


def _allowed_signers(allowed_signers: Sequence[str] | None) -> set[str]:
    raw = allowed_signers
    if raw is None:
        env_value = os.environ.get("CA_BUNDLE_ALLOWED_SIGNERS", "")
        raw = [part.strip() for part in env_value.split(",")]

    normalized = {signer.strip().lower() for signer in raw if signer.strip()}
    if not normalized:
        raise BundleResolutionError(
            "bundle resolution requires allowed_signers or CA_BUNDLE_ALLOWED_SIGNERS"
        )
    for signer in normalized:
        if not _HEX.fullmatch(signer):
            raise BundleResolutionError(f"allowed signer is not hex: {signer!r}")
    return normalized


def _verify_signature(public_key_hex: str, signature_hex: str, data: bytes) -> None:
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ModuleNotFoundError as e:
        raise BundleResolutionError(
            "bundle verification requires cryptography; install it with pip install "
            "'composable-agents[store]'"
        ) from e

    try:
        public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
        signature = bytes.fromhex(signature_hex)
        public_key.verify(signature, data)
    except InvalidSignature as e:
        raise BundleResolutionError("bundle signature verification failed") from e
    except ValueError as e:
        raise BundleResolutionError("bundle signature object contains invalid hex") from e


def _manifest_pures(manifest: dict[str, Any]) -> list[dict[str, str]]:
    pures = manifest.get("pures")
    if not isinstance(pures, list):
        raise BundleResolutionError("bundle manifest pures must be a list")

    out: list[dict[str, str]] = []
    for raw in pures:
        if not isinstance(raw, dict):
            raise BundleResolutionError("bundle manifest pure records must be objects")
        name = raw.get("name")
        abi = raw.get("abi")
        source = raw.get("source")
        source_hash = raw.get("sourceHash")
        if not all(isinstance(value, str) for value in (name, abi, source, source_hash)):
            raise BundleResolutionError("bundle manifest pure record has malformed fields")
        assert isinstance(name, str)
        assert isinstance(abi, str)
        assert isinstance(source, str)
        assert isinstance(source_hash, str)
        if name.startswith("std."):
            raise BundleResolutionError(
                f"bundle manifest must not include std.* pure {name!r}; std pures stay baked"
            )
        if abi != ABI_PYTHON_SOURCE_JSON_V1:
            raise BundleResolutionError(f"unsupported pure ABI for {name!r}: {abi!r}")
        out.append({"name": name, "abi": abi, "source": source, "sourceHash": source_hash})
    return out


def resolve_and_register(
    store: CASStore,
    bundle_hash: str,
    *,
    signature_digest: str | None = None,
    allowed_signers: Sequence[str] | None = None,
    require_native_grant: bool = True,
    registry: Registry = DEFAULT_REGISTRY,
) -> dict[str, Any]:
    if require_native_grant and os.environ.get("CA_BUNDLE_NATIVE_EXEC") != "1":
        raise BundleResolutionError(
            "bundle-sourced pures execute natively in-process in P2; this is a dev-only "
            "mode enabled by setting CA_BUNDLE_NATIVE_EXEC=1. The production path is "
            "the plan's P3 wasm executor tier."
        )

    signers = _allowed_signers(allowed_signers)
    if signature_digest is None:
        raise BundleResolutionError("bundle is unsigned: no signature reference provided")

    signature = _json_object(store.get(signature_digest), "bundle signature")
    if signature.get("algo") != "ed25519":
        raise BundleResolutionError("bundle signature algo must be 'ed25519'")
    if signature.get("bundleHash") != bundle_hash:
        raise BundleResolutionError("bundle signature does not match requested bundle hash")
    public_key = signature.get("publicKey")
    sig = signature.get("sig")
    if not isinstance(public_key, str) or not isinstance(sig, str):
        raise BundleResolutionError("bundle signature object has malformed publicKey or sig")
    public_key = public_key.lower()
    if public_key not in signers:
        raise BundleResolutionError(f"bundle signer is not in the allowlist: {public_key}")

    manifest_bytes = store.get(bundle_hash)
    _verify_signature(public_key, sig, manifest_bytes)

    manifest = _json_object(manifest_bytes, "bundle manifest")
    if manifest.get("signature") is not None:
        raise BundleResolutionError("bundle manifest signature field must be null")
    artifact_components = manifest.get("artifactComponents")
    artifact_hash = manifest.get("artifactHash")
    if not isinstance(artifact_components, str) or not isinstance(artifact_hash, str):
        raise BundleResolutionError("bundle manifest has malformed artifact fields")
    if artifact_hash != f"sha256:{artifact_components}":
        raise BundleResolutionError(
            "bundle manifest artifactHash must equal sha256:artifactComponents"
        )

    verified: list[tuple[str, str, str]] = []
    for pure_record in _manifest_pures(manifest):
        source_bytes = store.get(pure_record["source"])
        try:
            source = source_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            raise BundleResolutionError(
                f"source blob for pure {pure_record['name']!r} is not UTF-8"
            ) from e
        actual_hash = _text_hash(source)
        bundled_hash = pure_record["sourceHash"]
        if actual_hash != bundled_hash:
            raise BundleResolutionError(
                f"sourceHash mismatch for pure {pure_record['name']!r}: "
                f"source text hashes to {actual_hash}, manifest has {bundled_hash}"
            )

        existing = registry.pures.get(pure_record["name"])
        if existing is not None and existing.source_hash != bundled_hash:
            raise BundleResolutionError(
                f"pure {pure_record['name']!r} is already baked with hash "
                f"{existing.source_hash}, but bundle {bundle_hash} provides {bundled_hash}. "
                "Likely cause: a stale worker image (baked code is behind the bundle) or "
                "a stale bundle (published before the pure changed). Rebuild/redeploy the "
                "image, or republish."
            )
        verified.append((pure_record["name"], bundled_hash, source))

    registered: dict[str, str] = {}
    for name, source_hash, source in verified:
        registry.register_pure_from_source(name, source)
        registered[name] = source_hash

    return {
        "bundleHash": bundle_hash,
        "artifactHash": artifact_hash,
        "registered": registered,
    }


def _bundle_entries(raw: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for entry in raw.split(","):
        item = entry.strip()
        if not item:
            continue
        parts = item.split(":")
        if len(parts) != 2 or not all(_SHA256_HEX.fullmatch(part) for part in parts):
            raise BundleResolutionError(
                "malformed CA_BUNDLES entry; expected "
                "<bundleHash>:<signatureDigest> with 64 hex chars on each side"
            )
        entries.append((parts[0].lower(), parts[1].lower()))
    return entries


def resolve_entries(
    store: CASStore,
    entries: Sequence[tuple[str, str]],
    *,
    registry: Registry = DEFAULT_REGISTRY,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for bundle_hash, signature_digest in entries:
        records.append(
            resolve_and_register(
                store,
                bundle_hash.lower(),
                signature_digest=signature_digest.lower(),
                registry=registry,
            )
        )
    return records


def load_bundles_from_env(*, registry: Registry = DEFAULT_REGISTRY) -> list[dict[str, Any]]:
    raw = os.environ.get("CA_BUNDLES", "")
    if raw.strip() == "":
        return []

    store_url = os.environ.get("STORE_URL")
    if store_url is None or store_url.strip() == "":
        raise BundleResolutionError("STORE_URL is required when CA_BUNDLES is set")

    store = cas_from_url(store_url)
    return resolve_entries(store, _bundle_entries(raw), registry=registry)
