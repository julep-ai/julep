from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("cryptography")

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from julep import HAVE_TEMPORAL, arr, deploy, pure, seq
from julep.bundle import ABI_PYTHON_SOURCE_JSON_V1
from julep.artifact_store import ArtifactIntegrityError, LocalDirArtifactStore
from julep.contracts import manifest_from_json
from julep.errors import PureDriftError
from julep.execution import effects
from julep.execution.effects import VerifyPuresInput, WorkerContext, configure, verifyPures
from julep.execution.interpreter import InMemoryEnv, interpret
from julep.ir import Node, canonical_json
from julep.projection import InMemoryProjection, ProjectionEmitter
from julep.registry import PureEntry, Registry, _text_hash
from julep.worker_store import (
    BundleResolutionError,
    _manifest_pures,
    bundle_ref_entries,
    load_bundles_from_env,
    resolve_and_register,
)
from conftest import read_snapshot, run

if HAVE_TEMPORAL:
    from temporalio.api.common.v1 import Payloads
    from temporalio.bridge.proto.workflow_activation import WorkflowActivation
    from temporalio.bridge.proto.workflow_completion import WorkflowActivationCompletion
    from temporalio.converter import DefaultFailureConverter, DefaultPayloadConverter
    from temporalio.worker import WorkflowInstance, WorkflowRunner
    from temporalio.worker._workflow_instance import WorkflowInstanceDetails

    from julep.execution.bundle_runner import (
        BundleResolvingWorkflowRunner,
        _BundleResolvingInstance,
    )
    from julep.execution.harness import FlowInput


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


def _artifact_path(root: Path, digest: str) -> Path:
    return root / digest[:2] / digest[2:4] / digest


def _json_from_store(store: LocalDirArtifactStore, digest: str) -> dict[str, Any]:
    return json.loads(store.get(digest).decode("utf-8"))


def _put_signature(store: LocalDirArtifactStore, bundle_hash: str, seed: str) -> str:
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
    store = LocalDirArtifactStore(tmp_path)
    deployment = _deployment()
    rec = deployment.publish(store, signing_key=SEED_A)
    return store, deployment, rec


def _manifest_with_pure(**updates: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "abi": ABI_PYTHON_SOURCE_JSON_V1,
        "name": "bundle.worker.canonical.v1",
        "source": "a" * 64,
        "sourceHash": "pure:" + "b" * 16,
    }
    record.update(updates)
    return {"pures": [record]}


def test_manifest_pures_uses_omitted_wasm_default() -> None:
    [record] = _manifest_pures(_manifest_with_pure())

    assert record.executor_tier == "wasm"


@pytest.mark.parametrize("executor_tier", ["wasm", None])
def test_manifest_pures_rejects_explicit_wasm_default(executor_tier: Any) -> None:
    with pytest.raises(BundleResolutionError, match="omit executorTier"):
        _manifest_pures(_manifest_with_pure(executorTier=executor_tier))


@pytest.mark.parametrize(
    "fields",
    [
        {"envHash": None},
        {"envComponent": None},
        {"envHash": None, "envComponent": None},
    ],
)
def test_manifest_pures_rejects_null_env_fields(fields: dict[str, Any]) -> None:
    with pytest.raises(BundleResolutionError, match="envHash and envComponent"):
        _manifest_pures(_manifest_with_pure(**fields))


@pytest.mark.parametrize("field", ["deps", "requiresPython"])
def test_manifest_pures_rejects_null_native_only_fields_on_wasm(field: str) -> None:
    with pytest.raises(BundleResolutionError, match="must not carry deps/requiresPython"):
        _manifest_pures(_manifest_with_pure(**{field: None}))


def test_manifest_pures_distinguishes_missing_from_null_native_requires_python() -> None:
    with pytest.raises(BundleResolutionError, match="must carry executorTier, deps"):
        _manifest_pures(
            _manifest_with_pure(executorTier="native", deps=["numpy==2"])
        )

    [record] = _manifest_pures(
        _manifest_with_pure(
            executorTier="native",
            deps=["numpy==2"],
            requiresPython=None,
        )
    )
    assert record.executor_tier == "native"
    assert record.dep_list == ("numpy==2",)
    assert record.requires_python is None


