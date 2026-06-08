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
