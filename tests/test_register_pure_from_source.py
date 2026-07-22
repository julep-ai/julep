from __future__ import annotations

import hashlib

import pytest

from julep import HAVE_TEMPORAL
from julep.errors import JulepError
from julep.purity import register_pure_from_source
from julep.registry import (
    DEFAULT_REGISTRY,
    PureEntry,
    Registry,
    _text_hash,
    _wasm_source_only,
)


def _expected_hash(source: str) -> str:
    return f"pure:{hashlib.sha256(source.encode('utf-8')).hexdigest()[:16]}"


def test_register_pure_from_source_round_trip() -> None:
    reg = Registry()
    source = """@pure("artifacts.add_one")\ndef add_one(value):\n    return value + 1\n"""

    entry = reg.register_pure_from_source("artifacts.add_one", source)

    assert entry.name == "artifacts.add_one"
    assert reg.source_hash_of("artifacts.add_one") == _expected_hash(source)
    assert reg.get_pure("artifacts.add_one")(41) == 42


def test_register_pure_from_source_keeps_shipped_text_inspectable() -> None:
    reg = Registry()
    source = """@pure("artifacts.echo")\ndef echo(value):\n    return {"value": value}\n"""

    entry = reg.register_pure_from_source("artifacts.echo", source)

    # The canonical shipped text is retained verbatim on the wasm-tier entry
    # (it is what the wasm sandbox re-execs per call). It is NOT recoverable by
    # inspecting a host fn: bundle source is never exec'd on the host, so there
    # is no host fn object to introspect.
    assert entry.source == source
    assert entry.fn is _wasm_source_only


def test_register_pure_from_source_same_source_is_noop() -> None:
    reg = Registry()
    source = """@pure("artifacts.same")\ndef same(value):\n    return value\n"""

    first = reg.register_pure_from_source("artifacts.same", source)
    second = reg.register_pure_from_source("artifacts.same", source)

    assert second is first


def test_equal_hash_baked_pure_is_promoted_to_wasm_not_left_native() -> None:
    """A bundle-sourced pure must run in the wasm sandbox even when the SAME source
    is also baked into the worker (equal hash). register_pure_from_source must
    PROMOTE the equal-hash native entry to the wasm tier, not silently no-op and
    leave it native — otherwise a bundle pure escapes the sandbox.
    """
    reg = Registry()
    source = """@pure("artifacts.baked.eq")\ndef baked_eq(value):\n    return value * 2\n"""

    # Bake it natively (a trusted host fn whose source is exactly the bundle text).
    def baked_eq(value: int) -> int:
        return value * 2

    baked = reg.register_pure("artifacts.baked.eq", baked_eq)
    # Force the baked entry's source_hash to equal the bundle text's hash so this
    # is genuinely the equal-hash case (register_pure hashes the host fn source).
    reg.pures["artifacts.baked.eq"] = PureEntry(
        name=baked.name,
        fn=baked.fn,
        source_hash=_text_hash(source),
        executor="native",
    )
    assert reg.pures["artifacts.baked.eq"].executor == "native"

    promoted = reg.register_pure_from_source("artifacts.baked.eq", source)

    # Promoted, not a no-op: now wasm-tier with the source pinned, and get_pure
    # returns a wasm-bound callable (not the baked native fn).
    assert promoted.executor == "wasm"
    assert promoted.source == source
    assert reg.pures["artifacts.baked.eq"].executor == "wasm"
    assert reg.get_pure("artifacts.baked.eq") is not baked_eq
    assert reg.get_pure("artifacts.baked.eq")(21) == 42


def test_register_pure_from_source_collision_names_both_hashes_and_keeps_original() -> None:
    reg = Registry()
    original = """@pure("artifacts.collision")\ndef collision(value):\n    return value + 1\n"""
    changed = """@pure("artifacts.collision")\ndef collision(value):\n    return value + 2\n"""
    first = reg.register_pure_from_source("artifacts.collision", original)

    with pytest.raises(ValueError) as excinfo:
        reg.register_pure_from_source("artifacts.collision", changed)

    message = str(excinfo.value)
    assert "artifacts.collision" in message
    assert _expected_hash(original) in message
    assert _expected_hash(changed) in message
    assert reg.pures["artifacts.collision"] is first
    assert reg.get_pure("artifacts.collision")(1) == 2


