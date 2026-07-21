---
title: "Your First Flow"
description: "Write a typed @flow, declare a tool, pure, and reasoner, deploy it, and run it locally with dry_run — no API key needed."
---

## What you'll build

A support-triage flow that looks up a ticket, formats a prompt, and calls a reasoner to draft a reply — then runs the whole thing locally without a real LLM or a Temporal server.

You need Python 3.12 or newer. No API key. No running infrastructure.

## Install

```bash
pip install --pre julep
```

`julep.HAVE_TEMPORAL` tells you at runtime whether the durable execution layer is also available. The package compiles and runs flows either way.

## The complete example

Save this as `quickstart_flow.py` and run it with `python quickstart_flow.py`.

<!-- julep:doctest expect-output -->
```python
from typing import TypedDict

from julep import Reasoner, deploy, flow, pure, think, tool


class SupportReply(TypedDict):
    reply: str


@tool(effect="read", idempotent=True)
def lookup_ticket(ticket: str) -> dict[str, str]:
    return {
        "ticket": ticket,
        "queue": "billing",
        "summary": "Use the duplicate-charge runbook.",
    }


@pure("ticket_prompt")
def ticket_prompt(hit: dict[str, str]) -> dict[str, str]:
    return {"queue": hit["queue"], "context": hit["summary"]}


SUPPORT_REPLY = Reasoner(
    name="support_reply",
    model="anthropic:claude-haiku-4-5-20251001",
    system="Draft one concise support reply as JSON.",
    reply=SupportReply,
)


@flow
def triage(ticket: str) -> dict[str, str]:
    hit = lookup_ticket(ticket, retries=2, timeout_s=5)
    prompt = ticket_prompt(hit)
    answer = think(SUPPORT_REPLY, prompt, timeout_s=10)
    return hit | answer


def fake_support_reply(value: dict[str, str]) -> SupportReply:
    return {"reply": f"{value['queue']}: {value['context']}"}


deployment = deploy(triage, tools=[lookup_ticket], reasoners=[SUPPORT_REPLY])
result = deployment.dry_run(
    "Customer was charged twice.",
    reasoners={"support_reply": fake_support_reply},
)

print(result.value)
print(deployment.surface_shape.value)
```

```text
{'ticket': 'Customer was charged twice.', 'queue': 'billing', 'summary': 'Use the duplicate-charge runbook.', 'reply': 'billing: Use the duplicate-charge runbook.'}
Dataflow
```

## How it works

### `@tool` — side-effecting callables

<!-- julep:doctest skip -->
```python
@tool(effect="read", idempotent=True)
def lookup_ticket(ticket: str) -> dict[str, str]:
    ...
```

`@tool` wraps a Python callable so it can be called inside a `@flow`. Type hints become the tool's input/output schema. `effect=` is one of `"read"`, `"write"`, `"external"`, or `"dangerous"` — this controls ordering and retry policy in the compiled graph. `idempotent=True` lets the tool participate in race patterns and receive a stable idempotency key from the runtime.

### `@pure` — deterministic functions

<!-- julep:doctest skip -->
```python
@pure("ticket_prompt")
def ticket_prompt(hit: dict[str, str]) -> dict[str, str]:
    return {"queue": hit["queue"], "context": hit["summary"]}
```

A pure is a deterministic, side-effect-free function that runs on the workflow side (not as a tool activity). It must not do IO, read clocks, or touch mutable globals. At deploy time its source is hashed; if the source drifts between deploy and execution the workflow refuses to run.

### `Reasoner` — named LLM steps

<!-- julep:doctest skip -->
```python
SUPPORT_REPLY = Reasoner(
    name="support_reply",
    model="anthropic:claude-haiku-4-5-20251001",
    system="Draft one concise support reply as JSON.",
    reply=SupportReply,
)
```

A `Reasoner` names an LLM configuration. Declare it as an object, call it inside a flow with `think(SUPPORT_REPLY, handle)`, and include it in `deploy(..., reasoners=[SUPPORT_REPLY])`. The name, model, and system prompt are frozen into the deployment artifact; the actual LLM call is an activity that runs outside the control plane.

