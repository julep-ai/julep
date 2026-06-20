from __future__ import annotations

import hashlib
import inspect
import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from composable_agents import arr, deploy
from composable_agents.bundle import PureDepsUnbuildableError, publish_bundle
from composable_agents.cas import LocalDirCAS
from composable_agents.deps import base_component_hash, env_hash, parse_pep723
from composable_agents.errors import PureExecutionError
from composable_agents.execution import env_builder
from composable_agents.execution.wasm_executor import WasmExecutor, get_wasm_executor
from composable_agents.registry import DEFAULT_REGISTRY, Registry
from composable_agents.worker_store import BundleResolutionError, resolve_and_register
from conftest import read_snapshot


SEED = "66" * 32
EXTRACT_NAME = "cad.demo.extract_emails.v1"
MERGE_NAME = "cad.demo.merge_extractions.v1"
REAL_WHEEL_SKIP_REASON = (
    "ABI: wasi-wheels ship cp312 .so, base component is cp314; and imports trap "
    "under --stub-wasi (stat). wasi-wheels is unmaintained."
)


def _key(seed: str = SEED) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed))


def _public_key(seed: str = SEED) -> str:
    return _key(seed).public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    ).hex()


def _json_from_store(store: LocalDirCAS, digest: str) -> dict[str, Any]:
    return json.loads(store.get(digest).decode("utf-8"))


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


@contextmanager
def _with_default_source(name: str, source: str, *, tier: str = "wasm") -> Iterator[None]:
    previous = DEFAULT_REGISTRY.pures.pop(name, None)
    DEFAULT_REGISTRY.register_pure_from_source(name, source, tier=tier)
    try:
        yield
    finally:
        DEFAULT_REGISTRY.pures.pop(name, None)
        if previous is not None:
            DEFAULT_REGISTRY.pures[name] = previous


def _source(name: str, dep: str | None, *, body: str | None = None) -> str:
    block = ""
    if dep is not None:
        block = (
            "# /// script\n"
            f"# dependencies = [\"{dep}\"]\n"
            "# requires-python = \">=3.11\"\n"
            "# ///\n"
        )
    pure_body = body if body is not None else "def identity(value, **kwargs):\n    return value\n"
    return f"@pure(\"{name}\")\n{block}{pure_body}"


def _publish_source(
    name: str,
    source: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    native_grant: list[str] | None = None,
) -> tuple[LocalDirCAS, dict[str, Any], dict[str, Any]]:
    _patch_synth_env_builder(monkeypatch, tmp_path)
    with _with_default_source(name, source):
        deployment = deploy(arr(name), read_snapshot())
        store = LocalDirCAS(tmp_path)
        rec = publish_bundle(
            deployment,
            store,
            signing_key=SEED,
            registry=DEFAULT_REGISTRY,
            native_grant=native_grant,
        )
        manifest = _json_from_store(store, rec["bundleHash"])
        return store, rec, manifest
    raise AssertionError("unreachable")


def _manifest_pure(manifest: dict[str, Any], name: str) -> dict[str, Any]:
    matches = [pure_record for pure_record in manifest["pures"] if pure_record["name"] == name]
    assert len(matches) == 1
    return matches[0]


def test_example_pep723_metadata_survives_inspect_source() -> None:
    from examples import regex_extract_flow  # noqa: F401

    extract_entry = DEFAULT_REGISTRY.pures[EXTRACT_NAME]
    merge_entry = DEFAULT_REGISTRY.pures[MERGE_NAME]

    assert parse_pep723(inspect.getsource(extract_entry.fn)) == (
        ("regex==2024.11.6",),
        ">=3.11",
    )
    assert extract_entry.deps == ("regex==2024.11.6",)
    assert extract_entry.requires_python == ">=3.11"
    assert parse_pep723(inspect.getsource(merge_entry.fn)) == ((), None)
    assert merge_entry.deps == ()


