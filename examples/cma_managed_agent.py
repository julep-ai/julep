"""Run a facade ``Agent``'s loop on Anthropic's hosted Claude Managed Agents.

This is the one example that talks to a live service. Unlike the keyless cookbook
examples (which drive the loop with an in-process scripted reasoner), here the
*hosted CMA model* drives the think -> call -> observe loop while the framework
stays the capability and budget authority: it projects the granted ``@tool``
surface as CMA custom tools, dispatches each requested call locally, and charges
the same cost model / trace as ``.run()`` and ``.deploy()``.

Prereqs:

    export ANTHROPIC_API_KEY=sk-ant-...      # required; without it this no-ops
    pip install 'julep[cma]'      # the httpx-based CMA adapter

Then:

    .venv/bin/python examples/cma_managed_agent.py

Note: ``spent`` is reported in the framework's abstract cost units (think=2.0,
tool=1.0 by default), not dollars — see ``Result.cost``.
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from julep import Agent, tool
from julep.execution.cma import CMAClient

MODEL = "claude-haiku-4-5-20251001"
QUESTION = "What is the weather in Tokyo right now, in Fahrenheit?"


@tool(effect="read", idempotent=True)
def get_weather(city: str) -> dict[str, Any]:
    """Get the current weather for a city (celsius + conditions)."""
    table = {
        "Tokyo": {"celsius": 22, "conditions": "partly cloudy"},
        "Paris": {"celsius": 18, "conditions": "sunny"},
    }
    return table.get(city, {"celsius": 20, "conditions": "clear"})


@tool(effect="read", idempotent=True)
def to_fahrenheit(celsius: float) -> float:
    """Convert a Celsius temperature to Fahrenheit."""
    return celsius * 9 / 5 + 32


def build() -> Agent:
    return Agent(
        MODEL,
        tools=[get_weather, to_fahrenheit],
        name="cma_weather_assistant",
        instructions=(
            "You are a weather assistant. Use get_weather to look up a city's "
            "weather, then use to_fahrenheit to convert the temperature. Finish "
            "with a one-sentence summary including the Fahrenheit value."
        ),
        budget_cost=100.0,
        max_rounds=12,
    )


def run_demo(*, client: Optional[CMAClient] = None) -> Optional[dict[str, Any]]:
    """Run the agent on live CMA, or return ``None`` when no key/client is set.

    Returning ``None`` (rather than raising) keeps the example import-safe and a
    clean no-op in environments without credentials.
    """
    if client is None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return None
        # Imported lazily so the module stays import-safe without the cma extra.
        from julep.execution.cma_anthropic import AnthropicCMAClient

        client = AnthropicCMAClient(model=MODEL)
    return dict(build().run_on_cma(QUESTION, client=client))


def main() -> None:
    result = run_demo()
    if result is None:
        print("Set ANTHROPIC_API_KEY (and install julep[cma]) to run this example.")
        return

    print("=== live CMA run result ===")
    print("status:", result["status"], "| spent:", result.get("cost"), "cost units")
    print("output:", json.dumps(result["output"]))
    print("trace:")
    for entry in result["trace"]:
        print(f"  - {entry['decision']} {entry.get('ref', '')} ({entry['cost']} cost units)")


if __name__ == "__main__":
    main()