def _resolve(
    store: LocalDirArtifactStore,
    rec: dict[str, Any],
    registry: Registry,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Any]:
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
        "artifactComponents": deployment.artifact_hash.removeprefix("sha256:"),
        "flow": _json_from_store(store, rec["bundleHash"])["flow"],
        "registered": expected_pins,
    }
    assert fresh.source_hash_of("bundle.worker.normalize.v1") == expected_pins[
        "bundle.worker.normalize.v1"
    ]
    assert fresh.source_hash_of("bundle.worker.summarize.v1") == expected_pins[
        "bundle.worker.summarize.v1"
    ]
    # Bundle resolution registers pures as the wasm tier end to end: they execute
    # in the wasmtime sandbox, never natively in-process.
    assert fresh.pures["bundle.worker.normalize.v1"].executor == "wasm"
    assert fresh.pures["bundle.worker.summarize.v1"].executor == "wasm"

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
    assert all(ref["executorTier"] == "wasm" for ref in rec["pureRuntimeRefs"].values())
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
        _artifact_path(tmp_path, rec["bundleHash"]).write_bytes(b"{}")
    elif target == "source":
        manifest = _json_from_store(store, rec["bundleHash"])
        _artifact_path(tmp_path, manifest["pures"][0]["source"]).write_bytes(b"tampered")
    else:
        signature = _json_from_store(store, rec["signatureDigest"])
        signature["sig"] = ("0" if signature["sig"][0] != "0" else "1") + signature["sig"][1:]
        signature_digest = store.put(canonical_json(signature).encode("utf-8"))

    with pytest.raises((BundleResolutionError, ArtifactIntegrityError)):
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
    assert existing.executor == "wasm"
    # The equal-hash re-resolve is a no-op: the stored entry is unchanged and
    # still wasm-tier. get_pure returns a wasm-bound callable (never a host fn:
    # bundle source is not exec'd on the host) that produces the value computed
    # inside the wasm sandbox, equal to the native reference for the same source.
    sample = {"name": "  ada  ", "score": "7"}
    resolved = fresh.get_pure(first_pure["name"])
    assert resolved is not existing.fn
    # The native reference is the baked pure of the same name (a trusted host fn).
    baked_by_name = {
        "bundle.worker.normalize.v1": _bundle_worker_normalize.fn,
        "bundle.worker.summarize.v1": _bundle_worker_summarize.fn,
    }
    native_reg = Registry()
    native_reg.register_pure(first_pure["name"], baked_by_name[first_pure["name"]])
    assert resolved(sample) == native_reg.get_pure(first_pure["name"])(sample)


