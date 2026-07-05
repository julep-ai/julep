"""Executor selection policy: the single registry seam decides the tier.

The P3 contract is exactly two rules, enforced at one place
(``Registry.get_pure`` / ``Registry.register_*``):

* **Bundle-sourced -> wasm.** A pure registered via ``register_pure_from_source``
  (i.e. it arrived from a signed CAS bundle) has ``executor == "wasm"`` and
  ``get_pure`` returns a wasm-bound callable (NOT the native fn object), so it
  runs inside the wasmtime sandbox.
* **Baked / std.* -> native, unchanged.** A pure registered via ``register_pure``
  (including the whole ``std.*`` library) has ``executor == "native"`` and
  ``get_pure`` returns the native fn object itself, running in-process. The
  golden/baked path is therefore byte-identical.

A bundle is additionally forbidden from shipping a ``std.*`` pure at the
resolution boundary, so std can never be silently downgraded into the sandbox.
"""

from __future__ import annotations

from typing import Any

import pytest

from julep.registry import DEFAULT_REGISTRY, Registry
from julep.std import std_merge

# The full std library — every one of these MUST stay native (baked), forever.
STD_PURE_NAMES = (
    "std.merge",
    "std.pluck",
    "std.init",
    "std.assign",
    "std.collect",
    "std.pack",
    "std.unpack",
    "std.bind",
    "std.each_pack",
    "std.branch_predicate",
    "std.branch_selector",
    "std.continue_with",
)

BUNDLE_SOURCE = (
    '@pure("policy.bundle.pure.v1")\n'
    "def pure_fn(value, *, bump=1):\n"
    "    return value + bump\n"
)
BUNDLE_NAME = "policy.bundle.pure.v1"


def test_std_pures_are_all_native() -> None:
    """Every std.* pure is registered as the native tier in the default registry."""
    for name in STD_PURE_NAMES:
        entry = DEFAULT_REGISTRY.pures[name]
        assert entry.executor == "native", f"{name} must be native, got {entry.executor!r}"
        # The native tier carries no shipped source (it is trusted baked code).
        assert entry.source is None


def test_std_get_pure_returns_the_native_fn_object() -> None:
    """``get_pure`` for a std pure returns the exact native callable — NOT a
    wasm-bound wrapper. This is the baked path; it must stay in-process."""
    entry = DEFAULT_REGISTRY.pures["std.merge"]
    resolved = DEFAULT_REGISTRY.get_pure("std.merge")
    # Identity: the resolved callable IS the baked fn, so no sandbox is involved.
    assert resolved is entry.fn
    assert resolved is std_merge


def test_baked_pure_resolves_native_bundle_pure_resolves_wasm() -> None:
    """Side-by-side selection: same name, different registration path, different
    tier. Baked -> native fn object; bundle-sourced -> wasm-bound wrapper."""
    name = "policy.scale.v1"

    def scale(value: int, *, factor: int = 2) -> int:
        return value * factor

    baked = Registry()
    baked_entry = baked.register_pure(name, scale)
    assert baked_entry.executor == "native"
    assert baked.get_pure(name) is scale  # native: the fn object itself

    bundle = Registry()
    bundle_entry = bundle.register_pure_from_source(
        name,
        '@pure("policy.scale.v1")\ndef scale(value, *, factor=2):\n    return value * factor\n',
    )
    assert bundle_entry.executor == "wasm"
    resolved = bundle.get_pure(name)
    assert resolved is not bundle_entry.fn  # wasm: a wrapper, not the native fn
    # ...and the wrapper still computes the right value via the wasm executor.
    assert resolved(21) == 42
    assert resolved(5, factor=3) == 15


def test_bundle_sourced_pure_is_wasm_tier() -> None:
    """A pure registered from bundle source is wasm-tier with its source retained
    (the wasm executor re-execs that source in the sandbox per call)."""
    reg = Registry()
    entry = reg.register_pure_from_source(BUNDLE_NAME, BUNDLE_SOURCE)
    assert entry.executor == "wasm"
    assert entry.source == BUNDLE_SOURCE

    resolved = reg.get_pure(BUNDLE_NAME)
    assert resolved is not entry.fn
    assert resolved(10) == 11
    assert resolved(10, bump=5) == 15


def test_bundle_cannot_ship_a_std_pure() -> None:
    """Resolution refuses a bundle that ships a ``std.*`` pure, so std can never be
    downgraded into the sandbox — it always stays native/baked."""
    from julep.worker_store import BundleResolutionError, _manifest_pures

    with pytest.raises(BundleResolutionError, match=r"std\.\*"):
        _manifest_pures(
            {
                "pures": [
                    {
                        "name": "std.merge",
                        "abi": "python-source-json-v1",
                        "source": "def std_merge(value):\n    return value\n",
                        "sourceHash": "deadbeef",
                    }
                ]
            }
        )


def test_native_tier_is_unchanged_for_decorated_pures() -> None:
    """A ``@pure(...)``-decorated module pure (the baked path used by the golden
    corpus / demos) is native, and ``get_pure`` returns the fn unwrapped."""
    reg = Registry()

    @reg_pure(reg, "policy.decorated.v1")
    def decorated(value: Any) -> Any:
        return value

    entry = reg.pures["policy.decorated.v1"]
    assert entry.executor == "native"
    assert reg.get_pure("policy.decorated.v1") is entry.fn


def reg_pure(reg: Registry, name: str) -> Any:
    """Local ``@pure``-style decorator bound to a specific registry (mirrors the
    framework decorator, but without touching the process-global registry)."""

    def deco(fn: Any) -> Any:
        reg.register_pure(name, fn)
        return fn

    return deco
