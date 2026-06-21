"""P3 parity gate: the grade-scores demo flow yields the IDENTICAL result value
whether its pures run baked (native, in-process) or bundle-sourced (wasm).

``examples/grade_scores_flow.py`` is the P2.5 pures-only, bundle-shippable demo
target. This module runs its ``dry_run`` twice over the same frozen artifact:

* baked: ``Deployment.adry_run`` resolves the three pures from ``DEFAULT_REGISTRY``
  where ``@pure(...)`` registered them as ``executor == "native"``; and
* bundle-sourced: a fresh ``Registry`` holds the SAME three pures, registered via
  ``register_pure_from_source`` (``executor == "wasm"``) from each pure's frozen
  source text — exactly how a signed CAS bundle materialises them on a worker.

Both runs drive the identical ``deployment.flow`` IR through ``interpret``; only
the executor tier of the leaf pures differs. The flow is reasoner-free and tool-free,
so the only non-determinism the test could expose is a wasm-vs-native divergence
in a pure's output — which the value assertion forbids. This is the spec parity
gate: bundle-sourced (wasm) MUST equal baked (native), byte-for-byte in value.
"""

from __future__ import annotations

import asyncio
import inspect

from composable_agents.execution.interpreter import InMemoryEnv, interpret
from composable_agents.projection import InMemoryProjection, ProjectionEmitter
from composable_agents.registry import DEFAULT_REGISTRY, Registry
from examples import grade_scores_flow

# The three leaf pures the grade-scores flow composes; all bundle-shippable.
GRADE_PURE_NAMES = (
    "cad.demo.normalize_record.v1",
    "cad.demo.grade_one.v1",
    "cad.demo.tally_grades.v1",
)


def _wasm_registry_for(names: tuple[str, ...]) -> Registry:
    """A registry whose ``names`` are bundle-sourced (wasm tier).

    The source is taken from each baked pure via ``inspect.getsource`` — the same
    text ``deploy()`` would freeze into a CAS bundle — and re-registered through
    ``register_pure_from_source`` so the registry routes them to the wasm tier.
    """
    reg = Registry()
    for name in names:
        source = inspect.getsource(DEFAULT_REGISTRY.pures[name].fn)
        entry = reg.register_pure_from_source(name, source)
        assert entry.executor == "wasm", f"{name} should be wasm-tier, got {entry.executor}"
    return reg


def _run_flow_with_registry(value: object, registry: Registry | None) -> object:
    """Drive the grade-scores flow's frozen IR exactly like ``Deployment.adry_run``,
    but with a swappable pure registry so we can flip the leaf executor tier."""
    deployment = grade_scores_flow.build()
    env = InMemoryEnv(
        deployment.manifest,
        ProjectionEmitter(InMemoryProjection()),
        registry=registry,  # None -> DEFAULT_REGISTRY (baked/native)
    )
    return asyncio.run(interpret(deployment.flow, value, env)).value


def test_grade_scores_flow_wasm_matches_native() -> None:
    """The full demo flow: baked (native) result value == bundle-sourced (wasm)."""
    # Baked path: resolves all three pures from DEFAULT_REGISTRY as native.
    native_value = _run_flow_with_registry(grade_scores_flow.SCORES, registry=None)

    # Bundle-sourced path: the SAME flow IR, but the three pures are wasm-tier.
    wasm_reg = _wasm_registry_for(GRADE_PURE_NAMES)
    wasm_value = _run_flow_with_registry(grade_scores_flow.SCORES, registry=wasm_reg)

    assert wasm_value == native_value
    # Sanity: the run actually graded the roster (not an empty/short-circuit result).
    assert isinstance(native_value, dict)
    assert native_value["passed"] == 4
    assert native_value["tally"] == {"A": 1, "B": 2, "C": 1, "F": 1}


def test_grade_scores_flow_wasm_matches_native_messy_input() -> None:
    """Parity holds on a roster that exercises the normalize pure (whitespace +
    string scores) — the most divergence-prone pure if wasm and native disagreed."""
    roster = [
        {"name": "  Ada  ", "score": "100"},
        {"name": "Bob", "score": 59},
        {"name": "\tCarol\n", "score": "60"},
    ]
    native_value = _run_flow_with_registry(roster, registry=None)
    wasm_value = _run_flow_with_registry(roster, registry=_wasm_registry_for(GRADE_PURE_NAMES))

    assert wasm_value == native_value
    assert isinstance(native_value, dict)
    assert native_value["tally"] == {"A": 1, "D": 1, "F": 1}
