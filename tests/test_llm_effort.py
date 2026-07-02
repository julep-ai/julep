import asyncio
from types import SimpleNamespace
from typing import Any

from composable_agents.dotctx import Reasoner
from composable_agents.execution.llm import complete_reasoner


def _completion(content: str = "ok") -> Any:
    msg = SimpleNamespace(content=content, parsed=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)],
                           usage=None, model="m")


def _run(reasoner: Reasoner) -> dict[str, Any]:
    seen: dict[str, Any] = {}

    async def fake_acompletion(**kwargs: Any) -> Any:
        seen.update(kwargs)
        return _completion()

    asyncio.run(complete_reasoner(reasoner, "hi", acompletion=fake_acompletion))
    return seen


def test_effort_forwarded_and_temperature_dropped() -> None:
    seen = _run(Reasoner(name="t", model="openai:gpt-4o",
                         temperature=0.2, reasoning_effort="high"))
    assert seen["reasoning_effort"] == "high"
    assert "temperature" not in seen


def test_effort_none_forwarded_temperature_kept() -> None:
    seen = _run(Reasoner(name="t", model="openai:gpt-4o",
                         temperature=0.2, reasoning_effort="none"))
    assert seen["reasoning_effort"] == "none"
    assert seen["temperature"] == 0.2


def test_effort_max_clamped_to_xhigh_for_openai() -> None:
    # OpenAI's reasoning_effort has no "max" (its scale tops out at xhigh) and
    # any-llm passes the value through verbatim, so CA clamps it (codex review).
    seen = _run(Reasoner(name="t", model="openai:gpt-4o",
                         temperature=0.2, reasoning_effort="max"))
    assert seen["reasoning_effort"] == "xhigh"
    assert "temperature" not in seen


def test_effort_max_untouched_for_other_providers() -> None:
    seen = _run(Reasoner(name="t", model="anthropic:claude-x",
                         reasoning_effort="max"))
    assert seen["reasoning_effort"] == "max"


def test_unset_effort_not_sent() -> None:
    seen = _run(Reasoner(name="t", model="openai:gpt-4o", temperature=0.2))
    assert "reasoning_effort" not in seen
    assert seen["temperature"] == 0.2
