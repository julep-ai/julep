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
from dataclasses import dataclass
from typing import Any, cast

from . import deps
from .bundle import ABI_PYTHON_SOURCE_JSON_V1, BundleError
from .cas import CASError, CASStore, cas_from_url
from .registry import DEFAULT_REGISTRY, PureEntry, Registry, _text_hash

_SHA256_HEX = re.compile(r"^[0-9a-fA-F]{64}$")
_HEX = re.compile(r"^[0-9a-fA-F]+$")


class BundleResolutionError(BundleError):
    pass


@dataclass(frozen=True)
class _ManifestPure:
    name: str
    abi: str
    source: str
    source_hash: str
    executor_tier: str = "wasm"
    env_hash: str | None = None
    env_component: str | None = None
    dep_list: tuple[str, ...] = ()
    requires_python: str | None = None


@dataclass(frozen=True)
class _VerifiedPure:
    name: str
    source_hash: str
    source: str
    executor_tier: str = "wasm"
    env_hash: str | None = None
    env_component: str | None = None
    dep_list: tuple[str, ...] = ()
    requires_python: str | None = None


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


def _manifest_pures(manifest: dict[str, Any]) -> list[_ManifestPure]:
    pures = manifest.get("pures")
    if not isinstance(pures, list):
        raise BundleResolutionError("bundle manifest pures must be a list")

    out: list[_ManifestPure] = []
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
        env_hash = raw.get("envHash")
        env_component = raw.get("envComponent")
        executor_tier_raw = raw.get("executorTier")
        if executor_tier_raw is None:
            executor_tier = "wasm"
        elif executor_tier_raw in {"wasm", "native"}:
            assert isinstance(executor_tier_raw, str)
            executor_tier = executor_tier_raw
        else:
            raise BundleResolutionError(
                f"bundle manifest pure {name!r} has unsupported executorTier "
                f"{executor_tier_raw!r}"
            )
        dep_list_raw = raw.get("deps")
        requires_python_raw = raw.get("requiresPython")
        if requires_python_raw is not None and not isinstance(requires_python_raw, str):
            raise BundleResolutionError(
                f"bundle manifest pure {name!r} has malformed requiresPython"
            )
        requires_python = requires_python_raw
        if (env_hash is None) != (env_component is None):
            raise BundleResolutionError(
                f"bundle manifest pure {name!r} must carry envHash and envComponent together"
            )
        if env_hash is not None:
            if not isinstance(env_hash, str) or _SHA256_HEX.fullmatch(env_hash) is None:
                raise BundleResolutionError(
                    f"bundle manifest pure {name!r} has malformed envHash"
                )
            if not isinstance(env_component, str) or _SHA256_HEX.fullmatch(env_component) is None:
                raise BundleResolutionError(
                    f"bundle manifest pure {name!r} has malformed envComponent"
                )
            env_hash = env_hash.lower()
            env_component = env_component.lower()
        dep_list: tuple[str, ...] = ()
        if executor_tier == "native":
            if env_hash is not None or env_component is not None:
                raise BundleResolutionError(
                    f"bundle manifest pure {name!r} native tier must not carry "
                    "envHash/envComponent"
                )
            if (
                not isinstance(dep_list_raw, list)
                or not dep_list_raw
                or not all(isinstance(dep, str) for dep in dep_list_raw)
            ):
                raise BundleResolutionError(
                    f"bundle manifest pure {name!r} native tier requires non-empty "
                    "deps list"
                )
            dep_list = tuple(sorted(set(cast(list[str], dep_list_raw))))
        elif dep_list_raw is not None or "requiresPython" in raw:
            raise BundleResolutionError(
                f"bundle manifest pure {name!r} must not carry deps/requiresPython "
                "outside the native tier"
            )
        if name.startswith("std."):
            raise BundleResolutionError(
                f"bundle manifest must not include std.* pure {name!r}; std pures stay baked"
            )
        if abi != ABI_PYTHON_SOURCE_JSON_V1:
            raise BundleResolutionError(f"unsupported pure ABI for {name!r}: {abi!r}")
        out.append(
            _ManifestPure(
                name=name,
                abi=abi,
                source=source,
                source_hash=source_hash,
                executor_tier=executor_tier,
                env_hash=env_hash,
                env_component=env_component,
                dep_list=dep_list,
                requires_python=requires_python,
            )
        )
    return out