### `@flow` — the authoring surface

<!-- julep:doctest skip -->
```python
@flow
def triage(ticket: str) -> dict[str, str]:
    hit = lookup_ticket(ticket, retries=2, timeout_s=5)
    prompt = ticket_prompt(hit)
    answer = think(SUPPORT_REPLY, prompt, timeout_s=10)
    return hit | answer
```

`@flow` runs `triage(...)` **once at definition time** with `Handle` values — placeholder objects that represent future data. Every call to a registered tool, pure, or `think(...)` appends a step to a DAG instead of doing real work. `hit | answer` lowers to `std.merge` (later keys win). `retries=` and `timeout_s=` are step-level policy that travels with the frozen graph.

You cannot branch or iterate on a `Handle` with plain Python:

<!-- julep:doctest skip -->
```python
# These are define-time errors:
if hit:          # use cond(...) instead
    ...
for item in xs:  # use each(...) instead
    ...
```

Use the provided control helpers — `cond(pred, subject, then=..., orelse=...)` for binary branches, `switch(...)` for multi-way, `each(body, items, ...)` for fan-out.

### `deploy(...)` — freeze and admit

<!-- julep:doctest skip -->
```python
deployment = deploy(triage, tools=[lookup_ticket], reasoners=[SUPPORT_REPLY])
```

`deploy(...)` runs four static gates in order: **freeze** (bind every tool call to a content hash), **validate** (well-formedness and schema edges), **capability enforcement** (the flow may only use granted tools and reasoners), and **race admission** (every branch of a race must be safe to duplicate). A blocking diagnostic aborts by default. Pass `mode="dev"` to get warnings instead of errors while iterating locally.

After deploy you can inspect the artifact:

<!-- julep:doctest skip -->
```python
deployment.surface_shape    # inferred shape: Pipeline, Dataflow, Branching, …
deployment.diagnostics      # any non-blocking warnings
deployment.prod_gap_summary()  # what strict production deploy would block
```

### `dry_run(...)` — local execution

<!-- julep:doctest skip -->
```python
result = deployment.dry_run(
    "Customer was charged twice.",
    reasoners={"support_reply": fake_support_reply},
)
print(result.value)
```

`dry_run(...)` executes the frozen graph locally using the same deterministic interpreter that runs on Temporal. Pass `reasoners=` to substitute fake callables for any registered reasoners — the fake receives the value the flow would send to the LLM and returns the model-shaped response. No API key is required.

`result.value` is the merged output record from the flow's return expression.

## What the shape tells you

<!-- julep:doctest skip -->
```python
print(deployment.surface_shape.value)  # "Dataflow"
```

Every flow has an inferred shape on the lattice `Pipeline < Dataflow < Branching < Feedback < Staged < Agent`. A `Pipeline` is fully analyzable; an `Agent` is an open-ended controller at the top. The shape bounds what static guarantees hold and is computed from structure, not declared.

## Where to go next

- [Authoring guide](/docs/guides/authoring-flows) — the full determinism contract, branching, fan-out, captures, and define-time error reference.
- [Concepts](/docs/concepts/model) — frozen IR, the shape lattice, capabilities, and the projection plane.
- [Capabilities and safety](/docs/guides/capabilities-and-safety) — grants, approval gates, and race admission in detail.
- [Using the CLI](/docs/guides/using-the-cli) — `julep run`, `julep lint`, `julep deploy`, and the cross-agent graph.
- [Deploy to Temporal](/docs/deploy/temporal) — durable execution and worker setup.
- Larger examples: [`examples/episode_summary_flow.py`](https://github.com/julep-ai/julep-v2/blob/main/examples/episode_summary_flow.py) and [`examples/cluster_labeling_flow.py`](https://github.com/julep-ai/julep-v2/blob/main/examples/cluster_labeling_flow.py).

<!-- ported-by julep-docs-site: start/first-flow -->
