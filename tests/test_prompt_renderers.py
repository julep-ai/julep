from composable_agents.dotctx import Brain, brain_from_settings


def test_brain_defaults_system_render_none() -> None:
    b = Brain(name="b", model="m", system="hi")
    assert b.system == "hi"
    assert b.system_render is None


def test_brain_carries_system_render() -> None:
    b = Brain(name="b", model="m", system_render="b.system.v1")
    assert b.system == ""
    assert b.system_render == "b.system.v1"


def test_brain_from_settings_parses_system_render() -> None:
    b = brain_from_settings({"name": "b", "model": "m", "system_render": "r1"})
    assert b.system_render == "r1"


from composable_agents.dotctx import Brain
from composable_agents.prompt import project_context, render_system, rendered_brain_for, register_renderer


def test_project_context_unwraps_mapping_value() -> None:
    assert project_context({"input": 1, "trace": []}) == {"input": 1, "trace": []}
    assert project_context(7) == {"value": 7}


def test_render_system_without_renderer_returns_literal() -> None:
    b = Brain(name="b", model="m", system="literal")
    assert render_system(b, {"value": 1}) == "literal"


def test_rendered_brain_for_applies_registered_renderer() -> None:
    register_renderer("greet.v2", lambda ctx: f"Hello {ctx['who']}")
    b = Brain(name="b", model="m", system="ignored", system_render="greet.v2")
    out = rendered_brain_for(b, {"who": "ada"})
    assert out.system == "Hello ada"
    assert out.system_render is None          # rendered brain carries no renderer
    assert out.name == "b" and out.model == "m"


def test_rendered_brain_for_passes_plain_brain_through_unchanged() -> None:
    b = Brain(name="b", model="m", system="literal")
    assert rendered_brain_for(b, {"value": 1}) is b
