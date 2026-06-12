from __future__ import annotations

import hashlib
import inspect

import pytest

from composable_agents.purity import register_pure_from_source
from composable_agents.registry import DEFAULT_REGISTRY, Registry, _text_hash


def _expected_hash(source: str) -> str:
    return f"pure:{hashlib.sha256(source.encode('utf-8')).hexdigest()[:16]}"


def test_register_pure_from_source_round_trip() -> None:
    reg = Registry()
    source = """@pure("cas.add_one")\ndef add_one(value):\n    return value + 1\n"""

    entry = reg.register_pure_from_source("cas.add_one", source)

    assert entry.name == "cas.add_one"
    assert reg.source_hash_of("cas.add_one") == _expected_hash(source)
    assert reg.get_pure("cas.add_one")(41) == 42


def test_register_pure_from_source_keeps_shipped_text_inspectable() -> None:
    reg = Registry()
    source = """@pure("cas.echo")\ndef echo(value):\n    return {"value": value}\n"""

    entry = reg.register_pure_from_source("cas.echo", source)

    assert inspect.getsource(entry.fn) == source


def test_register_pure_from_source_same_source_is_noop() -> None:
    reg = Registry()
    source = """@pure("cas.same")\ndef same(value):\n    return value\n"""

    first = reg.register_pure_from_source("cas.same", source)
    second = reg.register_pure_from_source("cas.same", source)

    assert second is first


def test_register_pure_from_source_agrees_with_baked_registration() -> None:
    reg = Registry()

    def baked(value: int) -> int:
        return value * 2

    first = reg.register_pure("cas.baked", baked)
    source = inspect.getsource(baked)

    second = reg.register_pure_from_source("cas.baked", source)

    assert second is first


def test_register_pure_from_source_collision_names_both_hashes_and_keeps_original() -> None:
    reg = Registry()
    original = """@pure("cas.collision")\ndef collision(value):\n    return value + 1\n"""
    changed = """@pure("cas.collision")\ndef collision(value):\n    return value + 2\n"""
    first = reg.register_pure_from_source("cas.collision", original)

    with pytest.raises(ValueError) as excinfo:
        reg.register_pure_from_source("cas.collision", changed)

    message = str(excinfo.value)
    assert "cas.collision" in message
    assert _expected_hash(original) in message
    assert _expected_hash(changed) in message
    assert reg.pures["cas.collision"] is first
    assert reg.get_pure("cas.collision")(1) == 2


def test_plain_exec_register_pure_uses_wrong_qualname_fallback_but_source_api_does_not() -> None:
    source = """@pure("cas.qualname")\ndef qualname(value):\n    return value\n"""

    plain = Registry()

    def pure(name: str):
        def deco(fn):
            plain.register_pure(name, fn)
            return fn

        return deco

    exec(source, {"__name__": "<module>", "pure": pure})

    expected_wrong = _text_hash("<module>.qualname")
    assert plain.source_hash_of("cas.qualname") == expected_wrong

    via_source = Registry()
    via_source.register_pure_from_source("cas.qualname", source)
    assert via_source.source_hash_of("cas.qualname") == _expected_hash(source)


def test_default_registry_register_pure_from_source_shim_forwards() -> None:
    name = "cas.default.forward"
    source = """@pure("cas.default.forward")\ndef default_forward(value):\n    return value * 3\n"""

    try:
        entry = register_pure_from_source(name, source)
        assert DEFAULT_REGISTRY.source_hash_of(name) == _expected_hash(source)
        assert DEFAULT_REGISTRY.get_pure(name)(7) == 21
        assert entry is DEFAULT_REGISTRY.pures[name]
    finally:
        DEFAULT_REGISTRY.pures.pop(name, None)


def test_register_pure_from_source_decorator_name_mismatch_errors_clearly() -> None:
    reg = Registry()
    source = """@pure("cas.actual")\ndef actual(value):\n    return value\n"""

    with pytest.raises(ValueError, match="did not register requested pure 'cas.expected'"):
        reg.register_pure_from_source("cas.expected", source)

    assert not reg.is_registered("cas.expected")


def test_register_pure_from_source_failure_restores_pures_in_place() -> None:
    reg = Registry()

    def keep(value: int) -> int:
        return value + 1

    existing = reg.register_pure("cas.keep", keep)
    pures_alias = reg.pures
    source = """@pure("cas.actual")\ndef actual(value):\n    return value\n"""

    with pytest.raises(ValueError, match="did not register requested pure 'cas.expected'"):
        reg.register_pure_from_source("cas.expected", source)

    assert reg.pures is pures_alias
    assert pures_alias["cas.keep"] is existing
    assert "cas.actual" not in pures_alias
    assert "cas.expected" not in pures_alias


def test_register_pure_from_source_newline_less_source_errors_clearly() -> None:
    reg = Registry()
    source = """@pure("cas.no_newline")\ndef no_newline(value):\n    return value"""

    with pytest.raises(ValueError, match="source hash mismatch"):
        reg.register_pure_from_source("cas.no_newline", source)
