from composable_agents.deploy import _brain_identity, _renderer_source_hashes
from composable_agents.dotctx import Brain, register_brain
from composable_agents.prompt import register_renderer
from composable_agents.dsl import think


def test_brain_identity_omits_system_render_when_absent() -> None:
    register_brain(Brain(name="plain.b", model="m", system="s"))
    ident = _brain_identity("plain.b")
    assert "systemRender" not in ident          # no new key => golden unchanged


def test_brain_identity_includes_system_render_when_present() -> None:
    register_renderer("dep.r.v1", lambda ctx: "x")
    register_brain(Brain(name="rendered.b", model="m", system_render="dep.r.v1"))
    ident = _brain_identity("rendered.b")
    assert ident["systemRender"] == "dep.r.v1"


def test_renderer_source_hashes_pins_referenced_renderers() -> None:
    register_renderer("dep.r.v2", lambda ctx: "y")
    register_brain(Brain(name="rb2", model="m", system_render="dep.r.v2"))
    flow = think("rb2")
    hashes = _renderer_source_hashes(flow)
    assert hashes["dep.r.v2"].startswith("renderer:")
