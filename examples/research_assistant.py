"""Research assistant — Rung 1-2.

Shows the ``Agent`` facade with a budget and a multi-round scripted reasoner. The
``web_search`` tool is a fixed in-memory corpus, so the run is keyless and fully
deterministic with no network, Temporal, clock, or RNG.
"""

from __future__ import annotations

from typing import Any

from julep import Agent, tool


QUESTION = "How should we keep a queue worker from double-processing jobs?"


@tool(effect="read", idempotent=True)
def web_search(query: str) -> list[dict[str, str]]:
    corpus = {
        "postgres advisory locks": [
            {
                "id": "ops-note:advisory-locks",
                "title": "Use advisory locks for one-at-a-time job ownership.",
            }
        ],
        "queue visibility timeout": [
            {
                "id": "runbook:visibility-timeouts",
                "title": "Use a visibility timeout so abandoned work can be retried.",
            }
        ],
    }
    return corpus[query]


def scripted_llm(_reasoner_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    trace_len = len(payload["trace"])
    if trace_len == 0:
        return {"tool": "web_search", "input": "postgres advisory locks"}
    if trace_len == 1:
        return {"tool": "web_search", "input": "queue visibility timeout"}
    return {
        "output": {
            "answer": "Use Postgres advisory locks; pair them with a visibility timeout.",
            "sources": ["ops-note:advisory-locks", "runbook:visibility-timeouts"],
        }
    }


def build() -> Agent:
    return Agent(
        "scripted-research-assistant",
        tools=[web_search],
        name="cookbook_research_assistant",
        llm=scripted_llm,
        budget_cost=8.0,
        instructions="Gather two fixed sources, then synthesize a short answer.",
    )


def run_demo(question: str = QUESTION) -> dict[str, Any]:
    return build().run(question)


def run_ungranted_tool_demo() -> dict[str, Any]:
    def bad_llm(_reasoner_name: str, _payload: dict[str, Any]) -> dict[str, str]:
        return {"tool": "open_browser", "input": "https://example.com"}

    agent = Agent(
        "scripted-research-assistant",
        tools=[],
        name="cookbook_research_assistant_denied",
        llm=bad_llm,
        budget_cost=8.0,
    )
    return agent.run(QUESTION)


def main() -> None:
    result = run_demo()
    print("Research answer:")
    print(result["output"]["answer"])
    print(f"Spent: {result['cost']:.2f} cost units")
    print("Trace:")
    for step in result["trace"]:
        print(f"- {step['decision']} {step['ref']} ({step['cost']:.2f} cost units)")


if __name__ == "__main__":
    main()
