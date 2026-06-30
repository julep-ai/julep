from __future__ import annotations

import json
import hashlib
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("cryptography")
pytest.importorskip("wasmtime")

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from composable_agents import arr, deploy
from composable_agents.bundle import ABI_PYTHON_SOURCE_JSON_V1, BundleError
from composable_agents.cas import LocalDirCAS
from composable_agents.deps import base_component_hash, env_hash
from composable_agents.errors import PureExecutionError
from composable_agents.execution import env_builder
from composable_agents.execution.wasm_executor import WasmExecutor, get_wasm_executor
from composable_agents.ir import canonical_json
from composable_agents.registry import DEFAULT_REGISTRY, Registry
from composable_agents.worker_store import BundleResolutionError, resolve_and_register
from conftest import read_snapshot


SEED = "44" * 32


def _key(seed: str) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed))


def _public_key(seed: str) -> str:
    return _key(seed).public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    ).hex()


def _json_from_store(store: LocalDirCAS, digest: str) -> dict[str, Any]:
    return json.loads(store.get(digest).decode("utf-8"))


def _put_signature(store: LocalDirCAS, bundle_hash: str, seed: str = SEED) -> str:
    manifest_bytes = store.get(bundle_hash)
    signature = {
        "algo": "ed25519",
        "bundleHash": bundle_hash,
        "publicKey": _public_key(seed),
        "sig": _key(seed).sign(manifest_bytes).hex(),
    }
    return store.put(canonical_json(signature).encode("utf-8"))


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
def _with_default_source(name: str, source: str):
    previous = DEFAULT_REGISTRY.pures.pop(name, None)
    DEFAULT_REGISTRY.register_pure_from_source(name, source)
    try:
        yield
    finally:
        DEFAULT_REGISTRY.pures.pop(name, None)
        if previous is not None:
            DEFAULT_REGISTRY.pures[name] = previous


