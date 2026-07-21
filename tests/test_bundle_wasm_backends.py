"""Bundle-sourced (tier="wasm") pures execute via the wasmtime sandbox across
all three backends.

The seam is a single change in ``Registry.get_pure``: a wasm-tier pure (one
registered through ``register_pure_from_source``, i.e. arrived from a signed CAS
bundle) resolves to a wasm-bound callable that runs the pure inside a fresh
wasmtime CPython component instance. All three engine Envs route pure lookups
through the process registry, so this module asserts that:

* the Temporal worker passes ``wasmtime`` through the workflow sandbox, and an
  end-to-end Temporal flow whose only pure is bundle-sourced runs via wasm and
  returns the correct value (proving the passthrough wiring);
* the DBOS env (``DbosEnv.get_pure``) and the CMA env (``CMAAgentEnv.get_pure``)
  inherit the wasm tier for free via the registry; and
* a baked (native) pure and the same source resolved as a bundle (wasm) produce
  the identical value (parity), per the grade-scores demo target.

The DBOS/CMA cases need no database or live agent client: they exercise only the
``get_pure`` routing, which is pure compute.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("cryptography")

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from julep import HAVE_TEMPORAL, arr, deploy, pure, seq
from julep.cas import LocalDirCAS
from julep.execution import HAVE_DBOS
from julep.projection import InMemoryProjection, ProjectionEmitter
from julep.registry import Registry, _wasm_source_only

# A bundle-shippable source: the SAME text runs natively and in wasm because the
# component replicates the @pure(...) registry shim (see executor_component.py).
SCALE_SOURCE = (
    '@pure("wasm.backends.scale.v1")\n'
    "def scale(value, *, factor=2):\n"
    "    return value * factor\n"
)
SCALE_NAME = "wasm.backends.scale.v1"

SEED = "55" * 32

# Defined at MODULE level with a STRING-LITERAL name so inspect.getsource (used
# by deploy() to freeze the pure into the bundle) captures dedented, fully
# self-contained source. A nested def would ship leading indentation, and a
# non-literal name (a module constant) would NameError when the source is
# re-exec'd in the isolated resolution namespace -- both fail on resolution.
E2E_DOUBLE_NAME = "wasm.backends.e2e.double.v1"


@pure("wasm.backends.e2e.double.v1")
def _e2e_double(value: int) -> int:
    return value * 2


def _public_key(seed: str) -> str:
    return (
        Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed))
        .public_key()
        .public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        .hex()
    )


def _emitter() -> ProjectionEmitter:
    return ProjectionEmitter(InMemoryProjection())


def _wasm_registry() -> Registry:
    """A fresh registry holding only the bundle-sourced (wasm-tier) scale pure."""
    reg = Registry()
    entry = reg.register_pure_from_source(SCALE_NAME, SCALE_SOURCE)
    assert entry.executor == "wasm"
    return reg


# --------------------------------------------------------------------------- #
# Registry seam: a wasm-tier pure resolves to a wasm-bound callable.
# --------------------------------------------------------------------------- #
def test_registry_routes_bundle_pure_through_wasm() -> None:
    reg = _wasm_registry()
    entry = reg.pures[SCALE_NAME]

    resolved = reg.get_pure(SCALE_NAME)

    # Not a host fn: get_pure returns the wasm-bound callable for wasm tier, and
    # the entry's fn is the sentinel (bundle source is never exec'd on the host).
    assert resolved is not entry.fn
    assert entry.fn is _wasm_source_only
    # ...the wasm-bound callable produces the expected value via the wasm executor.
    assert resolved(21) == 42
    assert resolved(5, factor=3) == 15


def test_baked_native_and_bundle_wasm_parity() -> None:
    """Parity target: baked (native) vs bundle-sourced (wasm) give the same value."""
    native_reg = Registry()

    def scale(value: int, *, factor: int = 2) -> int:
        return value * factor

    native_reg.register_pure(SCALE_NAME, scale)
    wasm_reg = _wasm_registry()

    for sample in (0, 7, 21, 100):
        assert native_reg.get_pure(SCALE_NAME)(sample) == wasm_reg.get_pure(SCALE_NAME)(sample)


def test_grade_scores_demo_baked_vs_wasm_parity() -> None:
    """Spec parity gate: the grade-scores demo pures (the P2.5 bundle-shippable
    target) produce identical values baked (native) and bundle-sourced (wasm)."""
    import inspect

    from julep.registry import DEFAULT_REGISTRY
    from examples import grade_scores_flow  # noqa: F401  (import registers the pures)

    names = [
        "cad.demo.normalize_record.v1",
        "cad.demo.grade_one.v1",
        "cad.demo.tally_grades.v1",
    ]
    wasm_reg = Registry()
    for name in names:
        source = inspect.getsource(DEFAULT_REGISTRY.pures[name].fn)
        entry = wasm_reg.register_pure_from_source(name, source)
        assert entry.executor == "wasm"

    def native(name: str) -> Any:
        return DEFAULT_REGISTRY.get_pure(name)

    def wasm(name: str) -> Any:
        return wasm_reg.get_pure(name)

    record = {"name": " Linus ", "score": "82"}
    norm_native = native("cad.demo.normalize_record.v1")(record)
    norm_wasm = wasm("cad.demo.normalize_record.v1")(record)
    assert norm_native == norm_wasm

    assert native("cad.demo.grade_one.v1")(norm_native) == wasm("cad.demo.grade_one.v1")(norm_wasm)

    graded = [
        {"name": "Ada", "score": 91, "grade": "A", "passed": True},
        {"name": "Bob", "score": 58, "grade": "F", "passed": False},
    ]
    assert native("cad.demo.tally_grades.v1")(graded) == wasm("cad.demo.tally_grades.v1")(graded)


# --------------------------------------------------------------------------- #
# DBOS backend: DbosEnv.get_pure inherits the wasm tier via the registry.
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_env_runs_bundle_pure_via_wasm() -> None:
    from julep.execution.dbos_backend import DbosEnv
    from julep.execution.policy import ExecutionPolicy
    from julep.purity import register_pure_from_source
    from julep.registry import DEFAULT_REGISTRY

    # DbosEnv.get_pure routes through purity.get_pure -> DEFAULT_REGISTRY, so the
    # bundle pure must live in the process-global registry for this backend.
    DEFAULT_REGISTRY.pures.pop(SCALE_NAME, None)
    try:
        entry = register_pure_from_source(SCALE_NAME, SCALE_SOURCE)
        assert entry.executor == "wasm"

        env = DbosEnv(
            manifest={},
            emitter=_emitter(),
            session_id="sess",
            manifest_json={},
            policy=ExecutionPolicy(),
        )
        resolved = env.get_pure(SCALE_NAME)

        # wasm tier: a wasm-bound callable (not the native fn) with correct value.
        assert resolved is not entry.fn
        assert resolved(21) == 42
        assert resolved(5, factor=3) == 15
    finally:
        DEFAULT_REGISTRY.pures.pop(SCALE_NAME, None)


# --------------------------------------------------------------------------- #
# CMA backend: CMAAgentEnv.get_pure delegates to the inner env (registry).
# --------------------------------------------------------------------------- #
def test_cma_env_runs_bundle_pure_via_wasm() -> None:
    from julep import AgentConfig
    from julep.execution.cma import CMAAgentEnv
    from julep.execution.interpreter import InMemoryEnv

    # InMemoryEnv.get_pure resolves from a registry; point it at one holding the
    # bundle-sourced (wasm-tier) pure, and CMAAgentEnv delegates unchanged.
    reg = _wasm_registry()
    entry = reg.pures[SCALE_NAME]
    inner = InMemoryEnv({}, _emitter(), registry=reg)
    env = CMAAgentEnv(
        inner,
        client=object(),  # never touched: get_pure is pure registry routing
        tools={},
        cfg=AgentConfig(),
    )

    resolved = env.get_pure(SCALE_NAME)

    assert resolved is not entry.fn
    assert resolved(21) == 42
    assert resolved(5, factor=3) == 15


# --------------------------------------------------------------------------- #
# Temporal backend: the worker passes wasmtime through the workflow sandbox, and
# an end-to-end bundle-sourced flow runs via wasm.
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_build_worker_passes_wasmtime_through_sandbox(monkeypatch: pytest.MonkeyPatch) -> None:
    from temporalio.worker.workflow_sandbox import SandboxRestrictions

    import julep.execution.worker as worker_mod
    from julep.execution.activities import WorkerContext
    from julep.execution.bundle_runner import BundleResolvingWorkflowRunner

    # Capture the workflow_runner build_worker constructs without standing up a
    # real Worker (which needs a live client). Worker is patched to record kwargs
    # then short-circuit; the runner it would have received is what we assert on.
    captured: dict[str, Any] = {}

    class _Sentinel(Exception):
        pass

    def _spy_worker(*_args: Any, **kwargs: Any) -> Any:
        captured["workflow_runner"] = kwargs.get("workflow_runner")
        raise _Sentinel

    monkeypatch.setattr(worker_mod, "Worker", _spy_worker)

    with pytest.raises(_Sentinel):
        worker_mod.build_worker(object(), WorkerContext(), task_queue="q")

    runner = captured["workflow_runner"]
    assert isinstance(runner, BundleResolvingWorkflowRunner)
    # The sandbox must pass wasmtime through so the workflow-side wasm pure call
    # shares the process-global engine/component (else it re-imports wasmtime).
    passthrough = runner.inner.restrictions.passthrough_modules
    assert "wasmtime" in passthrough
    assert "julep" in passthrough
    # Sanity: stock Temporal defaults do NOT pass wasmtime through; our wiring does.
    assert "wasmtime" not in SandboxRestrictions.default.passthrough_modules


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_temporal_flow_runs_bundle_pure_via_wasm(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end: a Temporal flow whose only pure is bundle-sourced runs via the
    wasm sandbox inside workflow code and returns the correct value.

    The baked native registration is removed before the run, so the ONLY way the
    pure can resolve is bundle -> wasm tier -> wasmtime executor. Success proves
    the worker's ``wasmtime`` sandbox passthrough is wired correctly: workflow
    code calls into the process-global wasmtime engine/component, not a sandbox
    re-import.
    """
    import asyncio

    from temporalio.testing import WorkflowEnvironment

    from julep.execution.activities import WorkerContext
    from julep.execution.harness import run_flow
    from julep.execution.worker import build_worker
    from julep.registry import DEFAULT_REGISTRY

    name = E2E_DOUBLE_NAME
    # The module-level @pure(name) baked this into DEFAULT_REGISTRY at import so
    # deploy() can freeze its source; re-register defensively (the run pops it in
    # its finally so the only resolution path during the run is bundle -> wasm).
    if name not in DEFAULT_REGISTRY.pures:
        DEFAULT_REGISTRY.register_pure(name, _e2e_double.fn)

    store = LocalDirCAS(tmp_path)
    deployment = deploy(seq(arr(name)), tools=[])
    rec = deployment.publish(store, signing_key=SEED)

    # The worker's BundleResolvingWorkflowRunner reads STORE_URL; the resolver
    # checks JULEP_BUNDLE_ALLOWED_SIGNERS. No JULEP_BUNDLE_NATIVE_EXEC: P3 resolution is
    # ungated and lands on the wasm tier.
    monkeypatch.setenv("STORE_URL", f"file://{tmp_path}")
    monkeypatch.setenv("JULEP_BUNDLE_ALLOWED_SIGNERS", _public_key(SEED))

    async def _run() -> Any:
        # Remove the baked native registration: the only resolution path left is
        # the signed bundle -> register_pure_from_source -> wasm tier.
        DEFAULT_REGISTRY.pures.pop(name, None)
        async with await WorkflowEnvironment.start_time_skipping() as env:
            worker = build_worker(env.client, WorkerContext(), task_queue="wasm-backends-e2e")
            async with worker:
                bundle = [
                    {"bundleHash": rec["bundleHash"], "signatureDigest": rec["signatureDigest"]}
                ]
                return await run_flow(
                    env.client,
                    deployment.flow_json,
                    deployment.manifest_json,
                    session_id=f"wasm-backends-{uuid.uuid4()}",
                    input=21,
                    task_queue="wasm-backends-e2e",
                    bundle=bundle,
                )

    try:
        out = asyncio.run(_run())
        assert out == 42
        # After the run the worker registry holds the bundle pure as the wasm tier.
        entry = DEFAULT_REGISTRY.pures.get(name)
        assert entry is not None and entry.executor == "wasm"
    finally:
        DEFAULT_REGISTRY.pures.pop(name, None)
