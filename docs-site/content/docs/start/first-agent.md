---
title: "Your First Agent"
description: "Build and run a local composable-agents Agent in minutes — no API key required."
---

Save and run this as a normal Python script:

```python
from composable_agents import Agent, tool


@tool(effect="read", idempotent=True)
def search_kb(ticket: str) -> dict[str, str]:
    return {"queue": "billing", "summary": "Use the duplicate-charge runbook."}


def scripted_llm(_reasoner: str, payload: dict) -> dict:
    if not payload["trace"]:
        return {"tool": "search_kb", "input": payload["input"]}
    hit = payload["input"]
    return {"output": {"queue": hit["queue"], "reply": hit["summary"]}}


agent = Agent(reasoner="claude-sonnet-4-6", tools=[search_kb], llm=scripted_llm)
result = agent.run("Customer was charged twice and renewal access is blocked.")

print(result["status"])
print(result["output"])
print(result["trace"])
```

`@tool(...)` turns a Python callable into a native tool capability. `effect=` must be one of `"read"`, `"write"`, `"external"`, or `"dangerous"`; the effect is used by capability enforcement and approval checks. `idempotent=True` marks the native tool as retry-safe for repeated execution with the same input. The decorator infers JSON-ish input and output schemas from type hints.

`llm=` is a controller callable with the shape `(reasoner, payload) -> reply`. In the local facade, `reasoner` is the agent's **reasoner name** — its registry key (the `name=` you passed, or a deterministic default derived from the config), not the model string. Scripted callers ignore it (as `scripted_llm` does above); a real caller resolves it through the reasoner registry (`get_reasoner(name)`) to recover that reasoner's system prompt and reply schema. `payload` contains the current `"input"` and the append-only `"trace"`. For a tool call, return `{"tool": "<granted tool name>", "input": value}`. To finish, return `{"output": value}`. The agent loop accepts a closed reply vocabulary; the other reply forms are used by more advanced subflow and escalation cases.

`Agent(...)` freezes the controller identity around `reasoner`, `tools`, optional `name`, optional `llm`, `budget_cost`, `max_rounds`, `instructions`, and `mode`. The local `.run(...)` method executes the same bounded app loop through the in-memory interpreter. Use `await agent.arun(...)` instead when already inside an event loop.

## Reading the result

`Agent.run(...)` returns `Result`, a dict subclass with attribute accessors:

<!-- ca:doctest skip -->
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

## The keyless default reasoner

If you omit `llm=`, the facade does not call a model. It uses a keyless default reasoner that emits a `RuntimeWarning` once and returns the input unprocessed:

```python
from composable_agents import Agent

agent = Agent(reasoner="claude-sonnet-4-6")
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


async def llm_controller(reasoner_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    # `reasoner_name` is the registry key; `get_reasoner(reasoner_name)` recovers the
    # reasoner's model, system prompt, and reply schema to build the request.
    ...


agent = Agent(
    reasoner="claude-sonnet-4-6",
    tools=[search_kb],
    llm=llm_controller,
    max_rounds=8,
)
```

The framework constrains the controller through the reply schema and the granted tool set; it does not prescribe the model client.

For a batteries-included multi-provider controller, install the `providers` extra and use `make_local_reasoner` from `composable_agents.execution.llm`. It routes a `provider:model` prefix on `reasoner=` (e.g. `"openai:gpt-4o"`, `"gemini:gemini-2.5-flash"`) through [any-llm](https://github.com/mozilla-ai/any-llm), so the same agent runs on any supported provider:

<!-- ca:doctest skip -->
```python
# pip install 'composable-agents[providers]' 'any-llm-sdk[anthropic,openai]'
from composable_agents import Agent, tool
from composable_agents.execution.llm import make_local_reasoner

agent = Agent(reasoner="openai:gpt-4o", tools=[search_kb], llm=make_local_reasoner())
```

A bare model string (no `provider:` prefix) falls back to the default provider (anthropic). See [`examples/multi_provider_agent.py`](https://github.com/julep-ai/julep-v2/blob/main/examples/multi_provider_agent.py) for a runnable, key-guarded loop across several providers.

## Dev mode while iterating

Strict mode is the default. `Agent(..., mode="dev")` and `deploy(..., mode="dev")` keep compiling or running locally while retaining the diagnostics that production would block on.

```python
from composable_agents import Agent, tool


@tool(effect="dangerous", idempotent=False)
def refund_card(account_id: str) -> dict[str, str]:
    return {"status": "refunded", "account_id": account_id}


def scripted_llm(_reasoner: str, payload: dict) -> dict:
    if not payload["trace"]:
        return {"tool": "refund_card", "input": payload["input"]}
    return {"output": payload["input"]}


agent = Agent(
    reasoner="scripted-refund",
    tools=[refund_card],
    llm=scripted_llm,
    mode="dev",
)

deployment = agent.deployment()
print(deployment.prod_gap_summary())
print(agent.run("acct-123").prod_gap)
```

`deployment.prod_gap_summary()` gives the strict-production summary. Temporal stays prod-strict: `Deployment.run(...)` rejects dev-mode deployments, and `Agent.deploy(...)` uses the strict deployment path.

<!-- ported-by ca-docs-site: start/first-agent -->
