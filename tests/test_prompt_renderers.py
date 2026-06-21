import asyncio

import pytest

from composable_agents import HAVE_TEMPORAL
from composable_agents.dotctx import Reasoner, reasoner_from_settings, register_reasoner

if HAVE_TEMPORAL:
    from composable_agents.execution import activities as act
from composable_agents.prompt import (
    Ask,
    fragments,
    project_context,
    register_renderer,
    render_system,
    rendered_reasoner_for,
    renderer,
)


def test_reasoner_defaults_system_render_none() -> None:
    b = Reasoner(name="b", model="m", system="hi")
    assert b.system == "hi"
    assert b.system_render is None


def test_reasoner_carries_system_render() -> None:
    b = Reasoner(name="b", model="m", system_render="b.system.v1")
    assert b.system == ""
    assert b.system_render == "b.system.v1"


def test_reasoner_from_settings_parses_system_render() -> None:
    b = reasoner_from_settings({"name": "b", "model": "m", "system_render": "r1"})
    assert b.system_render == "r1"


def test_project_context_unwraps_mapping_value() -> None:
    assert project_context({"input": 1, "trace": []}) == {"input": 1, "trace": []}
    assert project_context(7) == {"value": 7}


def test_render_system_without_renderer_returns_literal() -> None:
    b = Reasoner(name="b", model="m", system="literal")
    assert render_system(b, {"value": 1}) == "literal"


def test_rendered_reasoner_for_applies_registered_renderer() -> None:
    register_renderer("greet.v2", lambda ctx: f"Hello {ctx['who']}")
    b = Reasoner(name="b", model="m", system="ignored", system_render="greet.v2")
    out = rendered_reasoner_for(b, {"who": "ada"})
    assert out.system == "Hello ada"
    assert out.system_render is None          # rendered reasoner carries no renderer
    assert out.name == "b" and out.model == "m"


def test_rendered_reasoner_for_passes_plain_reasoner_through_unchanged() -> None:
    b = Reasoner(name="b", model="m", system="literal")
    assert rendered_reasoner_for(b, {"value": 1}) is b


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_invoke_reasoner_renders_system_before_llm() -> None:
    register_renderer("inv.sys.v1", lambda ctx: f"sys:{ctx['input']}")
    register_reasoner(Reasoner(name="inv.reasoner", model="m", system_render="inv.sys.v1"))

    captured: dict = {}

    async def fake_llm(reasoner, value, principal, transcript, dispatch):
        captured["system"] = reasoner.system
        captured["system_render"] = reasoner.system_render
        return {"ok": True}

    prev = act._CTX.llm
    act._CTX.llm = fake_llm
    try:
        out = asyncio.run(act.invokeReasoner(act.InvokeReasonerInput(reasoner="inv.reasoner", value={"input": 42}, cid="c1")))
    finally:
        act._CTX.llm = prev

    assert out == {"ok": True}
    assert captured["system"] == "sys:42"
    assert captured["system_render"] is None


def test_fragment_backed_renderer_end_to_end() -> None:
    @renderer("research.system.v1")
    def research_system(ctx):
        return fragments(
            "You are a careful research agent.\n",
            Ask("persona", fmt=lambda p: f"Persona: {p}"),
        ).render(ctx)

    b = Reasoner(name="researcher", model="m", system_render="research.system.v1")
    out = rendered_reasoner_for(b, {"persona": "skeptic"})
    assert out.system == "You are a careful research agent.\nPersona: skeptic"