def _patch_synth_env_builder(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> list[str]:
    built: list[str] = []

    def fake_build_env_component(
        dep_list: tuple[str, ...],
        requires_python: str | None,
        *,
        out_dir: str | Path | None = None,
    ) -> Path:
        component_hash = env_hash(dep_list, requires_python, base_component_hash())
        built.append(component_hash)
        root = Path(out_dir) if out_dir is not None else tmp_path / "env-components"
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"env_{component_hash}.wasm"
        path.write_bytes(env_builder.synthesize_env_component(dep_list, requires_python))
        return path

    monkeypatch.setattr(env_builder, "build_env_component", fake_build_env_component)
    return built


def _publish_source(
    name: str,
    source: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[LocalDirCAS, Any, dict[str, Any], dict[str, Any]]:
    _patch_synth_env_builder(monkeypatch, tmp_path)
    with _with_default_source(name, source):
        store = LocalDirCAS(tmp_path / name.replace(".", "_"))
        deployment = deploy(arr(name), read_snapshot())
        rec = deployment.publish(store, signing_key=SEED)
        manifest = _json_from_store(store, rec["bundleHash"])
        return store, deployment, rec, manifest
    raise AssertionError("unreachable")


def test_executor_selects_registered_env_component_by_env_hash() -> None:
    dep_list = ("regex==1",)
    component_hash = env_hash(dep_list, ">=3.11", base_component_hash())
    component_bytes = env_builder.synthesize_env_component(dep_list, ">=3.11")
    executor = WasmExecutor()
    source = _source("env.cache.double.v1", "regex==1")

    executor.register_env_component(component_hash, component_bytes)

    assert executor.run("env.cache.double.v1", source, 21, {}, env_hash=component_hash) == 21
    assert executor._env_component_digests[component_hash] == hashlib.sha256(  # noqa: SLF001
        component_bytes
    ).hexdigest()


def test_executor_env_hash_none_uses_base_component() -> None:
    executor = WasmExecutor()
    source = _source("env.cache.base.v1", None)

    assert executor.run("env.cache.base.v1", source, {"ok": True}, {}) == {"ok": True}
    assert executor.run("env.cache.base.v1", source, {"ok": True}, {}, env_hash=None) == {
        "ok": True
    }


def test_executor_unknown_env_hash_fails_closed() -> None:
    executor = WasmExecutor()
    source = _source("env.cache.missing.v1", "regex==1")

    with pytest.raises(PureExecutionError) as excinfo:
        executor.run("env.cache.missing.v1", source, None, {}, env_hash="f" * 64)

    assert excinfo.value.error_type == "WasmEnvUnavailable"
    assert "env.cache.missing.v1" in excinfo.value.message
    assert "f" * 64 in excinfo.value.message


def test_resolve_missing_env_component_fails_without_registering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "env.cache.resolve_missing.v1"
    store, _deployment, rec, manifest = _publish_source(
        name,
        _source(name, "regex==1"),
        tmp_path,
        monkeypatch,
    )
    manifest["pures"][0]["envComponent"] = "a" * 64
    bundle_hash = store.put(canonical_json(manifest).encode("utf-8"))
    signature_digest = _put_signature(store, bundle_hash)
    fresh = Registry()

    with pytest.raises(BundleResolutionError, match="env component"):
        resolve_and_register(
            store,
            bundle_hash,
            signature_digest=signature_digest,
            allowed_signers=[_public_key(SEED)],
            registry=fresh,
        )

    assert fresh.pures == {}
    assert rec["bundleHash"] != bundle_hash


def test_worker_env_cache_wiring_publish_resolve_and_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "env.cache.worker.v1"
    store, _deployment, rec, manifest = _publish_source(
        name,
        _source(name, "regex==1"),
        tmp_path,
        monkeypatch,
    )
    pure_record = manifest["pures"][0]
    fresh = Registry()

    resolve_and_register(
        store,
        rec["bundleHash"],
        signature_digest=rec["signatureDigest"],
        allowed_signers=[_public_key(SEED)],
        registry=fresh,
    )

    assert "envHash" in pure_record
    assert "envComponent" in pure_record
    assert rec["pureRuntimeRefs"][name]["envHash"] == pure_record["envHash"]
    entry = fresh.pures[name]
    assert entry.executor == "wasm"
    assert entry.env_hash == pure_record["envHash"]
    assert env_hash(entry.deps, entry.requires_python, base_component_hash()) == pure_record[
        "envHash"
    ]
    assert pure_record["envHash"] in get_wasm_executor()._env_components  # noqa: SLF001
    assert fresh.get_pure(name)({"value": 7}) == {"value": 7}


def test_env_hash_dep_version_changes_env_component_and_published_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "env.cache.pin.v1"
    first = _publish_source(name, _source(name, "regex==1"), tmp_path / "a", monkeypatch)
    second = _publish_source(name, _source(name, "regex==2"), tmp_path / "b", monkeypatch)
    rec_a = first[2]
    manifest_a = first[3]
    rec_b = second[2]
    manifest_b = second[3]

    pure_a = manifest_a["pures"][0]
    pure_b = manifest_b["pures"][0]
    assert pure_a["envHash"] != pure_b["envHash"]
    assert pure_a["envComponent"] != pure_b["envComponent"]
    assert rec_a["pureRuntimeRefs"][name]["envHash"] != rec_b["pureRuntimeRefs"][name]["envHash"]
    assert rec_a["publishedArtifactHash"] != rec_b["publishedArtifactHash"]


def test_no_dep_manifest_has_no_env_fields_and_old_shape_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "env.cache.no_dep.v1"
    store, deployment, rec, manifest = _publish_source(name, _source(name, None), tmp_path, monkeypatch)

    assert all("envHash" not in pure_record for pure_record in manifest["pures"])
    assert all("envComponent" not in pure_record for pure_record in manifest["pures"])
    old_shape_manifest = {
        "artifactHash": deployment.artifact_hash,
        "artifactComponents": deployment.artifact_hash.removeprefix("sha256:"),
        "flow": manifest["flow"],
        "pures": [
            {
                "abi": ABI_PYTHON_SOURCE_JSON_V1,
                "name": pure_record["name"],
                "source": pure_record["source"],
                "sourceHash": pure_record["sourceHash"],
            }
            for pure_record in manifest["pures"]
        ],
        "signature": None,
    }
    assert store.get(rec["bundleHash"]) == canonical_json(old_shape_manifest).encode("utf-8")
    refs_without_env = {
        pure_record["name"]: {
            "sourceHash": pure_record["sourceHash"],
            "abi": ABI_PYTHON_SOURCE_JSON_V1,
            "bundleHash": rec["bundleHash"],
            "executorTier": "wasm",
        }
        for pure_record in manifest["pures"]
    }
    assert rec["publishedArtifactHash"] == deployment.artifact_hash_with_refs(refs_without_env)


def test_off_list_dep_publish_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    name = "env.cache.numpy.v1"
    _patch_synth_env_builder(monkeypatch, tmp_path)
    with _with_default_source(name, _source(name, "numpy==2")):
        monkeypatch.setenv("CA_PURE_NATIVE_DEPS", name)
        deployment = deploy(arr(name), read_snapshot())
        monkeypatch.delenv("CA_PURE_NATIVE_DEPS", raising=False)
        with pytest.raises(BundleError, match="off the curated WASI wheel list"):
            deployment.publish(LocalDirCAS(tmp_path), signing_key=SEED)


@pytest.mark.skipif(
    shutil.which("componentize-py") is None,
    reason="real env-component build requires the componentize-py toolchain on PATH",
)
def test_real_regex_wheel_env_component_imports_and_runs(tmp_path: Path) -> None:
    dep_list = ("regex==2024.11.6",)
    component_path = env_builder.build_env_component(dep_list, ">=3.11", out_dir=tmp_path)
    component_hash = env_hash(dep_list, ">=3.11", base_component_hash())
    executor = WasmExecutor()
    executor.register_env_component(component_hash, component_path.read_bytes())
    source = (
        "# /// script\n"
        "# dependencies = [\"regex==2024.11.6\"]\n"
        "# requires-python = \">=3.11\"\n"
        "# ///\n"
        "@pure(\"env.cache.regex.real.v1\")\n"
        "def uses_regex(value, **kwargs):\n"
        "    import regex\n"
        "    return bool(regex.match(r\"^[a-z]+$\", value))\n"
    )

    assert executor.run("env.cache.regex.real.v1", source, "abc", {}, env_hash=component_hash)
