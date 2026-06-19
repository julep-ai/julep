from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from composable_agents import arr, deploy, pure, seq
from composable_agents.bundle import ABI_PYTHON_SOURCE_JSON_V1
from composable_agents.cas import CASIntegrityError, LocalDirCAS
from composable_agents.contracts import manifest_from_json
from composable_agents.execution.interpreter import InMemoryEnv, interpret
from composable_agents.ir import Node, canonical_json
from composable_agents.projection import InMemoryProjection, ProjectionEmitter
from composable_agents.registry import Registry, _text_hash
from composable_agents.worker_store import BundleResolutionError, load_bundles_from_env, resolve_and_register
from conftest import read_snapshot, run


SEED_A = "11" * 32
SEED_B = "22" * 32


@pure("bundle.worker.normalize.v1")
def _bundle_worker_normalize(value: dict[str, Any]) -> dict[str, Any]:
    return {"name": value["name"].strip(), "score": int(value["score"])}


@pure("bundle.worker.summarize.v1")
def _bundle_worker_summarize(value: dict[str, Any]) -> dict[str, Any]:
    return {"summary": f"{value['name']}:{value['score'] + 1}"}


@pure("bundle.worker.with_std.v1")
def _bundle_worker_with_std(value: dict[str, Any]) -> dict[str, Any]:
    return {"wrapped": value}


def _key(seed: str) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed))


def _public_key(seed: str) -> str:
    return _key(seed).public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    ).hex()


def _cas_path(root: Path, digest: str) -> Path:
    return root / digest[:2] / digest[2:4] / digest


def _json_from_store(store: LocalDirCAS, digest: str) -> dict[str, Any]:
    return json.loads(store.get(digest).decode("utf-8"))


def _put_signature(store: LocalDirCAS, bundle_hash: str, seed: str) -> str:
    manifest_bytes = store.get(bundle_hash)
    public_key = _public_key(seed)
    sig = _key(seed).sign(manifest_bytes).hex()
    return store.put(
        canonical_json(
            {
                "algo": "ed25519",
                "bundleHash": bundle_hash,
                "publicKey": public_key,
                "sig": sig,
            }
        ).encode("utf-8")
    )


def _deployment():
    return deploy(
        seq(arr("bundle.worker.normalize.v1"), arr("bundle.worker.summarize.v1")),
        read_snapshot(),
    )


def _published(tmp_path: Path):
    store = LocalDirCAS(tmp_path)
    deployment = _deployment()
    rec = deployment.publish(store, signing_key=SEED_A)
    return store, deployment, rec


def _resolve(
    store: LocalDirCAS,
    rec: dict[str, Any],
    registry: Registry,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Any]:
    monkeypatch.setenv("CA_BUNDLE_NATIVE_EXEC", "1")
    return resolve_and_register(
        store,
        rec["bundleHash"],
        signature_digest=rec["signatureDigest"],
        allowed_signers=[_public_key(SEED_A)],
        registry=registry,
    )


def test_publish_resolve_round_trip_and_interpret_with_fresh_registry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, deployment, rec = _published(tmp_path)
    fresh = Registry()

    resolved = _resolve(store, rec, fresh, monkeypatch)

    expected_pins = deployment.artifact_components["pureSourceHashes"]
    assert resolved == {
        "bundleHash": rec["bundleHash"],
        "artifactHash": deployment.artifact_hash,
        "registered": expected_pins,
    }
    assert fresh.source_hash_of("bundle.worker.normalize.v1") == expected_pins[
        "bundle.worker.normalize.v1"
    ]
    assert fresh.source_hash_of("bundle.worker.summarize.v1") == expected_pins[
        "bundle.worker.summarize.v1"
    ]

    manifest = _json_from_store(store, rec["bundleHash"])
    flow_json = _json_from_store(store, manifest["flow"])
    flow = Node.from_json(flow_json)
    env = InMemoryEnv(
        manifest_from_json(deployment.manifest_json),
        ProjectionEmitter(InMemoryProjection()),
        registry=fresh,
    )
    value = {"name": " Ada ", "score": "16"}

    result = run(interpret(flow, value, env))

    assert result.value == _bundle_worker_summarize(_bundle_worker_normalize(value))
    assert rec["publishedArtifactHash"] == deployment.artifact_hash_with_refs(
        rec["pureRuntimeRefs"]
    )
    assert rec["publishedArtifactHash"] != deployment.artifact_hash
    assert all(ref["executorTier"] == "native" for ref in rec["pureRuntimeRefs"].values())
    assert {
        name: (ref["sourceHash"], ref["abi"], ref["bundleHash"])
        for name, ref in rec["pureRuntimeRefs"].items()
    } == {
        name: (hash_, ABI_PYTHON_SOURCE_JSON_V1, rec["bundleHash"])
        for name, hash_ in expected_pins.items()
    }


