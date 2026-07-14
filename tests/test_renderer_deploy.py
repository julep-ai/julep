import pytest

from julep.deploy import (
    _reasoner_identity,
    _referenced_reasoners,
    _renderer_source_hashes,
)
from julep.dotctx import Reasoner
from julep.registry import DEFAULT_REGISTRY
from julep.prompt import register_renderer
from julep.dsl import app, think


def test_reasoner_identity_omits_system_render_when_absent() -> None:
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="plain.b", model="m", system="s"))
    ident = _reasoner_identity("plain.b")
    assert "systemRender" not in ident          # no new key => golden unchanged


def test_reasoner_identity_includes_system_render_when_present() -> None:
    register_renderer("dep.r.v1", lambda ctx: "x")
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="rendered.b", model="m", system_render="dep.r.v1"))
    ident = _reasoner_identity("rendered.b")
    assert ident["systemRender"] == "dep.r.v1"


def test_renderer_source_hashes_pins_referenced_renderers() -> None:
    register_renderer("dep.r.v2", lambda ctx: "y")
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="rb2", model="m", system_render="dep.r.v2"))
    flow = think("rb2")
    hashes = _renderer_source_hashes(flow)
    assert hashes["dep.r.v2"].startswith("renderer:")


def test_referenced_reasoners_includes_app_summarizer() -> None:
    assert _referenced_reasoners(app("controller", summarizer="summarizer")) == [
        "controller",
        "summarizer",
    ]


def test_renderer_source_hashes_rejects_missing_renderer() -> None:
    reasoner_name = "deploy.missing.renderer.reasoner"
    renderer_name = "deploy.missing.renderer"
    existing_reasoner = DEFAULT_REGISTRY.reasoners.pop(reasoner_name, None)
    existing_renderer = DEFAULT_REGISTRY.renderers.pop(renderer_name, None)
    try:
        DEFAULT_REGISTRY.register_reasoner(
            Reasoner(
                name=reasoner_name,
                model="m",
                system_render=renderer_name,
            )
        )

        with pytest.raises(ValueError, match="unknown renderer"):
            _renderer_source_hashes(think(reasoner_name))
    finally:
        DEFAULT_REGISTRY.reasoners.pop(reasoner_name, None)
        if existing_reasoner is not None:
            DEFAULT_REGISTRY.reasoners[reasoner_name] = existing_reasoner
        if existing_renderer is not None:
            DEFAULT_REGISTRY.renderers[renderer_name] = existing_renderer
