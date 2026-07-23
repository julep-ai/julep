"""pureRuntimeRefs artifact identity tests."""

from __future__ import annotations

import julep
from julep import arr, call, deploy, mcp, seq
from julep import purity
from julep.ir import canonical_json
from julep.purity import PureEntry
from conftest import read_snapshot


def _pure_runtime_ref_fn(value):
    return value


def _deployment(monkeypatch):
    monkeypatch.setitem(
        purity._REGISTRY,
        "runtime.ref.identity",
        PureEntry("runtime.ref.identity", _pure_runtime_ref_fn, "pure:stable"),
    )
    monkeypatch.setattr(julep, "__version__", "runtime-ref-test-version")
    return deploy(seq(arr("runtime.ref.identity"), call(mcp("srv", "a"))), read_snapshot("a"))


def _runtime_refs(
    *,
    bundle_hash: str = "a" * 64,
    executor_tier: str = "native",
    env_hash: str | None = None,
) -> dict[str, dict[str, str]]:
    ref = {
        "sourceHash": "pure:0123456789abcdef",
        "abi": "python-source/json-v1",
        "bundleHash": bundle_hash,
        "executorTier": executor_tier,
    }
    if env_hash is not None:
        ref["envHash"] = env_hash
    return {"runtime.ref.identity": ref}


def test_pure_runtime_refs_absent_and_empty_are_base_identity(monkeypatch):
    deployment = _deployment(monkeypatch)

    absent = deployment.artifact_components_with_refs(None)
    empty = deployment.artifact_components_with_refs({})

    assert canonical_json(absent) == canonical_json(deployment.artifact_components)
    assert canonical_json(empty) == canonical_json(deployment.artifact_components)
    assert "pureRuntimeRefs" not in absent
    assert "pureRuntimeRefs" not in empty
    assert "pureRuntimeRefs" not in deployment.artifact_components
    assert deployment.artifact_hash_with_refs(None) == deployment.artifact_hash
    assert deployment.artifact_hash_with_refs({}) == deployment.artifact_hash


def test_refs_absent_artifact_hash_regression_pin(monkeypatch):
    deployment = _deployment(monkeypatch)

    # Guards refs-absent identity across the pureRuntimeRefs join change.
    assert deployment.artifact_hash == (
        "sha256:152a4af8d608b2d37809cc397a5119c3593147dc8af4476c6a7ffa8fd45f5542"
    )


def test_pure_runtime_refs_present_changes_hash_and_joins_one_key(monkeypatch):
    deployment = _deployment(monkeypatch)
    refs = _runtime_refs()

    joined = deployment.artifact_components_with_refs(refs)

    assert deployment.artifact_hash_with_refs(refs) != deployment.artifact_hash
    assert joined == {**deployment.artifact_components, "pureRuntimeRefs": refs}
    assert set(joined) == {*deployment.artifact_components, "pureRuntimeRefs"}


def test_pure_runtime_ref_perturbations_change_hash(monkeypatch):
    deployment = _deployment(monkeypatch)
    base_hash = deployment.artifact_hash_with_refs(_runtime_refs())

    wasm_hash = deployment.artifact_hash_with_refs(_runtime_refs(executor_tier="wasm"))
    env_hash = deployment.artifact_hash_with_refs(
        _runtime_refs(env_hash="env:" + ("b" * 64))
    )
    bundle_hash = deployment.artifact_hash_with_refs(_runtime_refs(bundle_hash="c" * 64))

    assert wasm_hash != base_hash
    assert env_hash != base_hash
    assert bundle_hash != base_hash


def test_pure_runtime_refs_are_canonicalized_by_content(monkeypatch):
    deployment = _deployment(monkeypatch)
    bundle_hash = "d" * 64
    first = {
        "runtime.ref.a": {
            "sourceHash": "pure:aaaaaaaaaaaaaaaa",
            "abi": "python-source/json-v1",
            "bundleHash": bundle_hash,
            "executorTier": "native",
        },
        "runtime.ref.b": {
            "executorTier": "native",
            "bundleHash": bundle_hash,
            "abi": "python-source/json-v1",
            "sourceHash": "pure:bbbbbbbbbbbbbbbb",
        },
    }
    second = {
        "runtime.ref.b": {
            "sourceHash": "pure:bbbbbbbbbbbbbbbb",
            "abi": "python-source/json-v1",
            "bundleHash": bundle_hash,
            "executorTier": "native",
        },
        "runtime.ref.a": {
            "executorTier": "native",
            "bundleHash": bundle_hash,
            "abi": "python-source/json-v1",
            "sourceHash": "pure:aaaaaaaaaaaaaaaa",
        },
    }

    assert canonical_json(deployment.artifact_components_with_refs(first)) == canonical_json(
        deployment.artifact_components_with_refs(second)
    )
    assert deployment.artifact_hash_with_refs(first) == deployment.artifact_hash_with_refs(second)


def test_pure_runtime_refs_do_not_mutate_cached_base(monkeypatch):
    deployment = _deployment(monkeypatch)
    refs = _runtime_refs()
    base_hash = deployment.artifact_hash

    joined = deployment.artifact_components_with_refs(refs)
    with_refs_hash = deployment.artifact_hash_with_refs(refs)

    assert "pureRuntimeRefs" not in deployment.artifact_components
    assert deployment.artifact_hash == base_hash
    assert joined is not deployment.artifact_components
    assert with_refs_hash != base_hash
