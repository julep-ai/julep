# Getting Started

This tutorial starts from the pure `Agent` facade and ends at the durable Temporal path. For the compact overview, read the repository [README](../README.md); this page expands the same surface without changing the model.

## Install

```bash
pip install composable-agents
pip install 'composable-agents[temporal]'
pip install 'composable-agents[temporal,http,otel]'
```

The base install covers authoring, local `Agent.run(...)`, freeze, validation, capability checks, and the in-memory interpreter. The `[temporal]` extra adds the durable runtime: Temporal workflows, activities, client helpers, and worker helpers. The `[temporal,http,otel]` install also includes native HTTP hand support and OpenTelemetry export.

The package is importable either way:

```python
import composable_agents

print(composable_agents.HAVE_TEMPORAL)
```

`composable_agents.HAVE_TEMPORAL` is `True` only when the guarded Temporal runtime imports successfully.

## Your first agent (no API key)

Save and run this as a normal Python script:

```python
from composable_agents import Agent, tool


@tool(effect="read", idempotent=True)
def search_kb(ticket: str) -> dict[str, str]:
    return {"queue": "billing", "summary": "Use the duplicate-charge runbook."}


def scripted_llm(_brain: str, payload: dict) -> dict:
    if not payload["trace"]:
        return {"tool": "search_kb", "input": payload["input"]}
    hit = payload["input"]
    return {"output": {"queue": hit["queue"], "reply": hit["summary"]}}


agent = Agent(brain="claude-sonnet-4-6", tools=[search_kb], llm=scripted_llm)
result = agent.run("Customer was charged twice and renewal access is blocked.")

print(result["status"])
print(result["output"])
print(result["trace"])
```

`@tool(...)` turns a Python callable into a native tool capability. `effect=` must be one of `"read"`, `"write"`, `"external"`, or `"dangerous"`; the effect is used by capability enforcement and approval checks. `idempotent=True` marks the native hand as retry-safe for repeated execution with the same input. The decorator infers JSON-ish input and output schemas from type hints.

`llm=` is a controller callable with the shape `(brain, payload) -> reply`. In the local facade, `brain` is the model string passed to `Agent(...)`; `payload` contains the current `"input"` and the append-only `"trace"`. For a tool call, return `{"tool": "<granted tool name>", "input": value}`. To finish, return `{"output": value}`. The agent loop accepts a closed reply vocabulary; the other reply forms are used by more advanced subflow and escalation cases.

`Agent(...)` freezes the controller identity around `brain`, `tools`, optional `name`, optional `llm`, `budget_cost`, `max_rounds`, `instructions`, and `mode`. The local `.run(...)` method executes the same bounded app loop through the in-memory interpreter. Use `await agent.arun(...)` instead when already inside an event loop.

## Reading the result

`Agent.run(...)` returns `Result`, a dict subclass with attribute accessors:

```python
result = agent.run("Customer was charged twice.")

print(result.output)
print(result.status)
print(result.ok)
print(result.trace)
print(result.cost)

print(result["status"])
print(result.get("cost"))
```

The core fields are `.output`, `.status`, `.ok`, `.trace`, `.cost`, `.rounds`, `.reason`, and `.prod_gap`. `.cost` reads the terminal dict's `cost` value. Dict compatibility is intentional, so existing code can use either `result.status` or `result["status"]`.

## The keyless default brain

If you omit `llm=`, the facade does not call a model. It uses a keyless default brain that emits a `RuntimeWarning` once and returns the input unprocessed:

```python
from composable_agents import Agent

agent = Agent(brain="claude-sonnet-4-6")
result = agent.run({"task": "classify this later"})

print(result.output)
```

For a real model, pass an async callable with the same reply contract:

```python
# Real LLM variant: wire the provider client inside this function.
from typing import Any

from composable_agents import Agent, tool


@tool(effect="read", idempotent=True)
def search_kb(ticket: str) -> dict[str, str]:
    return {"queue": "billing", "summary": "Use the duplicate-charge runbook."}


async def llm_controller(brain: str, payload: dict[str, Any]) -> dict[str, Any]:
    ...


agent = Agent(
    brain="claude-sonnet-4-6",
    tools=[search_kb],
    llm=llm_controller,
    max_rounds=8,
)
```

The framework constrains the controller through the reply schema and the granted tool set; it does not prescribe the model client.

## Dev mode while iterating

Strict mode is the default. `Agent(..., mode="dev")` and `deploy(..., mode="dev")` keep compiling or running locally while retaining the diagnostics that production would block on.

```python
from composable_agents import Agent, tool


@tool(effect="dangerous", idempotent=False)
def refund_card(account_id: str) -> dict[str, str]:
    return {"status": "refunded", "account_id": account_id}


def scripted_llm(_brain: str, payload: dict) -> dict:
    if not payload["trace"]:
        return {"tool": "refund_card", "input": payload["input"]}
    return {"output": payload["input"]}


agent = Agent(
    brain="scripted-refund",
    tools=[refund_card],
    llm=scripted_llm,
    mode="dev",
)

deployment = agent.deployment()
print(deployment.prod_gap_summary())
print(agent.run("acct-123").prod_gap)
```

`deployment.prod_gap_summary()` gives the strict-production summary. Temporal stays prod-strict: `Deployment.run(...)` rejects dev-mode deployments, and `Agent.deploy(...)` uses the strict deployment path.

## From local to durable

For a tool-only facade agent, the durable call shape is the same compiled artifact plus a Temporal client:

```python
# Temporal variant: requires `pip install 'composable-agents[temporal]'`
# and a running Temporal server.
from temporalio.client import Client

client = await Client.connect("localhost:7233")
result = await agent.deploy(
    client,
    session_id="ticket-123",
    input="Customer was charged twice.",
)
```

The worker must host the workflows, activities, tool hands, LLM callable, and capability context. See [Deploy on Temporal](deploy-temporal.md) for the full worker setup and `examples/temporal_durable_agent.py` for an end-to-end local dev-server run.

## Climb the ladder

1. Local keyless `Agent.run(...)`: [examples/support_triage.py](../examples/support_triage.py), covered in [Examples](examples.md).
2. Add a budget guard with `budget_cost`: [examples/research_assistant.py](../examples/research_assistant.py).
3. Add approval structure with `human_gate(...)`: [examples/email_approval.py](../examples/email_approval.py), with safety context in [Capabilities and Safety](capabilities-and-safety.md).
4. Run the admitted artifact durably on Temporal: [examples/temporal_durable_agent.py](../examples/temporal_durable_agent.py) and [Deploy on Temporal](deploy-temporal.md).
5. Drop to raw combinators when you need full control: `seq`, `par`, `alt`, `iter_up_to`, `stage`, `app`, `sub`, `race`, `hedge`, `quorum`; see [Concepts](concepts.md), [Typed Flow](design/typed-flow.md), and the normative [SPEC](SPEC.md).
6. Read the capstone composition last: [examples/elnino/swarm.py](../examples/elnino/swarm.py).

For repository workflow and contribution rules, see [CONTRIBUTING](../CONTRIBUTING.md). The docs index is [docs/README.md](README.md).