def test_equal_hash_baked_pure_is_promoted_to_wasm_on_resolve(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pure baked NATIVELY into the worker with the same source the bundle ships
    (equal hash) must be PROMOTED to the wasm tier on resolution — it must not
    silently stay native, or a bundle-sourced pure would escape the sandbox.
    """
    store, _deployment, rec = _published(tmp_path)
    manifest = _json_from_store(store, rec["bundleHash"])
    first_pure = manifest["pures"][0]
    source = store.get(first_pure["source"]).decode("utf-8")

    fresh = Registry()
    # Bake the same-source pure natively, pinned to the bundle's exact sourceHash.
    baked_by_name = {
        "bundle.worker.normalize.v1": _bundle_worker_normalize.fn,
        "bundle.worker.summarize.v1": _bundle_worker_summarize.fn,
    }
    baked = fresh.register_pure(first_pure["name"], baked_by_name[first_pure["name"]])
    fresh.pures[first_pure["name"]] = PureEntry(
        name=baked.name,
        fn=baked.fn,
        source_hash=_text_hash(source),
        executor="native",
    )
    assert fresh.pures[first_pure["name"]].executor == "native"

    _resolve(store, rec, fresh, monkeypatch)

    promoted = fresh.pures[first_pure["name"]]
    assert promoted.executor == "wasm", "equal-hash baked pure must be promoted to wasm"
    assert promoted.source == source
    # get_pure now returns a wasm-bound callable, not the baked native fn.
    assert fresh.get_pure(first_pure["name"]) is not baked.fn


def test_missing_wasm_extra_fails_fast_at_resolution_not_at_lookup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A worker missing the `wasm` extra must FAIL FAST at resolution with a
    BundleResolutionError carrying install guidance — not register the wasm pures
    and then blow up with a raw ModuleNotFoundError at the first lookup inside
    workflow code (a WorkflowTaskFailed mid-run).
    """
    import builtins

    store, _deployment, rec = _published(tmp_path)
    fresh = Registry()

    # Simulate the absence of the `wasm` extra: importing the wasm executor (which
    # imports wasmtime at module top) raises ModuleNotFoundError.
    import julep.execution.wasm_executor as wasm_mod

    monkeypatch.delitem(
        __import__("sys").modules,
        "julep.execution.wasm_executor",
        raising=False,
    )
    real_import = builtins.__import__

    def _fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "julep.execution.wasm_executor" or name == "wasmtime":
            raise ModuleNotFoundError("No module named 'wasmtime'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    with pytest.raises(BundleResolutionError) as excinfo:
        _resolve(store, rec, fresh, monkeypatch)

    message = str(excinfo.value)
    assert "wasm" in message
    assert "julep[wasm]" in message
    # The wasm pures must NOT have been registered before the fast failure.
    assert not fresh.pures
    # Sanity: the real module is still importable after the test (monkeypatch undo).
    assert wasm_mod is not None


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


def test_resolution_is_ungated_and_registers_wasm_tier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # P3: the former P2 dev-only JULEP_BUNDLE_NATIVE_EXEC native-exec gate is gone.
    # Bundle pures run in the wasm sandbox (not natively in-process), so
    # resolution succeeds by default and registers pures as the wasm tier.
    store, _deployment, rec = _published(tmp_path)
    monkeypatch.delenv("JULEP_BUNDLE_NATIVE_EXEC", raising=False)
    fresh = Registry()

    resolved = resolve_and_register(
        store,
        rec["bundleHash"],
        signature_digest=rec["signatureDigest"],
        allowed_signers=[_public_key(SEED_A)],
        registry=fresh,
    )

    assert resolved["registered"]
    assert all(entry.executor == "wasm" for entry in fresh.pures.values())


def test_manual_built_manifest_rejects_std_pure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = LocalDirArtifactStore(tmp_path)
    source_digest = store.put(b"@pure(\"std.bad\")\ndef bad(value):\n    return value\n")
    components = {
        "flowJson": arr("std.bad").to_json(),
        "manifestJson": {},
        "pureSourceHashes": {"std.bad": "pure:0123456789abcdef"},
        "reasoners": {},
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
    store = LocalDirArtifactStore(tmp_path)
    name = "bundle.worker.bad_source_hash.v1"
    source = f"""@pure("{name}")\ndef bad_source_hash(value):\n    return value\n"""
    source_digest = store.put(source.encode("utf-8"))
    components_digest = store.put(
        canonical_json(
            {
                "flowJson": arr(name).to_json(),
                "manifestJson": {},
                "pureSourceHashes": {name: "pure:0000000000000000"},
                "reasoners": {},
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
    monkeypatch.setenv("JULEP_ARTIFACT_STORE_URL", f"file://{tmp_path}")
    monkeypatch.setenv("JULEP_BUNDLES", f"{rec['bundleHash']}:{rec['signatureDigest']}")
    monkeypatch.setenv("JULEP_BUNDLE_ALLOWED_SIGNERS", f" {_public_key(SEED_A)} ")

    first = load_bundles_from_env(registry=fresh)
    second = load_bundles_from_env(registry=fresh)

    assert first == second
    assert set(first[0]["registered"]) == set(rec["pureRuntimeRefs"])


def test_load_bundles_from_env_noop_and_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fresh = Registry()

    monkeypatch.delenv("JULEP_BUNDLES", raising=False)
    assert load_bundles_from_env(registry=fresh) == []

    monkeypatch.setenv("JULEP_BUNDLES", "abc")
    monkeypatch.delenv("JULEP_ARTIFACT_STORE_URL", raising=False)
    with pytest.raises(BundleResolutionError, match="JULEP_ARTIFACT_STORE_URL"):
        load_bundles_from_env(registry=fresh)

    monkeypatch.setenv("JULEP_ARTIFACT_STORE_URL", f"file://{tmp_path}")
    with pytest.raises(BundleResolutionError, match="<bundleHash>:<signatureDigest>"):
        load_bundles_from_env(registry=fresh)


def test_verify_pures_resolves_bundle_on_fresh_activity_registry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _store, deployment, rec = _published(tmp_path)
    fresh = Registry()
    configure(WorkerContext(registry=fresh))
    monkeypatch.setenv("JULEP_ARTIFACT_STORE_URL", f"file://{tmp_path}")
    bundle = [{"bundleHash": rec["bundleHash"], "signatureDigest": rec["signatureDigest"]}]
    resolved_entries = []
    manifest = _json_from_store(_store, rec["bundleHash"])

    def fake_resolve_entries(store, entries, *, registry):
        resolved_entries.extend(entries)
        for name, source_hash in deployment.artifact_components["pureSourceHashes"].items():
            registry.pures[name] = PureEntry(
                name=name,
                fn=lambda value: value,
                source_hash=source_hash,
                executor="wasm",
            )
        return [
            {
                "bundleHash": rec["bundleHash"],
                "artifactHash": deployment.artifact_hash,
                "flow": manifest["flow"],
                "registered": deployment.artifact_components["pureSourceHashes"],
            }
        ]

    monkeypatch.setattr(effects, "resolve_entries", fake_resolve_entries)

    run(
        verifyPures(
            VerifyPuresInput(
                pinned=deployment.artifact_components["pureSourceHashes"],
                bundle=bundle,
                flow_json=deployment.flow_json,
            )
        )
    )

    assert resolved_entries == [(rec["bundleHash"], rec["signatureDigest"])]
    assert set(fresh.pures) == set(deployment.artifact_components["pureSourceHashes"])
    assert all(entry.executor == "wasm" for entry in fresh.pures.values())


def test_verify_pures_rejects_bundle_bound_to_different_flow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _store, deployment, rec = _published(tmp_path)
    configure(WorkerContext(registry=Registry()))
    monkeypatch.setenv("JULEP_ARTIFACT_STORE_URL", f"file://{tmp_path}")
    bundle = [{"bundleHash": rec["bundleHash"], "signatureDigest": rec["signatureDigest"]}]

    def fake_resolve_entries(store, entries, *, registry):
        for name, source_hash in deployment.artifact_components["pureSourceHashes"].items():
            registry.pures[name] = PureEntry(
                name=name,
                fn=lambda value: value,
                source_hash=source_hash,
                executor="wasm",
            )
        return [
            {
                "bundleHash": rec["bundleHash"],
                "artifactHash": deployment.artifact_hash,
                "flow": _json_from_store(_store, rec["bundleHash"])["flow"],
                "registered": deployment.artifact_components["pureSourceHashes"],
            }
        ]

    monkeypatch.setattr(effects, "resolve_entries", fake_resolve_entries)

    with pytest.raises(PureDriftError, match="bundle flow mismatch"):
        run(
            verifyPures(
                VerifyPuresInput(
                    pinned=deployment.artifact_components["pureSourceHashes"],
                    bundle=bundle,
                    flow_json=arr("bundle.worker.normalize.v1").to_json(),
                )
            )
        )


def test_verify_pures_bundle_resolution_failure_is_pure_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _store, deployment, rec = _published(tmp_path)
    configure(WorkerContext(registry=Registry()))
    monkeypatch.delenv("JULEP_ARTIFACT_STORE_URL", raising=False)
    bundle = [{"bundleHash": rec["bundleHash"], "signatureDigest": rec["signatureDigest"]}]

    with pytest.raises(PureDriftError, match="JULEP_ARTIFACT_STORE_URL"):
        run(
            verifyPures(
                VerifyPuresInput(
                    pinned=deployment.artifact_components["pureSourceHashes"],
                    bundle=bundle,
                    flow_json=deployment.flow_json,
                )
            )
        )


if HAVE_TEMPORAL:

    class _DummyInstance(WorkflowInstance):
        def __init__(self) -> None:
            self.activated = 0

        def activate(self, act: WorkflowActivation) -> WorkflowActivationCompletion:
            self.activated += 1
            return WorkflowActivationCompletion()

        def get_serialization_context(self, command_info):
            return None

        def get_external_store_context(self, command_info):
            return None

        def get_info(self):
            return None

    class _DummyRunner(WorkflowRunner):
        def __init__(self, instance: _DummyInstance) -> None:
            self.instance = instance
            self.prepared = []
            self.failure_types = []

        def prepare_workflow(self, defn) -> None:
            self.prepared.append(defn)

        def create_instance(self, det: WorkflowInstanceDetails) -> WorkflowInstance:
            return self.instance

        def set_worker_level_failure_exception_types(self, types) -> None:
            self.failure_types = list(types)


def _workflow_details() -> "WorkflowInstanceDetails":
    return WorkflowInstanceDetails(
        payload_converter_class=DefaultPayloadConverter,
        failure_converter_class=DefaultFailureConverter,
        interceptor_classes=[],
        defn=None,
        info=None,
        randomness_seed=1,
        extern_functions={},
        disable_eager_activity_execution=False,
        worker_level_failure_exception_types=[],
        last_completion_result=Payloads(),
        last_failure=None,
    )


def _flow_activation(bundle: list[dict[str, str]]) -> "WorkflowActivation":
    converter = DefaultPayloadConverter()
    act = WorkflowActivation()
    job = act.jobs.add()
    job.initialize_workflow.workflow_type = "FlowWorkflow"
    job.initialize_workflow.arguments.extend(
        converter.to_payloads([FlowInput(session_id="sess", flow_json={}, manifest_json={}, bundle=bundle)])
    )
    return act


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_bundle_runner_resolves_flow_input_bundle_before_activation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, deployment, rec = _published(tmp_path)
    fresh = Registry()
    monkeypatch.setenv("JULEP_BUNDLE_ALLOWED_SIGNERS", _public_key(SEED_A))
    dummy = _DummyInstance()
    runner = BundleResolvingWorkflowRunner(
        inner=_DummyRunner(dummy),
        store=store,
        registry=fresh,
    )
    bundle = [{"bundleHash": rec["bundleHash"], "signatureDigest": rec["signatureDigest"]}]

    instance = runner.create_instance(_workflow_details())
    instance.activate(_flow_activation(bundle))
    instance.activate(_flow_activation(bundle))

    assert dummy.activated == 2
    assert fresh.source_hash_of("bundle.worker.normalize.v1") == deployment.artifact_components[
        "pureSourceHashes"
    ]["bundle.worker.normalize.v1"]
    assert fresh.source_hash_of("bundle.worker.summarize.v1") == deployment.artifact_components[
        "pureSourceHashes"
    ]["bundle.worker.summarize.v1"]


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_bundle_runner_is_inert_without_store(tmp_path: Path) -> None:
    _store, _deployment, rec = _published(tmp_path)
    fresh = Registry()
    dummy = _DummyInstance()
    runner = BundleResolvingWorkflowRunner(
        inner=_DummyRunner(dummy),
        store=None,
        registry=fresh,
    )
    bundle = [{"bundleHash": rec["bundleHash"], "signatureDigest": rec["signatureDigest"]}]

    runner.create_instance(_workflow_details()).activate(_flow_activation(bundle))

    assert dummy.activated == 1
    assert fresh.pures == {}


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_bundle_runner_forwards_current_workflow_instance_abstract_methods() -> None:
    abstract_methods = WorkflowInstance.__abstractmethods__
    assert abstract_methods
    assert abstract_methods <= _BundleResolvingInstance.__dict__.keys()
    assert _BundleResolvingInstance.__abstractmethods__ == frozenset()


def test_bundle_entries_fail_closed_on_malformed() -> None:
    # A present-but-malformed bundle ref must FAIL CLOSED (raise), never be
    # silently skipped -- otherwise a flow meant to run signed pures falls back
    # to ambient/stale registry state, defeating the code-as-data signing
    # guarantee. A genuinely absent bundle stays a valid no-op.
    good = [{"bundleHash": "a" * 64, "signatureDigest": "b" * 64}]
    assert bundle_ref_entries(None) == []
    assert bundle_ref_entries([]) == []
    assert bundle_ref_entries(good) == [("a" * 64, "b" * 64)]

    with pytest.raises(BundleResolutionError):
        bundle_ref_entries({"bundleHash": "a" * 64, "signatureDigest": "b" * 64})  # not a list
    with pytest.raises(BundleResolutionError):
        bundle_ref_entries([42])  # entry not an object
    with pytest.raises(BundleResolutionError):
        bundle_ref_entries([{"bundleHash": "a" * 64}])  # missing signatureDigest
    with pytest.raises(BundleResolutionError):
        bundle_ref_entries([{"bundleHash": "nothex", "signatureDigest": "b" * 64}])  # bad hex
