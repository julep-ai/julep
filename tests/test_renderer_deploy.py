from composable_agents.deploy import _reasoner_identity, _renderer_source_hashes
from composable_agents.dotctx import Reasoner
from composable_agents.registry import DEFAULT_REGISTRY
from composable_agents.prompt import register_renderer
from composable_agents.dsl import think


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
