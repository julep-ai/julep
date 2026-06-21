from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pytest

from composable_agents import arr, deploy, pure, seq
from composable_agents.bundle import publish_bundle
from composable_agents.cas import LocalDirCAS
from composable_agents import deps
from composable_agents.deps import base_component_hash, env_hash, parse_pep723
from composable_agents.execution import env_builder
from composable_agents.ir import canonical_json
from composable_agents.registry import DEFAULT_REGISTRY, Registry
from conftest import read_snapshot


SEED = "33" * 32


@pure("deps.test.normalize.v1")
def _deps_test_normalize(value: dict[str, Any]) -> dict[str, Any]:
    return {"name": value["name"].strip()}


@pure("deps.test.wrap.v1")
def _deps_test_wrap(value: dict[str, Any]) -> dict[str, Any]:
    return {"wrapped": value}


def _json_from_store(store: LocalDirCAS, digest: str) -> dict[str, Any]:
    return json.loads(store.get(digest).decode("utf-8"))


def _pure_source(name: str, dep: str | None, *, empty_deps: bool = False) -> str:
    if dep is not None:
        block = (
            "# /// script\n"
            f"# dependencies = [\"{dep}\"]\n"
            "# requires-python = \">=3.11\"\n"
            "# ///\n"
        )
    elif empty_deps:
        block = (
            "# /// script\n"
            "# dependencies = []\n"
            "# requires-python = \">=3.11\"\n"
            "# ///\n"
        )
    else:
        block = ""
    return (
        f"{block}@pure(\"{name}\")\n"
        "def identity(value):\n"
        "    return value\n"
    )


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


def test_parse_pep723_no_block() -> None:
    assert parse_pep723("def f(value):\n    return value\n") == ((), None)


def test_parse_pep723_deps_and_requires_python() -> None:
    source = (
        "# /// script\n"
        "# dependencies = [\"zipp==3.20.0\", \"anyio>=4\", \"anyio>=4\"]\n"
        "# requires-python = \">=3.11\"\n"
        "# ///\n"
        "def f(value):\n"
        "    return value\n"
    )

    assert parse_pep723(source) == (("anyio>=4", "zipp==3.20.0"), ">=3.11")


def test_parse_pep723_sorts_deps_regardless_of_source_order() -> None:
    first = (
        "# /// script\n"
        "# dependencies = [\"b==1\", \"a==1\"]\n"
        "# ///\n"
    )
    second = (
        "# /// script\n"
        "# dependencies = [\"a==1\", \"b==1\"]\n"
        "# ///\n"
    )

    assert parse_pep723(first) == parse_pep723(second)


def test_parse_pep723_malformed_toml_errors() -> None:
    source = (
        "# /// script\n"
        "# dependencies = [\n"
        "# ///\n"
    )

    with pytest.raises(ValueError, match="TOML"):
        parse_pep723(source)


def test_parse_pep723_two_script_blocks_errors() -> None:
    source = (
        "# /// script\n"
        "# dependencies = []\n"
        "# ///\n"
        "# /// script\n"
        "# dependencies = []\n"
        "# ///\n"
    )

    with pytest.raises(ValueError, match="at most one"):
        parse_pep723(source)


def test_env_hash_is_stable_and_hex() -> None:
    base = "a" * 64
    first = env_hash(["z==1", "a==1", "z==1"], ">=3.11", base)
    second = env_hash(["a==1", "z==1"], ">=3.11", base)

    assert first == second
    assert re.fullmatch(r"[0-9a-f]{64}", first)


def test_env_hash_omitted_requires_python_is_host_independent() -> None:
    base = "a" * 64
    dep_list = ["regex==2024.11.6"]
    expected_payload = {
        "deps": list(deps._normalized_deps(dep_list)),  # noqa: SLF001
        "requiresPython": None,
        "baseComponent": deps._base_component_digest(base),  # noqa: SLF001
    }
    expected = hashlib.sha256(canonical_json(expected_payload).encode("utf-8")).hexdigest()

    assert deps._python_major_minor(None) is None  # noqa: SLF001
    assert env_hash(dep_list, None, base) == expected
    assert env_hash(dep_list, None, base) == env_hash(dep_list, None, base)
    assert env_hash(dep_list, None, base) != env_hash(dep_list, ">=3.11", base)


