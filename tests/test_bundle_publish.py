from __future__ import annotations

import inspect
import json
import re
from pathlib import Path
from typing import Any

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from composable_agents import arr, deploy, pure, seq
from composable_agents.bundle import ABI_PYTHON_SOURCE_JSON_V1, BundleError, publish_bundle
from composable_agents.cas import LocalDirCAS
from composable_agents.ir import canonical_json
from composable_agents.registry import PureEntry, Registry
from conftest import read_snapshot


SEED_A = "11" * 32
SEED_B = "22" * 32


@pure("bundle.test.normalize.v1")
def _bundle_test_normalize(value: dict[str, Any]) -> dict[str, Any]:
    return {"name": value["name"].strip(), "score": int(value["score"])}


@pure("bundle.test.summarize.v1")
def _bundle_test_summarize(value: dict[str, Any]) -> dict[str, Any]:
    return {"summary": f"{value['name']}:{value['score'] + 1}"}


@pure("bundle.test.with_std.v1")
def _bundle_test_with_std(value: dict[str, Any]) -> dict[str, Any]:
    return {"wrapped": value}


def _public_key(seed: str) -> str:
    key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed))
    return key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    ).hex()


def _json_from_store(store: LocalDirCAS, digest: str) -> dict[str, Any]:
    return json.loads(store.get(digest).decode("utf-8"))


def _simple_deployment():
    return deploy(
        seq(arr("bundle.test.normalize.v1"), arr("bundle.test.summarize.v1")),
        read_snapshot(),
    )


def test_publish_record_shape_and_stored_manifest(tmp_path: Path) -> None:
    store = LocalDirCAS(tmp_path)
    deployment = _simple_deployment()

    rec = deployment.publish(store, signing_key=SEED_A)

    assert re.fullmatch(r"[0-9a-f]{64}", rec["bundleHash"])
    assert re.fullmatch(r"[0-9a-f]{64}", rec["signatureDigest"])
    assert rec["publishedArtifactHash"] == deployment.artifact_hash_with_refs(
        rec["pureRuntimeRefs"]
    )
    assert rec["publishedArtifactHash"] != deployment.artifact_hash

    manifest = _json_from_store(store, rec["bundleHash"])
    assert manifest["artifactHash"] == deployment.artifact_hash
    assert manifest["artifactComponents"] == deployment.artifact_hash.removeprefix("sha256:")
    assert manifest["signature"] is None
    assert [p["name"] for p in manifest["pures"]] == sorted(
        deployment.artifact_components["pureSourceHashes"]
    )

    for pure_record in manifest["pures"]:
        name = pure_record["name"]
        ref = rec["pureRuntimeRefs"][name]
        assert pure_record["abi"] == ABI_PYTHON_SOURCE_JSON_V1
        assert pure_record["sourceHash"] == deployment.artifact_components["pureSourceHashes"][name]
        assert ref == {
            "sourceHash": pure_record["sourceHash"],
            "abi": ABI_PYTHON_SOURCE_JSON_V1,
            "bundleHash": rec["bundleHash"],
            "executorTier": "native",
        }

    signature = _json_from_store(store, rec["signatureDigest"])
    assert signature["algo"] == "ed25519"
    assert signature["bundleHash"] == rec["bundleHash"]
    assert signature["publicKey"] == _public_key(SEED_A)
    assert re.fullmatch(r"[0-9a-f]{128}", signature["sig"])


def test_bundle_hash_is_signer_independent(tmp_path: Path) -> None:
    deployment = _simple_deployment()
    first = deployment.publish(LocalDirCAS(tmp_path / "a"), signing_key=SEED_A)
    second = deployment.publish(LocalDirCAS(tmp_path / "b"), signing_key=SEED_B)

    assert first["bundleHash"] == second["bundleHash"]
    assert first["signatureDigest"] != second["signatureDigest"]


def test_empty_custom_set_publishes_with_empty_refs(tmp_path: Path) -> None:
    deployment = deploy(arr("std.pluck", {"key": "name"}), read_snapshot())
    rec = deployment.publish(LocalDirCAS(tmp_path), signing_key=SEED_A)

    assert rec["pureRuntimeRefs"] == {}
    assert rec["publishedArtifactHash"] == deployment.artifact_hash

    manifest = _json_from_store(LocalDirCAS(tmp_path), rec["bundleHash"])
    assert manifest["pures"] == []


def test_std_pures_are_excluded_when_custom_pures_are_bundled(tmp_path: Path) -> None:
    deployment = deploy(
        seq(arr("std.pluck", {"key": "payload"}), arr("bundle.test.with_std.v1")),
        read_snapshot(),
    )
    rec = deployment.publish(LocalDirCAS(tmp_path), signing_key=SEED_A)
    manifest = _json_from_store(LocalDirCAS(tmp_path), rec["bundleHash"])

    assert [p["name"] for p in manifest["pures"]] == ["bundle.test.with_std.v1"]
    assert set(rec["pureRuntimeRefs"]) == {"bundle.test.with_std.v1"}