@pytest.mark.parametrize("target", ["manifest", "source", "signature"])
def test_tampering_fails_closed_without_registering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    target: str,
) -> None:
    store, _deployment, rec = _published(tmp_path)
    fresh = Registry()
    signature_digest = rec["signatureDigest"]

    if target == "manifest":
        _cas_path(tmp_path, rec["bundleHash"]).write_bytes(b"{}")
    elif target == "source":
        manifest = _json_from_store(store, rec["bundleHash"])
        _cas_path(tmp_path, manifest["pures"][0]["source"]).write_bytes(b"tampered")
    else:
        signature = _json_from_store(store, rec["signatureDigest"])
        signature["sig"] = ("0" if signature["sig"][0] != "0" else "1") + signature["sig"][1:]
        signature_digest = store.put(canonical_json(signature).encode("utf-8"))

    with pytest.raises((BundleResolutionError, CASIntegrityError)):
        _resolve(
            store,
            {**rec, "signatureDigest": signature_digest},
            fresh,
            monkeypatch,
        )

    assert fresh.pures == {}


def test_unknown_signer_and_unsigned_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, _deployment, rec = _published(tmp_path)
    monkeypatch.setenv("CA_BUNDLE_NATIVE_EXEC", "1")

    with pytest.raises(BundleResolutionError) as unknown:
        resolve_and_register(
            store,
            rec["bundleHash"],
            signature_digest=rec["signatureDigest"],
            allowed_signers=[_public_key(SEED_B)],
            registry=Registry(),
        )
    assert _public_key(SEED_A) in str(unknown.value)

    with pytest.raises(BundleResolutionError, match="unsigned|signature"):
        resolve_and_register(
            store,
            rec["bundleHash"],
            signature_digest=None,
            allowed_signers=[_public_key(SEED_A)],
            registry=Registry(),
        )


def test_equal_hash_baked_collision_is_noop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, _deployment, rec = _published(tmp_path)
    manifest = _json_from_store(store, rec["bundleHash"])
    first_pure = manifest["pures"][0]
    source = store.get(first_pure["source"]).decode("utf-8")
    fresh = Registry()
    existing = fresh.register_pure_from_source(first_pure["name"], source)

    _resolve(store, rec, fresh, monkeypatch)

    assert fresh.pures[first_pure["name"]] is existing
    assert fresh.get_pure(first_pure["name"]) is existing.fn


def test_different_hash_collision_errors_with_operator_guidance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, _deployment, rec = _published(tmp_path)
    manifest = _json_from_store(store, rec["bundleHash"])
    pure_name = manifest["pures"][0]["name"]
    fresh = Registry()
    changed = f"""@pure("{pure_name}")\ndef changed(value):\n    return value\n"""
    fresh.register_pure_from_source(pure_name, changed)
    baked_hash = fresh.source_hash_of(pure_name)
    bundled_hash = manifest["pures"][0]["sourceHash"]

    with pytest.raises(BundleResolutionError) as excinfo:
        _resolve(store, rec, fresh, monkeypatch)

    message = str(excinfo.value)
    assert pure_name in message
    assert baked_hash in message
    assert bundled_hash in message
    assert rec["bundleHash"] in message
    assert "stale worker image" in message
    assert "stale bundle" in message


def test_dev_gate_blocks_without_env_and_explicit_grant_skips_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, _deployment, rec = _published(tmp_path)
    monkeypatch.delenv("CA_BUNDLE_NATIVE_EXEC", raising=False)
    fresh = Registry()

    with pytest.raises(BundleResolutionError) as excinfo:
        resolve_and_register(
            store,
            rec["bundleHash"],
            signature_digest=rec["signatureDigest"],
            allowed_signers=[_public_key(SEED_A)],
            registry=fresh,
        )

    message = str(excinfo.value)
    assert "CA_BUNDLE_NATIVE_EXEC" in message
    assert "wasm" in message
    assert fresh.pures == {}

    resolved = resolve_and_register(
        store,
        rec["bundleHash"],
        signature_digest=rec["signatureDigest"],
        allowed_signers=[_public_key(SEED_A)],
        require_native_grant=False,
        registry=fresh,
    )
    assert resolved["registered"]


