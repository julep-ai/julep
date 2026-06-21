"""Drive the local agent loop against *any* provider via any-llm.

Unlike the keyless cookbook examples (which script the reasoner in-process) and the
Anthropic-only CMA example (which runs the loop on Anthropic's hosted service),
here a real provider model drives the local think -> call -> observe loop through
the any-llm-backed ``LlmCaller`` (``composable_agents.execution.llm``), while the
framework stays the capability and budget authority: it grants only the declared
``@tool`` surface, dispatches each requested call locally, and charges the same
cost model / trace as every other backend.

The provider is chosen by a ``provider:model`` prefix on the model string; a bare
slug would fall back to the default provider (anthropic).

Prereqs:

    pip install 'composable-agents[providers]' 'any-llm-sdk[anthropic,openai]'
    export ANTHROPIC_API_KEY=sk-ant-...   # for the anthropic:... model
    export OPENAI_API_KEY=sk-...          # for the openai:... model

Then:

    .venv/bin/python examples/multi_provider_agent.py

A model whose API key is absent is skipped, so this no-ops cleanly with no keys.
``cost`` is in the framework's abstract units (think=2.0, tool=1.0 by default),
not dollars.
"""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any

from composable_agents import Agent, tool
from composable_agents.execution.llm import make_local_reasoner

QUESTION = "What is the weather in Tokyo right now, in Fahrenheit?"

# (model string, env var that must be present to run it). Mixes providers that
# support native structured output (anthropic, openai, groq) with one that takes
# the prompt-injected-JSON fallback path (gemini), so a single run exercises both
# strategies in execution/llm.py.
MODELS: list[tuple[str, str]] = [
    ("anthropic:claude-haiku-4-5-20251001", "ANTHROPIC_API_KEY"),
    ("openai:gpt-4o-mini", "OPENAI_API_KEY"),
    ("groq:llama-3.3-70b-versatile", "GROQ_API_KEY"),
    ("gemini:gemini-2.5-flash", "GEMINI_API_KEY"),
]


def _arg(payload: Any, key: str) -> Any:
    """Recover a single tool argument from the model's raw ``input``.

    The local loop tools a tool exactly the ``input`` value the model produced,
    and providers differ in habit: some send the bare argument (``"Tokyo"``),
    others wrap it in a named object (``{"city": "Tokyo"}``). Accept either, and
    fall back to the sole value of a one-key object whose key we didn't predict.
    """
    if isinstance(payload, dict):
        if key in payload:
            return payload[key]
        return next(iter(payload.values()), payload)
    return payload


@tool(effect="read", idempotent=True)
def get_weather(payload: Any) -> dict[str, Any]:
    """Get the current weather for a city (celsius + conditions)."""
    city = _arg(payload, "city")
    table = {
        "Tokyo": {"celsius": 22, "conditions": "partly cloudy"},
        "Paris": {"celsius": 18, "conditions": "sunny"},
    }
    return table.get(city, {"celsius": 20, "conditions": "clear"})


@tool(effect="read", idempotent=True)
def to_fahrenheit(payload: Any) -> float:
    """Convert a Celsius temperature to Fahrenheit."""
    return float(_arg(payload, "celsius")) * 9 / 5 + 32


def build(model: str) -> Agent:
    slug = re.sub(r"[^a-z0-9]+", "_", model.lower())
    return Agent(
        model,
        tools=[get_weather, to_fahrenheit],
        name=f"multi_provider_{slug}",
        instructions=(
            "You are a weather agent. Goal: report a city's current temperature "
            "in Fahrenheit.\n"
            "Each turn you receive a JSON object with two keys:\n"
            "  - 'input': the result of your last action (initially the user's "
            "question).\n"
            "  - 'trace': the tools you have already called this run, in order.\n"
            "Reply with EXACTLY one JSON object and nothing else:\n"
            "  - {\"tool\": <name>, \"input\": <arg>} to call a tool, or\n"
            "  - {\"output\": <one-sentence answer including the Fahrenheit "
            "value>} when finished.\n"
            "Procedure (do each step once; never call a tool already shown in "
            "'trace'):\n"
            "  1. trace empty -> call get_weather with the city name, e.g. "
            "{\"tool\": \"get_weather\", \"input\": \"Tokyo\"}.\n"
            "  2. trace has get_weather but not to_fahrenheit -> 'input' now holds "
            "{\"celsius\": n, ...}; call {\"tool\": \"to_fahrenheit\", \"input\": "
            "n}.\n"
            "  3. trace has to_fahrenheit -> 'input' is the Fahrenheit number; "
            "reply with {\"output\": \"...\"}."
        ),
        llm=make_local_reasoner(),
        budget_cost=30.0,
    )


async def main() -> None:
    # One event loop for the whole demo (via ``arun``): spinning a fresh
    # ``asyncio.run`` per model would finalize each provider's HTTP connections
    # after its loop had closed, printing harmless "Event loop is closed" noise.
    ran_any = False
    for model, key_env in MODELS:
        if not os.environ.get(key_env):
            print(f"- skipping {model} ({key_env} not set)")
            continue
        ran_any = True
        print(f"\n=== {model} ===")
        try:
            result = await build(model).arun(QUESTION)
        except Exception as exc:  # noqa: BLE001 - a demo: one provider's failure shouldn't hide the rest
            print(f"error:  {type(exc).__name__}: {exc}")
            continue
        print(f"status: {result.status}")
        print(f"output: {result.output}")
        print(f"cost:   {result['cost']:.2f} cost units")
        for step in result["trace"]:
            print(f"  - {step['decision']} {step['ref']} ({step['cost']:.2f})")
    if not ran_any:
        print("\nNo provider keys set; nothing to run. See the module docstring.")


if __name__ == "__main__":
    asyncio.run(main())