def resolve_and_register(
    store: CASStore,
    bundle_hash: str,
    *,
    signature_digest: str | None = None,
    allowed_signers: Sequence[str] | None = None,
    native_grant: Sequence[str] | str | None = None,
    registry: Registry = DEFAULT_REGISTRY,
) -> dict[str, Any]:
    """Resolve a signed CAS bundle and register its pures by manifest tier.

    Wasm pures execute in the wasmtime sandbox. Native dependency pures require
    an explicit CA_PURE_NATIVE_DEPS grant on this worker and are registered as
    native_venv source-only pures.
    """

    signers = _allowed_signers(allowed_signers)
    native_grants = deps.native_dep_grants(native_grant)
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
    flow_digest = manifest.get("flow")
    if not isinstance(artifact_components, str) or not isinstance(artifact_hash, str):
        raise BundleResolutionError("bundle manifest has malformed artifact fields")
    if not isinstance(flow_digest, str) or _SHA256_HEX.fullmatch(flow_digest) is None:
        raise BundleResolutionError("bundle manifest has malformed flow digest")
    if artifact_hash != f"sha256:{artifact_components}":
        raise BundleResolutionError(
            "bundle manifest artifactHash must equal sha256:artifactComponents"
        )

    verified: list[_VerifiedPure] = []
    for pure_record in _manifest_pures(manifest):
        source_bytes = store.get(pure_record.source)
        try:
            source = source_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            raise BundleResolutionError(
                f"source blob for pure {pure_record.name!r} is not UTF-8"
            ) from e
        actual_hash = _text_hash(source)
        bundled_hash = pure_record.source_hash
        if actual_hash != bundled_hash:
            raise BundleResolutionError(
                f"sourceHash mismatch for pure {pure_record.name!r}: "
                f"source text hashes to {actual_hash}, manifest has {bundled_hash}"
            )

        existing = registry.pures.get(pure_record.name)
        if existing is not None and existing.source_hash != bundled_hash:
            raise BundleResolutionError(
                f"pure {pure_record.name!r} is already baked with hash "
                f"{existing.source_hash}, but bundle {bundle_hash} provides {bundled_hash}. "
                "Likely cause: a stale worker image (baked code is behind the bundle) or "
                "a stale bundle (published before the pure changed). Rebuild/redeploy the "
                "image, or republish."
            )
        verified.append(
            _VerifiedPure(
                name=pure_record.name,
                source_hash=bundled_hash,
                source=source,
                executor_tier=pure_record.executor_tier,
                env_hash=pure_record.env_hash,
                env_component=pure_record.env_component,
                dep_list=pure_record.dep_list,
                requires_python=pure_record.requires_python,
            )
        )

    for verified_pure in verified:
        if verified_pure.executor_tier == "native" and verified_pure.name not in native_grants:
            raise BundleResolutionError(
                f"bundle pure {verified_pure.name!r} requests native dependency tier, "
                "but this worker has not granted it via CA_PURE_NATIVE_DEPS"
            )

    if verified:
        _validate_sources_without_registering(verified)
        _validate_native_metadata(verified)

    wasm_verified = [pure for pure in verified if pure.executor_tier == "wasm"]
    # Wasm verified pures probe the wasm runtime NOW — at resolution (worker init
    # / fresh-activation), before any pure lookup — and eagerly build the
    # process-global executor. Otherwise a worker missing the `wasm` extra
    # registers the pures fine and then fails LATE with a raw ModuleNotFoundError
    # at the first lookup inside workflow code (a WorkflowTaskFailed mid-run).
    # Fail fast at resolution with install guidance.
    if wasm_verified:
        _ensure_wasm_runtime()
        _register_env_components(store, wasm_verified)

    registered: dict[str, str] = {}
    base_component_hash: str | None = None
    for verified_pure in verified:
        tier = "native_venv" if verified_pure.executor_tier == "native" else "wasm"
        entry = registry.register_pure_from_source(
            verified_pure.name,
            verified_pure.source,
            tier=tier,
        )
        if verified_pure.executor_tier == "native":
            assert entry.deps == verified_pure.dep_list
            assert entry.requires_python == verified_pure.requires_python
        if verified_pure.env_hash is not None:
            if base_component_hash is None:
                base_component_hash = deps.base_component_hash()
            expected_env_hash = _entry_env_hash(entry, base_component_hash)
            if expected_env_hash != verified_pure.env_hash:
                raise BundleResolutionError(
                    f"envHash mismatch for pure {verified_pure.name!r}: manifest has "
                    f"{verified_pure.env_hash}, worker re-derived {expected_env_hash}"
                )
            registry.set_pure_env_hash(verified_pure.name, verified_pure.env_hash)
        registered[verified_pure.name] = verified_pure.source_hash

    return {
        "bundleHash": bundle_hash,
        "artifactHash": artifact_hash,
        "artifactComponents": artifact_components,
        "flow": flow_digest,
        "registered": registered,
    }


def _validate_sources_without_registering(verified: Sequence[_VerifiedPure]) -> None:
    scratch = Registry()
    for pure_record in verified:
        try:
            scratch.register_pure_from_source(pure_record.name, pure_record.source)
        except ValueError as e:
            raise BundleResolutionError(str(e)) from e


def _validate_native_metadata(verified: Sequence[_VerifiedPure]) -> None:
    for pure_record in verified:
        if pure_record.executor_tier != "native":
            continue
        try:
            parsed_deps, requires_python = deps.parse_pep723(pure_record.source)
        except ValueError as e:
            raise BundleResolutionError(
                f"native pure {pure_record.name!r} has malformed dependency metadata"
            ) from e
        if parsed_deps != pure_record.dep_list:
            raise BundleResolutionError(
                f"dependency metadata mismatch for native pure {pure_record.name!r}: "
                f"manifest has {list(pure_record.dep_list)!r}, source declares "
                f"{list(parsed_deps)!r}"
            )
        if requires_python != pure_record.requires_python:
            raise BundleResolutionError(
                f"requiresPython mismatch for native pure {pure_record.name!r}: "
                f"manifest has {pure_record.requires_python!r}, source declares "
                f"{requires_python!r}"
            )