def test_plain_exec_register_pure_uses_wrong_qualname_fallback_but_source_api_does_not() -> None:
    source = """@pure("artifacts.qualname")\ndef qualname(value):\n    return value\n"""

    plain = Registry()

    def pure(name: str):
        def deco(fn):
            plain.register_pure(name, fn)
            return fn

        return deco

    exec(source, {"__name__": "<module>", "pure": pure})

    expected_wrong = _text_hash("<module>.qualname")
    assert plain.source_hash_of("artifacts.qualname") == expected_wrong

    via_source = Registry()
    via_source.register_pure_from_source("artifacts.qualname", source)
    assert via_source.source_hash_of("artifacts.qualname") == _expected_hash(source)


def test_default_registry_register_pure_from_source_shim_forwards() -> None:
    name = "artifacts.default.forward"
    source = """@pure("artifacts.default.forward")\ndef default_forward(value):\n    return value * 3\n"""

    try:
        entry = register_pure_from_source(name, source)
        assert DEFAULT_REGISTRY.source_hash_of(name) == _expected_hash(source)
        assert DEFAULT_REGISTRY.get_pure(name)(7) == 21
        assert entry is DEFAULT_REGISTRY.pures[name]
    finally:
        DEFAULT_REGISTRY.pures.pop(name, None)


def test_register_pure_from_source_decorator_name_mismatch_errors_clearly() -> None:
    reg = Registry()
    source = """@pure("artifacts.actual")\ndef actual(value):\n    return value\n"""

    with pytest.raises(ValueError, match="did not register requested pure 'artifacts.expected'"):
        reg.register_pure_from_source("artifacts.expected", source)

    assert not reg.is_registered("artifacts.expected")


def test_register_pure_from_source_failure_restores_pures_in_place() -> None:
    reg = Registry()

    def keep(value: int) -> int:
        return value + 1

    existing = reg.register_pure("artifacts.keep", keep)
    pures_alias = reg.pures
    source = """@pure("artifacts.actual")\ndef actual(value):\n    return value\n"""

    with pytest.raises(ValueError, match="did not register requested pure 'artifacts.expected'"):
        reg.register_pure_from_source("artifacts.expected", source)

    assert reg.pures is pures_alias
    assert pures_alias["artifacts.keep"] is existing
    assert "artifacts.actual" not in pures_alias
    assert "artifacts.expected" not in pures_alias


def test_register_pure_from_source_newline_less_source_errors_clearly() -> None:
    reg = Registry()
    source = """@pure("artifacts.no_newline")\ndef no_newline(value):\n    return value"""

    with pytest.raises(ValueError, match="source hash mismatch"):
        reg.register_pure_from_source("artifacts.no_newline", source)


def test_baked_pure_is_native_tier_and_get_pure_returns_native_fn() -> None:
    reg = Registry()

    def baked(value: int) -> int:
        return value + 5

    entry = reg.register_pure("artifacts.tier.native", baked)

    assert entry.executor == "native"
    assert entry.source is None
    # native tier: get_pure returns the exact native fn object (identity preserved)
    assert reg.get_pure("artifacts.tier.native") is baked


