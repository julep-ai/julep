"""Support ticket triage — Rung 0-1.

Shows the ``Agent`` facade as a useful keyless local loop: a scripted reasoner uses
read-only tools to search a tiny knowledge base, classify priority, and finish
with a triage decision. No API key, Temporal server, network, clock, or RNG is
needed.
"""

from __future__ import annotations

from typing import Any

from julep import Agent, tool


TICKET = "Customer was charged twice and says renewal access is blocked."


@tool(effect="read", idempotent=True)
def search_kb(ticket: str) -> dict[str, str]:
    if "charged twice" in ticket.lower():
        return {
            "article": "billing-retry-runbook",
            "queue": "billing",
            "summary": "Duplicate charge reports go to billing with the retry runbook.",
        }
    return {"article": "general-intake", "queue": "support", "summary": "General intake."}


@tool(effect="read", idempotent=True)
def classify_priority(kb_hit: dict[str, str]) -> dict[str, str]:
    return {
        "priority": "high" if kb_hit["queue"] == "billing" else "normal",
        "queue": kb_hit["queue"],
    }


def scripted_llm(_reasoner_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    trace_len = len(payload["trace"])
    if trace_len == 0:
        return {"tool": "search_kb", "input": payload["input"]}
    if trace_len == 1:
        return {"tool": "classify_priority", "input": payload["input"]}
    return {
        "output": {
            "priority": "high",
            "queue": "billing",
            "reply": "Use the billing retry runbook and refund duplicate charge if confirmed.",
        }
    }


def build() -> Agent:
    return Agent(
        "scripted-support-triage",
        tools=[search_kb, classify_priority],
        name="cookbook_support_triage",
        llm=scripted_llm,
        instructions="Triage a support ticket using only granted read tools.",
    )


def run_demo(ticket: str = TICKET) -> dict[str, Any]:
    return build().run(ticket)


def run_ungranted_tool_demo() -> dict[str, Any]:
    def bad_llm(_reasoner_name: str, _payload: dict[str, Any]) -> dict[str, str]:
        return {"tool": "refund_card", "input": "customer-123"}

    agent = Agent(
        "scripted-support-triage",
        tools=[search_kb],
        name="cookbook_support_triage_denied",
        llm=bad_llm,
    )
    return agent.run(TICKET)


def main() -> None:
    result = run_demo()
    print("Support triage decision:")
    print(result["output"])
    print("Trace:")
    for step in result["trace"]:
        print(f"- {step['decision']} {step['ref']} (${step['cost']:.2f})")


if __name__ == "__main__":
    main()