def _entry_env_hash(entry: PureEntry, base_component_hash: str) -> str:
    if not entry.deps:
        raise BundleResolutionError(
            f"pure {entry.name!r} carries envHash but declares no dependencies"
        )
    return deps.env_hash(entry.deps, entry.requires_python, base_component_hash)


def _register_env_components(store: CASStore, verified: Sequence[_VerifiedPure]) -> None:
    from .execution.wasm_executor import get_wasm_executor

    executor = get_wasm_executor()
    base_component_hash: str | None = None
    for pure_record in verified:
        try:
            parsed_deps, requires_python = deps.parse_pep723(pure_record.source)
        except ValueError as e:
            raise BundleResolutionError(
                f"pure {pure_record.name!r} has malformed dependency metadata"
            ) from e
        if pure_record.env_hash is None:
            if parsed_deps:
                raise BundleResolutionError(
                    f"wasm pure {pure_record.name!r} declares dependencies and must ship "
                    "envHash/envComponent"
                )
            continue
        if pure_record.env_component is None:
            raise BundleResolutionError(
                f"pure {pure_record.name!r} carries envHash without envComponent"
            )
        if not parsed_deps:
            raise BundleResolutionError(
                f"pure {pure_record.name!r} carries envHash but declares no dependencies"
            )
        if base_component_hash is None:
            base_component_hash = deps.base_component_hash()
        expected_env_hash = deps.env_hash(parsed_deps, requires_python, base_component_hash)
        if expected_env_hash != pure_record.env_hash:
            raise BundleResolutionError(
                f"envHash mismatch for pure {pure_record.name!r}: manifest has "
                f"{pure_record.env_hash}, worker re-derived {expected_env_hash}"
            )
        try:
            component_bytes = store.get(pure_record.env_component)
        except CASError as e:
            raise BundleResolutionError(
                f"env component {pure_record.env_component} for pure {pure_record.name!r} "
                "is missing or failed CAS verification"
            ) from e
        try:
            executor.register_env_component(pure_record.env_hash, component_bytes)
        except Exception as e:
            raise BundleResolutionError(
                f"failed to load env component {pure_record.env_component} for pure "
                f"{pure_record.name!r} envHash {pure_record.env_hash}: {e}"
            ) from e


def _ensure_wasm_runtime() -> None:
    """Fail fast if the wasm tier cannot run, and eagerly init the executor.

    Bundle-sourced pures run in the wasmtime sandbox, which requires the optional
    `wasm` extra (``wasmtime``) and the vendored ``executor.wasm`` component. This
    probe runs at resolution time so a misconfigured image fails BEFORE accepting
    work, rather than with a raw ``ModuleNotFoundError`` at the first pure lookup
    deep inside workflow code. Eagerly constructing the process-global executor
    here also moves the one-time component load / ``.cwasm`` cache IO (and any
    epoch thread) out of the Temporal workflow sandbox.
    """
    try:
        from .execution.wasm_executor import get_wasm_executor
    except ModuleNotFoundError as e:
        raise BundleResolutionError(
            "bundle-sourced pures run in the wasm sandbox, which requires the "
            "'wasm' extra (wasmtime). Install it: pip install "
            "'composable-agents[wasm]'."
        ) from e

    try:
        get_wasm_executor()
    except FileNotFoundError as e:
        raise BundleResolutionError(
            "the vendored wasm executor component is missing from this image; "
            "rebuild the worker image with composable-agents[wasm] so "
            "composable_agents/execution/_wasm/executor.wasm is present."
        ) from e


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


def bundle_ref_entries(raw: Any) -> list[tuple[str, str]]:
    """Parse workflow-input bundle refs into resolver entries.

    ``None`` means "no bundle" and is a no-op. A present-but-malformed value
    fails closed so signed code cannot silently fall back to stale ambient
    registry state.
    """
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise BundleResolutionError(
            f"malformed bundle: expected a list of refs, got {type(raw).__name__}"
        )

    entries: list[tuple[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise BundleResolutionError(
                f"malformed bundle ref: expected an object, got {type(item).__name__}"
            )
        bundle_hash = item.get("bundleHash")
        signature_digest = item.get("signatureDigest")
        if not isinstance(bundle_hash, str) or not isinstance(signature_digest, str):
            raise BundleResolutionError(
                "malformed bundle ref: bundleHash and signatureDigest must be strings"
            )
        if _SHA256_HEX.fullmatch(bundle_hash) is None or _SHA256_HEX.fullmatch(signature_digest) is None:
            raise BundleResolutionError(
                "malformed bundle ref; expected bundleHash/signatureDigest as 64 hex chars"
            )
        entries.append((bundle_hash.lower(), signature_digest.lower()))
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
