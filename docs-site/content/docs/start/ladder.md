---
title: "On-Ramp Ladder"
description: "Build a returns-triage flow one surface at a time: tool, pure, reasoner, branching, fan-out, and deploy inspection."
---

This ladder builds a returns-triage workflow one authoring surface at a time.
Every step is a complete runnable program and uses `dry_run(...)`, so it needs
no provider key and no running infrastructure.

## 1. A Tool

Start with a native `@tool` that returns canned data, then call it from a
one-line `@flow`.

<!-- ca:doctest expect-output -->
```python
from composable_agents import deploy, flow, tool


@tool(effect="read", idempotent=True)
def lookup_return(order_id: str) -> dict[str, object]:
    return {
        "order_id": order_id,
        "action": "review",
        "reason": "damaged",
        "items": ["coat", "scarf"],
    }


@flow
def triage(order_id: str) -> dict[str, object]:
    return lookup_return(order_id)


deployment = deploy(triage, tools=[lookup_return])
print(deployment.dry_run("ret-100").value)
```

```text
{'order_id': 'ret-100', 'action': 'review', 'reason': 'damaged', 'items': ['coat', 'scarf']}
```

## 2. A Pure

Add a deterministic `@pure` to reshape tool output. `hit["reason"]` plucks a
field from the record handle, and `hit | decision` merges records.

<!-- ca:doctest expect-output -->
```python
from composable_agents import deploy, flow, pure, tool


@tool(effect="read", idempotent=True)
def lookup_return(order_id: str) -> dict[str, object]:
    return {
        "order_id": order_id,
        "action": "review",
        "reason": "damaged",
        "items": ["coat", "scarf"],
    }


@pure("ladder_reason_to_decision")
def reason_to_decision(reason: str) -> dict[str, str]:
    return {"decision": "inspect" if reason == "damaged" else "auto"}


@flow
def triage(order_id: str) -> dict[str, object]:
    hit = lookup_return(order_id)
    reason = hit["reason"]
    decision = reason_to_decision(reason)
    return hit | decision


deployment = deploy(triage, tools=[lookup_return])
print(deployment.dry_run("ret-100").value)
```

```text
{'order_id': 'ret-100', 'action': 'review', 'reason': 'damaged', 'items': ['coat', 'scarf'], 'decision': 'inspect'}
```

## 3. A Reasoner

Declare a `Reasoner(...)` object, pass it to `think(reasoner, prompt)`, and use
a fake reasoner in `dry_run(...)` for keyless local execution.

<!-- ca:doctest expect-output -->
```python
from typing import TypedDict

from composable_agents import Reasoner, deploy, flow, pure, think, tool


class ReturnDecision(TypedDict):
    decision: str
    note: str


@tool(effect="read", idempotent=True)
def lookup_return(order_id: str) -> dict[str, object]:
    return {
        "order_id": order_id,
        "action": "review",
        "reason": "damaged",
        "items": ["coat", "scarf"],
    }


@pure("ladder_decision_prompt")
def decision_prompt(hit: dict[str, object]) -> dict[str, object]:
    return {"order_id": hit["order_id"], "reason": hit["reason"]}


RETURN_DECIDER = Reasoner(
    name="return_decider",
    model="anthropic:claude-haiku-4-5-20251001",
    system="Classify the return request as JSON.",
    reply=ReturnDecision,
)


@flow
def triage(order_id: str) -> dict[str, object]:
    hit = lookup_return(order_id)
    prompt = decision_prompt(hit)
    answer = think(RETURN_DECIDER, prompt)
    return prompt | answer


def fake_return_decider(value: dict[str, object]) -> ReturnDecision:
    return {"decision": "inspect", "note": f"Review {value['reason']} return."}


deployment = deploy(triage, tools=[lookup_return], reasoners=[RETURN_DECIDER])
print(
    deployment.dry_run(
        "ret-100",
        reasoners={"return_decider": fake_return_decider},
    ).value
)
```

```text
{'order_id': 'ret-100', 'reason': 'damaged', 'decision': 'inspect', 'note': 'Review damaged return.'}
```

## 4. Branching

Use `switch_on(subject, key="action", cases={...})` to route on one record
field. It is sugar over `switch`; case names match `str(subject["action"])`.

