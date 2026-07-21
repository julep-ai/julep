from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("cryptography")

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from julep import arr, deploy
from julep.bundle import PureDepsUnbuildableError, publish_bundle
from julep.cas import LocalDirCAS
from julep.deps import base_component_hash, env_hash
from julep.execution import env_builder
from julep.registry import DEFAULT_REGISTRY, Registry
from julep.worker_store import BundleResolutionError, resolve_and_register
from conftest import read_snapshot


SEED = "55" * 32


def _key(seed: str = SEED) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed))


def _public_key(seed: str = SEED) -> str:
    return _key(seed).public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    ).hex()


def _json_from_store(store: LocalDirCAS, digest: str) -> dict[str, Any]:
    return json.loads(store.get(digest).decode("utf-8"))


def _source(name: str, dep: str | None) -> str:
    block = ""
    if dep is not None:
        block = (
            "# /// script\n"
            f"# dependencies = [\"{dep}\"]\n"
            "# requires-python = \">=3.11\"\n"
            "# ///\n"
        )
    return (
        f"{block}@pure(\"{name}\")\n"
        "def identity(value, **kwargs):\n"
        "    return value\n"
    )


@contextmanager
def _with_default_source(name: str, source: str, *, tier: str = "wasm"):
    previous = DEFAULT_REGISTRY.pures.pop(name, None)
    DEFAULT_REGISTRY.register_pure_from_source(name, source, tier=tier)
    try:
        yield
    finally:
        DEFAULT_REGISTRY.pures.pop(name, None)
        if previous is not None:
            DEFAULT_REGISTRY.pures[name] = previous


