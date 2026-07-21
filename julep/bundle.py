"""Build and publish signed CAS bundle manifests for deployments."""

from __future__ import annotations

import inspect
import re
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from . import _env, deps
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


class PureDepsUnbuildableError(BundleError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


def validate_pure_deps(
    deployment: Deployment,
    *,
    registry: Registry,
    native_grant: Iterable[str] | str | None = None,
) -> None:
    """Fail closed when a referenced dep'd pure cannot run in wasm or native."""
    grants = deps.native_dep_grants(native_grant)
    pure_hashes = deployment.artifact_components["pureSourceHashes"]
    if not isinstance(pure_hashes, dict):
        raise BundlePureSourceError("deployment artifact has malformed pureSourceHashes")

    from .execution import env_builder

    for name in sorted(pure_hashes):
        if not isinstance(name, str) or name.startswith("std."):
            continue
        entry = registry.pures.get(name)
        if entry is None or not entry.deps:
            continue
        if env_builder.supported_deps(entry.deps) or name in grants:
            continue
        offending = env_builder.unsupported_deps(entry.deps)
        raise PureDepsUnbuildableError(
            f"pure {name!r} declares dependency metadata that cannot be built for the "
            "wasm tier: dependency requirement(s) "
            f"{', '.join(repr(dep) for dep in offending)} are off the curated WASI "
            f"wheel list ({', '.join(sorted(env_builder.SUPPORTED_WASI_WHEELS))}). "
            "Use a supported wasi-wheel dependency, or grant this pure the native "
            f"tier by adding {name} to JULEP_PURE_NATIVE_DEPS."
        )


def _signing_seed(value: str | None) -> bytes:
    raw = value if value is not None else _env.get(_env.JULEP_BUNDLE_SIGNING_KEY)
    if raw is None or raw.strip() == "":
        raise BundleSigningError(
            "bundle signing requires a signing_key parameter or JULEP_BUNDLE_SIGNING_KEY"
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
            "'julep[store]'"
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


def bundle_signer_public_key(signing_key: str | None = None) -> str:
    """Return the Ed25519 public key for a configured bundle-signing seed."""

    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ModuleNotFoundError as exc:
        raise BundleSigningError(
            "bundle signing requires cryptography; install it with pip install "
            "'julep[store]'"
        ) from exc
    private_key = Ed25519PrivateKey.from_private_bytes(_signing_seed(signing_key))
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    ).hex()


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
    native_grant: Iterable[str] | str | None = None,
) -> dict[str, Any]:
    grants = deps.native_dep_grants(native_grant)
    validate_pure_deps(deployment, registry=registry, native_grant=grants)
    pure_sources = _custom_pure_sources(deployment, registry)

    manifest_pures: list[dict[str, Any]] = []
    base_component_hash: str | None = None
    env_components: dict[str, str] = {}
    for pure_record in pure_sources:
        source_digest = store.put(pure_record["source"].encode("utf-8"))
        name = pure_record["name"]
        manifest_pure: dict[str, Any] = {
            "abi": ABI_PYTHON_SOURCE_JSON_V1,
            "name": name,
            "source": source_digest,
            "sourceHash": pure_record["sourceHash"],
        }
        entry = registry.pures[name]
        if entry.deps:
            from .execution import env_builder

            if env_builder.supported_deps(entry.deps):
                if base_component_hash is None:
                    base_component_hash = deps.base_component_hash()
                env_hash = deps.env_hash(entry.deps, entry.requires_python, base_component_hash)
                env_component = env_components.get(env_hash)
                if env_component is None:
                    try:
                        built_env_hash, env_component = env_builder.publish_env_component(
                            entry.deps,
                            entry.requires_python,
                            store,
                        )
                    except env_builder.EnvBuildError as e:
                        raise BundleError(
                            f"failed to build dependency env component for pure {name!r}: {e}"
                        ) from e
                    if built_env_hash != env_hash:
                        raise BundleError(
                            f"env builder returned envHash {built_env_hash} for pure {name!r}, "
                            f"expected {env_hash}"
                        )
                    env_components[env_hash] = env_component
                manifest_pure["envHash"] = env_hash
                manifest_pure["envComponent"] = env_component
            elif name in grants:
                manifest_pure["executorTier"] = "native"
                manifest_pure["deps"] = list(entry.deps)
                manifest_pure["requiresPython"] = entry.requires_python
        manifest_pures.append(manifest_pure)

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
    pure_runtime_refs: dict[str, dict[str, str]] = {}
    for pure_record in manifest_pures:
        name = pure_record["name"]
        executor_tier = "native" if pure_record.get("executorTier") == "native" else "wasm"
        ref = {
            "sourceHash": pure_record["sourceHash"],
            "abi": pure_record["abi"],
            "bundleHash": bundle_hash,
            "executorTier": executor_tier,
        }
        if "envHash" in pure_record:
            ref["envHash"] = pure_record["envHash"]
        pure_runtime_refs[name] = ref
    return {
        "bundleHash": bundle_hash,
        "signatureDigest": signature_digest,
        "publishedArtifactHash": deployment.artifact_hash_with_refs(pure_runtime_refs),
        "pureRuntimeRefs": pure_runtime_refs,
    }