def test_registry_executor_of_reports_source_tiers_and_unknowns() -> None:
    reg = Registry()
    wasm_source = """@pure("artifacts.tier.wasm.source")\ndef wasm_source(value):\n    return value\n"""
    native_source = (
        """@pure("artifacts.tier.native_venv.source")\n"""
        "def native_source(value):\n"
        "    return value\n"
    )

    reg.register_pure_from_source("artifacts.tier.wasm.source", wasm_source)
    reg.register_pure_from_source(
        "artifacts.tier.native_venv.source",
        native_source,
        tier="native_venv",
    )

    assert reg.executor_of("artifacts.tier.wasm.source") == "wasm"
    assert reg.executor_of("artifacts.tier.native_venv.source") == "native_venv"
    with pytest.raises(KeyError, match="unknown pure 'artifacts.tier.missing'"):
        reg.executor_of("artifacts.tier.missing")


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_temporal_env_blocks_native_venv_pures_but_allows_wasm_lookup() -> None:
    from julep.execution.harness import ExecutionPolicy, _TemporalEnv
    from julep.projection import InMemoryProjection, ProjectionEmitter

    wasm_name = "artifacts.temporal.wasm.source"
    native_name = "artifacts.temporal.native_venv.source"
    wasm_source = f"""@pure({wasm_name!r})\ndef wasm_source(value):\n    return value\n"""
    native_source = (
        f"""@pure({native_name!r})\n"""
        "def native_source(value):\n"
        "    return value\n"
    )
    previous_wasm = DEFAULT_REGISTRY.pures.pop(wasm_name, None)
    previous_native = DEFAULT_REGISTRY.pures.pop(native_name, None)

    async def gate_waiter(value, cid, timeout_s):  # noqa: ANN001
        return value

    try:
        DEFAULT_REGISTRY.register_pure_from_source(wasm_name, wasm_source)
        DEFAULT_REGISTRY.register_pure_from_source(
            native_name,
            native_source,
            tier="native_venv",
        )
        env = _TemporalEnv(
            manifest={},
            emitter=ProjectionEmitter(InMemoryProjection()),
            session_id="s",
            manifest_json={},
            policy=ExecutionPolicy(),
            gate_waiter=gate_waiter,
        )

        assert callable(env.get_pure(wasm_name))
        with pytest.raises(JulepError, match="native-tier"):
            env.get_pure(native_name)
    finally:
        DEFAULT_REGISTRY.pures.pop(wasm_name, None)
        DEFAULT_REGISTRY.pures.pop(native_name, None)
        if previous_wasm is not None:
            DEFAULT_REGISTRY.pures[wasm_name] = previous_wasm
        if previous_native is not None:
            DEFAULT_REGISTRY.pures[native_name] = previous_native


def test_register_pure_from_source_does_not_exec_module_level_code_on_host() -> None:
    """SECURITY: a bundle's module-level code must NOT run on the host at
    registration. The wasm tier is fail-closed; even signed bundle source runs
    only inside the wasm sandbox, never in the host process.

    The probe source sets a host env var at MODULE level (outside the @pure def).
    Under the old host-exec registration this var leaked onto the host; it must
    not now, on the success path OR on a path that ultimately rejects.
    """
    import os

    sentinel_env = "CAD_HOST_EXEC_PROOF"
    os.environ.pop(sentinel_env, None)

    evil = (
        "import os\n"
        f"os.environ[{sentinel_env!r}] = 'escaped-on-host'\n"
        '@pure("artifacts.evil.v1")\n'
        "def evil(value):\n"
        "    return value\n"
    )

    reg = Registry()
    try:
        # Success path: registers fine, but the module-level os.environ write must
        # NOT have executed on the host.
        entry = reg.register_pure_from_source("artifacts.evil.v1", evil)
        assert entry.executor == "wasm"
        assert sentinel_env not in os.environ, "bundle module-level code ran on the host"

        # Rejecting path (name mismatch): still must not exec module-level code.
        with pytest.raises(ValueError, match="did not register requested pure"):
            Registry().register_pure_from_source("artifacts.evil.mismatch.v1", evil)
        assert sentinel_env not in os.environ, "bundle module-level code ran on the host"
    finally:
        os.environ.pop(sentinel_env, None)


def test_from_source_pure_is_wasm_tier_and_get_pure_returns_wasm_callable() -> None:
    reg = Registry()
    source = """@pure("artifacts.tier.wasm")\ndef adder(value, **kwargs):\n    return value + 100\n"""

    entry = reg.register_pure_from_source("artifacts.tier.wasm", source)

    assert entry.executor == "wasm"
    assert entry.source == source
    # No host fn object exists: bundle source is never exec'd on the host.
    assert entry.fn is _wasm_source_only

    resolved = reg.get_pure("artifacts.tier.wasm")
    # wasm tier: get_pure returns a wasm-bound callable, NOT the sentinel fn.
    assert resolved is not entry.fn
    # ...that produces the value computed inside the wasm sandbox.
    assert resolved(1) == 101


def test_from_source_wasm_callable_matches_native_with_kwargs() -> None:
    reg = Registry()
    source = (
        """@pure("artifacts.tier.kwargs")\n"""
        """def scale(value, *, factor=1):\n"""
        """    return value * factor\n"""
    )

    entry = reg.register_pure_from_source("artifacts.tier.kwargs", source)
    resolved = reg.get_pure("artifacts.tier.kwargs")
    assert entry.fn is _wasm_source_only

    # The wasm-bound callable computes the value inside the sandbox.
    assert resolved(10, factor=3) == 30
    # called with no kwargs (interpreter's fn(value) path) must also work.
    assert resolved(10) == 10