def test_signing_key_can_come_from_env_or_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    deployment = _simple_deployment()

    monkeypatch.setenv("CA_BUNDLE_SIGNING_KEY", SEED_A)
    from_env = deployment.publish(LocalDirCAS(tmp_path / "env"))
    assert _json_from_store(LocalDirCAS(tmp_path / "env"), from_env["signatureDigest"])[
        "publicKey"
    ] == _public_key(SEED_A)

    key_file = tmp_path / "seed.txt"
    key_file.write_text(f"  {SEED_B}\n", encoding="utf-8")
    monkeypatch.setenv("CA_BUNDLE_SIGNING_KEY", str(key_file))
    from_file = deployment.publish(LocalDirCAS(tmp_path / "file"))
    assert _json_from_store(LocalDirCAS(tmp_path / "file"), from_file["signatureDigest"])[
        "publicKey"
    ] == _public_key(SEED_B)


def test_missing_signing_key_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CA_BUNDLE_SIGNING_KEY", raising=False)

    with pytest.raises(BundleError, match="CA_BUNDLE_SIGNING_KEY"):
        _simple_deployment().publish(LocalDirCAS(tmp_path))


def test_missing_registry_source_errors(tmp_path: Path) -> None:
    deployment = _simple_deployment()

    with pytest.raises(BundleError) as excinfo:
        publish_bundle(deployment, LocalDirCAS(tmp_path), signing_key=SEED_A, registry=Registry())

    message = str(excinfo.value)
    assert "bundle.test.normalize.v1" in message
    assert "registered before publish" in message


def test_drifted_registry_source_errors(tmp_path: Path) -> None:
    deployment = _simple_deployment()
    registry = Registry()
    registry.register_pure_from_source(
        "bundle.test.normalize.v1",
        """@pure("bundle.test.normalize.v1")\ndef changed(value):\n    return value\n""",
    )
    registry.register_pure_from_source(
        "bundle.test.summarize.v1",
        inspect.getsource(_bundle_test_summarize.fn),
    )

    with pytest.raises(BundleError) as excinfo:
        publish_bundle(deployment, LocalDirCAS(tmp_path), signing_key=SEED_A, registry=registry)

    message = str(excinfo.value)
    assert "bundle.test.normalize.v1" in message
    assert deployment.artifact_components["pureSourceHashes"]["bundle.test.normalize.v1"] in message
    assert registry.source_hash_of("bundle.test.normalize.v1") in message


def test_noninspectable_registry_source_errors(tmp_path: Path) -> None:
    deployment = _simple_deployment()
    registry = Registry()
    source = """@pure("bundle.test.normalize.v1")\ndef dynamic(value):\n    return value\n"""
    captured: dict[str, Any] = {}

    def pure_for_exec(name: str):
        def deco(fn):
            captured[name] = fn
            return fn

        return deco

    exec(source, {"pure": pure_for_exec})
    registry.pures["bundle.test.normalize.v1"] = PureEntry(
        "bundle.test.normalize.v1",
        captured["bundle.test.normalize.v1"],
        deployment.artifact_components["pureSourceHashes"]["bundle.test.normalize.v1"],
    )
    registry.register_pure_from_source(
        "bundle.test.summarize.v1",
        inspect.getsource(_bundle_test_summarize.fn),
    )

    with pytest.raises(BundleError, match="not inspectable"):
        publish_bundle(deployment, LocalDirCAS(tmp_path), signing_key=SEED_A, registry=registry)


def test_inspected_source_must_match_registry_hash(tmp_path: Path) -> None:
    deployment = _simple_deployment()
    registry = Registry()

    def fake(value: dict[str, Any]) -> dict[str, Any]:
        return value

    registry.pures["bundle.test.normalize.v1"] = PureEntry(
        "bundle.test.normalize.v1",
        fake,
        deployment.artifact_components["pureSourceHashes"]["bundle.test.normalize.v1"],
    )
    registry.register_pure_from_source(
        "bundle.test.summarize.v1",
        inspect.getsource(_bundle_test_summarize.fn),
    )

    with pytest.raises(BundleError) as excinfo:
        publish_bundle(deployment, LocalDirCAS(tmp_path), signing_key=SEED_A, registry=registry)

    message = str(excinfo.value)
    assert "source hash mismatch" in message
    assert "bundle.test.normalize.v1" in message


def test_stored_manifest_hashes_unsigned_canonical_bytes(tmp_path: Path) -> None:
    store = LocalDirCAS(tmp_path)
    rec = _simple_deployment().publish(store, signing_key=SEED_A)

    manifest = _json_from_store(store, rec["bundleHash"])

    assert manifest["signature"] is None
    assert rec["bundleHash"] == store.put(canonical_json(manifest).encode("utf-8"))
