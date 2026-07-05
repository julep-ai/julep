# tests/test_renderer_registry.py
import pytest
from julep.registry import Registry


def _r(ctx):  # a renderer: Context -> str
    return f"hi {ctx.get('who','')}"


def test_register_and_get_renderer() -> None:
    reg = Registry()
    reg.register_renderer("greet.v1", _r)
    assert reg.get_renderer("greet.v1")({"who": "ada"}) == "hi ada"


def test_renderer_source_hash_is_pinned_and_stable() -> None:
    reg = Registry()
    reg.register_renderer("greet.v1", _r)
    h = reg.renderer_source_hash_of("greet.v1")
    assert h.startswith("renderer:")
    reg2 = Registry()
    reg2.register_renderer("greet.v1", _r)
    assert reg2.renderer_source_hash_of("greet.v1") == h


def test_collision_on_different_fn_raises() -> None:
    reg = Registry()
    reg.register_renderer("greet.v1", _r)
    with pytest.raises(ValueError):
        reg.register_renderer("greet.v1", lambda ctx: "other")


def test_unknown_renderer_raises() -> None:
    with pytest.raises(KeyError):
        Registry().get_renderer("nope")