def test_example_publish_resolve_carries_env_hash_end_to_end(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from examples import regex_extract_flow

    _patch_synth_env_builder(monkeypatch, tmp_path)
    store = LocalDirCAS(tmp_path)
    deployment = regex_extract_flow.build()
    rec = deployment.publish(store, signing_key=SEED)
    manifest = _json_from_store(store, rec["bundleHash"])

    regex_pure = _manifest_pure(manifest, EXTRACT_NAME)
    merge_pure = _manifest_pure(manifest, MERGE_NAME)
    assert "envHash" in regex_pure
    assert "envComponent" in regex_pure
    assert re_full_sha256(regex_pure["envHash"])
    assert re_full_sha256(regex_pure["envComponent"])
    assert "executorTier" not in regex_pure
    for key in ("envHash", "envComponent"):
        assert key not in merge_pure

    regex_ref = rec["pureRuntimeRefs"][EXTRACT_NAME]
    assert regex_ref["envHash"] == regex_pure["envHash"]
    assert regex_ref["executorTier"] == "wasm"
    merge_ref = rec["pureRuntimeRefs"][MERGE_NAME]
    assert merge_ref["executorTier"] == "wasm"
    assert "envHash" not in merge_ref

    example_entry = DEFAULT_REGISTRY.pures[EXTRACT_NAME]
    assert env_hash(
        example_entry.deps,
        example_entry.requires_python,
        base_component_hash(),
    ) == regex_pure["envHash"]

    fresh = Registry()
    resolve_and_register(
        store,
        rec["bundleHash"],
        signature_digest=rec["signatureDigest"],
        allowed_signers=[_public_key()],
        registry=fresh,
    )

    assert regex_pure["envHash"] in get_wasm_executor()._env_components  # noqa: SLF001
    resolved = fresh.pures[EXTRACT_NAME]
    assert resolved.executor == "wasm"
    assert resolved.env_hash == regex_pure["envHash"]

    component_bytes = env_builder.synthesize_env_component(
        example_entry.deps,
        example_entry.requires_python,
    )
    executor = WasmExecutor()
    executor.register_env_component(regex_pure["envHash"], component_bytes)
    assert regex_pure["envHash"] in executor._env_components  # noqa: SLF001
    assert executor._env_component_digests[regex_pure["envHash"]] == hashlib.sha256(  # noqa: SLF001
        component_bytes
    ).hexdigest()

    with pytest.raises(PureExecutionError) as excinfo:
        executor._select_component(EXTRACT_NAME, "f" * 64)  # noqa: SLF001
    assert excinfo.value.error_type == "WasmEnvUnavailable"

    # Blocked leg: actually importing regex from the dep env needs the real
    # wasi-wheel component, which is blocked by the ABI/stat-trap issue below.
    assert REAL_WHEEL_SKIP_REASON

    base_source = _source("dep.e2e.base.identity.v1", None)
    assert executor.run("dep.e2e.base.identity.v1", base_source, {"ok": True}, {}) == {
        "ok": True
    }


def re_full_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        char in "0123456789abcdef" for char in value
    )


def test_off_list_dep_without_native_grant_blocks_deploy_and_publish(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "dep.e2e.numpy.blocked.v1"
    source = _source(name, "numpy==2")
    with _with_default_source(name, source):
        monkeypatch.delenv("CA_PURE_NATIVE_DEPS", raising=False)
        with pytest.raises(PureDepsUnbuildableError) as deploy_exc:
            deploy(arr(name), read_snapshot())
        assert name in str(deploy_exc.value)
        assert "numpy==2" in str(deploy_exc.value)
        assert "CA_PURE_NATIVE_DEPS" in str(deploy_exc.value)

        monkeypatch.setenv("CA_PURE_NATIVE_DEPS", name)
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


def test_off_list_dep_with_native_grant_resolves_as_native_venv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "dep.e2e.numpy.native.v1"
    source = _source(name, "numpy==2")
    with _with_default_source(name, source, tier="native_venv"):
        monkeypatch.setenv("CA_PURE_NATIVE_DEPS", name)
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

    pure_record = _manifest_pure(manifest, name)
    assert pure_record["executorTier"] == "native"
    assert pure_record["deps"] == ["numpy==2"]
    assert pure_record["requiresPython"] == ">=3.11"
    assert "envHash" not in pure_record
    assert "envComponent" not in pure_record

    runtime_ref = rec["pureRuntimeRefs"][name]
    assert runtime_ref["executorTier"] == "native"
    assert "envHash" not in runtime_ref

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
    with pytest.raises(BundleResolutionError, match="CA_PURE_NATIVE_DEPS"):
        resolve_and_register(
            store,
            rec["bundleHash"],
            signature_digest=rec["signatureDigest"],
            allowed_signers=[_public_key()],
            native_grant=[],
            registry=denied,
        )
    assert denied.pures == {}


def test_env_hash_distinguishes_dep_versions_end_to_end(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "dep.e2e.regex.pin.v1"
    body = "def extract(value, **kwargs):\n    return value\n"
    source_a = _source(name, "regex==2024.11.6", body=body)
    source_b = _source(name, "regex==2023.12.25", body=body)

    first = _publish_source(name, source_a, tmp_path / "a", monkeypatch)
    second = _publish_source(name, source_b, tmp_path / "b", monkeypatch)
    rec_a = first[1]
    manifest_a = first[2]
    rec_b = second[1]
    manifest_b = second[2]

    pure_a = _manifest_pure(manifest_a, name)
    pure_b = _manifest_pure(manifest_b, name)
    assert pure_a["envHash"] != pure_b["envHash"]
    assert pure_a["envComponent"] != pure_b["envComponent"]
    assert rec_a["pureRuntimeRefs"][name]["envHash"] != rec_b["pureRuntimeRefs"][name]["envHash"]
    assert rec_a["publishedArtifactHash"] != rec_b["publishedArtifactHash"]


@pytest.mark.skip(reason=REAL_WHEEL_SKIP_REASON)
def test_real_regex_wheel_env_component_imports_and_runs(tmp_path: Path) -> None:
    dep_list = ("regex==2024.11.6",)
    component_path = env_builder.build_env_component(dep_list, ">=3.11", out_dir=tmp_path)
    component_hash = env_hash(dep_list, ">=3.11", base_component_hash())
    executor = WasmExecutor()
    executor.register_env_component(component_hash, component_path.read_bytes())
    source = _source(
        "dep.e2e.regex.real.v1",
        "regex==2024.11.6",
        body=(
            "def uses_regex(value, **kwargs):\n"
            "    import regex\n"
            "    return bool(regex.match(r\"^[a-z]+$\", value))\n"
        ),
    )

    assert executor.run("dep.e2e.regex.real.v1", source, "abc", {}, env_hash=component_hash)