def _patch_synth_env_builder(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_build_env_component(
        dep_list: tuple[str, ...],
        requires_python: str | None,
        *,
        out_dir: str | Path | None = None,
    ) -> Path:
        component_hash = env_hash(dep_list, requires_python, base_component_hash())
        root = Path(out_dir) if out_dir is not None else tmp_path / "env-components"
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"env_{component_hash}.wasm"
        path.write_bytes(env_builder.synthesize_env_component(dep_list, requires_python))
        return path

    monkeypatch.setattr(env_builder, "build_env_component", fake_build_env_component)


def _publish_native_bundle(
    name: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[LocalDirCAS, dict[str, Any], dict[str, Any]]:
    source = _source(name, "numpy==2")
    with _with_default_source(name, source):
        monkeypatch.setenv("JULEP_PURE_NATIVE_DEPS", name)
        deployment = deploy(arr(name), read_snapshot())
        store = LocalDirCAS(tmp_path)
        rec = publish_bundle(
            deployment,
            store,
            signing_key=SEED,
            registry=DEFAULT_REGISTRY,
            native_grant=[name],
        )
        manifest = _json_from_store(store, rec["bundleHash"])
        return store, rec, manifest
    raise AssertionError("unreachable")


def test_off_list_dep_without_grant_blocks_deploy_and_publish(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "native.grant.numpy.blocked.v1"
    source = _source(name, "numpy==2")
    with _with_default_source(name, source):
        monkeypatch.delenv("JULEP_PURE_NATIVE_DEPS", raising=False)
        with pytest.raises(PureDepsUnbuildableError) as deploy_exc:
            deploy(arr(name), read_snapshot())
        assert name in str(deploy_exc.value)
        assert "numpy==2" in str(deploy_exc.value)
        assert "JULEP_PURE_NATIVE_DEPS" in str(deploy_exc.value)

        monkeypatch.setenv("JULEP_PURE_NATIVE_DEPS", name)
        deployment = deploy(arr(name), read_snapshot())
        with pytest.raises(PureDepsUnbuildableError) as publish_exc:
            publish_bundle(
                deployment,
                LocalDirCAS(tmp_path),
                signing_key=SEED,
                registry=DEFAULT_REGISTRY,
                native_grant=[],
            )
        assert name in str(publish_exc.value)
        assert "numpy==2" in str(publish_exc.value)
        assert "off the curated WASI wheel list" in str(publish_exc.value)


def test_granted_native_venv_source_routes_to_native_wrapper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "native.grant.route.v1"
    source = _source(name, "numpy==2")
    with _with_default_source(name, source, tier="native_venv"):
        monkeypatch.setenv("JULEP_PURE_NATIVE_DEPS", name)
        deploy(arr(name), read_snapshot())

        entry = DEFAULT_REGISTRY.pures[name]
        resolved = DEFAULT_REGISTRY.get_pure(name)
        assert entry.executor == "native_venv"
        assert resolved is not entry.fn
        assert callable(resolved)


def test_supported_dep_stays_wasm_without_grant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "native.grant.regex.v1"
    _patch_synth_env_builder(monkeypatch, tmp_path)
    with _with_default_source(name, _source(name, "regex==1")):
        monkeypatch.delenv("JULEP_PURE_NATIVE_DEPS", raising=False)
        deployment = deploy(arr(name), read_snapshot())
        rec = deployment.publish(LocalDirCAS(tmp_path), signing_key=SEED)
        manifest = _json_from_store(LocalDirCAS(tmp_path), rec["bundleHash"])

    pure_record = manifest["pures"][0]
    assert DEFAULT_REGISTRY.pures.get(name) is None
    assert "envHash" in pure_record
    assert "envComponent" in pure_record
    assert "executorTier" not in pure_record
    assert rec["pureRuntimeRefs"][name]["executorTier"] == "wasm"


def test_no_dep_pure_does_not_emit_new_fields(tmp_path: Path) -> None:
    name = "native.grant.no_dep.v1"
    with _with_default_source(name, _source(name, None)):
        deployment = deploy(arr(name), read_snapshot())
        rec = deployment.publish(LocalDirCAS(tmp_path), signing_key=SEED)
        manifest = _json_from_store(LocalDirCAS(tmp_path), rec["bundleHash"])

    pure_record = manifest["pures"][0]
    runtime_ref = rec["pureRuntimeRefs"][name]
    for key in ("executorTier", "deps", "requiresPython", "envHash", "envComponent"):
        assert key not in pure_record
    assert runtime_ref == {
        "sourceHash": pure_record["sourceHash"],
        "abi": pure_record["abi"],
        "bundleHash": rec["bundleHash"],
        "executorTier": "wasm",
    }


def test_worker_resolution_requires_native_grant_and_registers_native_venv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "native.grant.worker.v1"
    store, rec, _manifest = _publish_native_bundle(name, tmp_path, monkeypatch)

    fresh = Registry()
    resolve_and_register(
        store,
        rec["bundleHash"],
        signature_digest=rec["signatureDigest"],
        allowed_signers=[_public_key()],
        native_grant=[name],
        registry=fresh,
    )
    entry = fresh.pures[name]
    assert entry.executor == "native_venv"
    assert entry.deps == ("numpy==2",)
    assert entry.requires_python == ">=3.11"

    denied = Registry()
    with pytest.raises(BundleResolutionError, match="JULEP_PURE_NATIVE_DEPS"):
        resolve_and_register(
            store,
            rec["bundleHash"],
            signature_digest=rec["signatureDigest"],
            allowed_signers=[_public_key()],
            native_grant=[],
            registry=denied,
        )
    assert denied.pures == {}


def test_native_granted_publish_manifest_and_runtime_ref_shape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "native.grant.publish.v1"
    _store, rec, manifest = _publish_native_bundle(name, tmp_path, monkeypatch)

    pure_record = manifest["pures"][0]
    assert pure_record["executorTier"] == "native"
    assert pure_record["deps"] == ["numpy==2"]
    assert pure_record["requiresPython"] == ">=3.11"
    assert "envHash" not in pure_record
    assert "envComponent" not in pure_record

    runtime_ref = rec["pureRuntimeRefs"][name]
    assert runtime_ref["executorTier"] == "native"
    assert "envHash" not in runtime_ref