<!-- ca:doctest expect-output -->
```python
from composable_agents import deploy, flow, pure, switch_on


@pure("ladder_mark_review")
def mark_review(req: dict[str, object]) -> dict[str, object]:
    return {"route": "manual-review", "order_id": req["order_id"]}


@pure("ladder_mark_auto")
def mark_auto(req: dict[str, object]) -> dict[str, object]:
    return {"route": "auto-approve", "order_id": req["order_id"]}


@flow
def review(req: dict[str, object]) -> dict[str, object]:
    return mark_review(req)


@flow
def auto(req: dict[str, object]) -> dict[str, object]:
    return mark_auto(req)


@flow
def route(req: dict[str, object]) -> dict[str, object]:
    return switch_on(req, key="action", cases={"review": review, "auto": auto}, default=auto)


deployment = deploy(route, tools=[])
print(deployment.dry_run({"order_id": "ret-100", "action": "review"}).value)
print(deployment.dry_run({"order_id": "ret-101", "action": "auto"}).value)
```

```text
{'route': 'manual-review', 'order_id': 'ret-100'}
{'route': 'auto-approve', 'order_id': 'ret-101'}
```

## 5. Fan-Out

Use `each(body, items, max_parallel=...)` over a runtime list. The body item
parameter is positional; enclosing values are explicit captures.

<!-- ca:doctest expect-output -->
```python
from composable_agents import deploy, each, flow, pure


@pure("ladder_label_return")
def label_return(item: dict[str, object]) -> dict[str, object]:
    return {"order_id": item["order_id"], "label": f"{item['reason']}-return"}


@flow
def label_one(item: dict[str, object]) -> dict[str, object]:
    return label_return(item)


@flow
def label_batch(batch: dict[str, object]) -> list[dict[str, object]]:
    returns = batch["returns"]
    return each(label_one, returns, max_parallel=2)


deployment = deploy(label_batch, tools=[])
print(
    deployment.dry_run(
        {
            "returns": [
                {"order_id": "ret-100", "reason": "damaged"},
                {"order_id": "ret-101", "reason": "wrong-size"},
            ]
        }
    ).value
)
```

```text
[{'order_id': 'ret-100', 'label': 'damaged-return'}, {'order_id': 'ret-101', 'label': 'wrong-size-return'}]
```

## 6. Deploy and Inspect

`deploy(...)` freezes the flow and exposes the shape, strict-production gap
summary, and the same keyless `dry_run(...)` path used above.

<!-- ca:doctest expect-output -->
```python
from typing import TypedDict

from composable_agents import Reasoner, deploy, flow, pure, switch_on, think, tool


class ReturnDecision(TypedDict):
    decision: str
    note: str


@tool(effect="read", idempotent=True)
def lookup_return(order_id: str) -> dict[str, object]:
    return {
        "order_id": order_id,
        "action": "review",
        "reason": "damaged",
    }


@pure("ladder_review_prompt")
def review_prompt(req: dict[str, object]) -> dict[str, object]:
    return {"order_id": req["order_id"], "reason": req["reason"]}


@pure("ladder_auto_decision")
def auto_decision(req: dict[str, object]) -> dict[str, object]:
    return {"decision": "auto-approve", "note": f"Auto-approved {req['order_id']}."}


RETURN_REVIEWER = Reasoner(
    name="return_reviewer",
    model="anthropic:claude-haiku-4-5-20251001",
    system="Review a return request as JSON.",
    reply=ReturnDecision,
)


@flow
def review(req: dict[str, object]) -> dict[str, object]:
    prompt = review_prompt(req)
    answer = think(RETURN_REVIEWER, prompt)
    return prompt | answer


@flow
def auto(req: dict[str, object]) -> dict[str, object]:
    return auto_decision(req)


@flow
def triage(order_id: str) -> dict[str, object]:
    req = lookup_return(order_id, name="req")
    return switch_on(req, key="action", cases={"review": review, "auto": auto}, default=auto)


def fake_return_reviewer(value: dict[str, object]) -> ReturnDecision:
    return {"decision": "inspect", "note": f"Manual review for {value['reason']}."}


deployment = deploy(triage, tools=[lookup_return], reasoners=[RETURN_REVIEWER])
print(deployment.surface_shape.value)
print(deployment.prod_gap_summary())
print(
    deployment.dry_run(
        "ret-100",
        reasoners={"return_reviewer": fake_return_reviewer},
    ).value
)
```

```text
Branching
no prod gap
{'order_id': 'ret-100', 'reason': 'damaged', 'decision': 'inspect', 'note': 'Manual review for damaged.'}
```

<!-- ported-by ca-docs-site: start/ladder -->