def test_no_dep_publish_keeps_existing_bytes_without_env_hash(tmp_path: Path) -> None:
    custom_store = LocalDirCAS(tmp_path / "custom")
    deployment = deploy(
        seq(arr("deps.test.normalize.v1"), arr("deps.test.wrap.v1")),
        read_snapshot(),
    )

    rec = deployment.publish(custom_store, signing_key=SEED)

    assert rec["publishedArtifactHash"] == deployment.artifact_hash_with_refs(
        rec["pureRuntimeRefs"]
    )
    for ref in rec["pureRuntimeRefs"].values():
        assert "envHash" not in ref

    manifest = _json_from_store(custom_store, rec["bundleHash"])
    assert custom_store.get(manifest["flow"]) == canonical_json(deployment.flow_json).encode(
        "utf-8"
    )
    assert custom_store.get(manifest["artifactComponents"]) == canonical_json(
        deployment.artifact_components
    ).encode("utf-8")
    manifest_bytes = canonical_json(manifest).encode("utf-8")
    assert rec["bundleHash"] == custom_store.put(manifest_bytes)

    std_deployment = deploy(arr("std.pluck", {"key": "name"}), read_snapshot())
    std_rec = std_deployment.publish(LocalDirCAS(tmp_path / "std"), signing_key=SEED)
    assert std_rec["pureRuntimeRefs"] == {}
    assert std_rec["publishedArtifactHash"] == std_deployment.artifact_hash


def test_dep_pin_changes_env_hash_and_published_artifact_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_synth_env_builder(monkeypatch, tmp_path)
    isolated_a = Registry()
    isolated_b = Registry()
    name = "deps.test.pin.v1"
    source_a = _pure_source(name, "regex==2024.1.1")
    source_b = _pure_source(name, "regex==2024.2.1")
    entry_a = isolated_a.register_pure_from_source(name, source_a)
    entry_b = isolated_b.register_pure_from_source(name, source_b)

    hash_a = env_hash(entry_a.deps, entry_a.requires_python, base_component_hash())
    hash_b = env_hash(entry_b.deps, entry_b.requires_python, base_component_hash())
    assert hash_a != hash_b

    previous = DEFAULT_REGISTRY.pures.pop(name, None)
    try:
        DEFAULT_REGISTRY.register_pure_from_source(name, source_a)
        deployment_a = deploy(arr(name), read_snapshot())
        rec_a = deployment_a.publish(LocalDirCAS(tmp_path / "a"), signing_key=SEED)

        DEFAULT_REGISTRY.pures.pop(name, None)
        DEFAULT_REGISTRY.register_pure_from_source(name, source_b)
        deployment_b = deploy(arr(name), read_snapshot())
        rec_b = deployment_b.publish(LocalDirCAS(tmp_path / "b"), signing_key=SEED)
    finally:
        DEFAULT_REGISTRY.pures.pop(name, None)
        if previous is not None:
            DEFAULT_REGISTRY.pures[name] = previous

    assert rec_a["pureRuntimeRefs"][name]["envHash"] == hash_a
    assert rec_b["pureRuntimeRefs"][name]["envHash"] == hash_b
    assert rec_a["publishedArtifactHash"] != rec_b["publishedArtifactHash"]


def test_empty_dependencies_list_does_not_emit_env_hash(tmp_path: Path) -> None:
    name = "deps.test.empty.v1"
    source = _pure_source(name, None, empty_deps=True)
    previous = DEFAULT_REGISTRY.pures.pop(name, None)
    try:
        DEFAULT_REGISTRY.register_pure_from_source(name, source)
        deployment = deploy(arr(name), read_snapshot())
        rec = publish_bundle(
            deployment,
            LocalDirCAS(tmp_path),
            signing_key=SEED,
            registry=DEFAULT_REGISTRY,
        )
    finally:
        DEFAULT_REGISTRY.pures.pop(name, None)
        if previous is not None:
            DEFAULT_REGISTRY.pures[name] = previous

    assert "envHash" not in rec["pureRuntimeRefs"][name]