def test_hand_built_manifest_rejects_std_pure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = LocalDirCAS(tmp_path)
    source_digest = store.put(b"@pure(\"std.bad\")\ndef bad(value):\n    return value\n")
    components = {
        "flowJson": arr("std.bad").to_json(),
        "manifestJson": {},
        "pureSourceHashes": {"std.bad": "pure:0123456789abcdef"},
        "brains": {},
        "capabilities": None,
        "executionPolicy": None,
        "frameworkVersion": "test",
    }
    components_digest = store.put(canonical_json(components).encode("utf-8"))
    manifest = {
        "artifactHash": f"sha256:{components_digest}",
        "artifactComponents": components_digest,
        "flow": store.put(canonical_json(arr("std.bad").to_json()).encode("utf-8")),
        "pures": [
            {
                "abi": ABI_PYTHON_SOURCE_JSON_V1,
                "name": "std.bad",
                "source": source_digest,
                "sourceHash": "pure:0123456789abcdef",
            }
        ],
        "signature": None,
    }
    bundle_hash = store.put(canonical_json(manifest).encode("utf-8"))
    signature_digest = _put_signature(store, bundle_hash, SEED_A)
    monkeypatch.setenv("CA_BUNDLE_NATIVE_EXEC", "1")

    with pytest.raises(BundleResolutionError, match="std.bad"):
        resolve_and_register(
            store,
            bundle_hash,
            signature_digest=signature_digest,
            allowed_signers=[_public_key(SEED_A)],
            registry=Registry(),
        )


def test_source_hash_mismatch_in_manifest_fails_before_registration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = LocalDirCAS(tmp_path)
    name = "bundle.worker.bad_source_hash.v1"
    source = f"""@pure("{name}")\ndef bad_source_hash(value):\n    return value\n"""
    source_digest = store.put(source.encode("utf-8"))
    components_digest = store.put(
        canonical_json(
            {
                "flowJson": arr(name).to_json(),
                "manifestJson": {},
                "pureSourceHashes": {name: "pure:0000000000000000"},
                "brains": {},
                "capabilities": None,
                "executionPolicy": None,
                "frameworkVersion": "test",
            }
        ).encode("utf-8")
    )
    bundle_hash = store.put(
        canonical_json(
            {
                "artifactHash": f"sha256:{components_digest}",
                "artifactComponents": components_digest,
                "flow": store.put(canonical_json(arr(name).to_json()).encode("utf-8")),
                "pures": [
                    {
                        "abi": ABI_PYTHON_SOURCE_JSON_V1,
                        "name": name,
                        "source": source_digest,
                        "sourceHash": "pure:0000000000000000",
                    }
                ],
                "signature": None,
            }
        ).encode("utf-8")
    )
    signature_digest = _put_signature(store, bundle_hash, SEED_A)
    monkeypatch.setenv("CA_BUNDLE_NATIVE_EXEC", "1")
    fresh = Registry()

    with pytest.raises(BundleResolutionError) as excinfo:
        resolve_and_register(
            store,
            bundle_hash,
            signature_digest=signature_digest,
            allowed_signers=[_public_key(SEED_A)],
            registry=fresh,
        )

    assert _text_hash(source) in str(excinfo.value)
    assert "pure:0000000000000000" in str(excinfo.value)
    assert fresh.pures == {}


def test_load_bundles_from_env_registers_idempotently(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _store, _deployment, rec = _published(tmp_path)
    fresh = Registry()
    monkeypatch.setenv("STORE_URL", f"file://{tmp_path}")
    monkeypatch.setenv("CA_BUNDLES", f"{rec['bundleHash']}:{rec['signatureDigest']}")
    monkeypatch.setenv("CA_BUNDLE_ALLOWED_SIGNERS", f" {_public_key(SEED_A)} ")
    monkeypatch.setenv("CA_BUNDLE_NATIVE_EXEC", "1")

    first = load_bundles_from_env(registry=fresh)
    second = load_bundles_from_env(registry=fresh)

    assert first == second
    assert set(first[0]["registered"]) == set(rec["pureRuntimeRefs"])


def test_load_bundles_from_env_noop_and_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fresh = Registry()

    monkeypatch.delenv("CA_BUNDLES", raising=False)
    assert load_bundles_from_env(registry=fresh) == []

    monkeypatch.setenv("CA_BUNDLES", "abc")
    monkeypatch.delenv("STORE_URL", raising=False)
    with pytest.raises(BundleResolutionError, match="STORE_URL"):
        load_bundles_from_env(registry=fresh)

    monkeypatch.setenv("STORE_URL", f"file://{tmp_path}")
    with pytest.raises(BundleResolutionError, match="<bundleHash>:<signatureDigest>"):
        load_bundles_from_env(registry=fresh)
