---
title: "Team Guide"
description: "Internal orientation for engineers authoring agents and flows."
---

The practical guide for engineers on the team building agents and flows with
`composable_agents`. It covers how we set up, the day-to-day authoring loop, and
where to go for depth. It links out rather than restating; the deep docs are the
source of truth.

- **Need syntax fast?** → [Cheat-sheet](/docs/reference/cheatsheet)
- **Hit something surprising?** → [Gotchas & FAQ](/docs/guides/gotchas)
- **Want the full surface?** → [Authoring Guide](/docs/guides/authoring-flows) · [Concepts](/docs/concepts/model) · [SPEC](/docs/internals/specification)

---

## What this is, in one breath

We build agents as **composable, durable dataflows** instead of ad-hoc loops. You
author with `@flow`: an ordinary Python function whose body wires graph steps.
Registered tools, pures, and reasoners compile to a frozen, content-hashed IR
that can crash and resume, retry safely, explain every step, and **deny any tool
the model was not explicitly granted**. The pure authoring/compile core needs no
API key and no Temporal — durable execution is an optional layer.

If you only remember one thing: **the `@flow` body runs once at *define* time to
build a graph; it does not do runtime work.** Runtime work lives in `@tool`,
`@pure`, and reasoner handlers. ([Why](/docs/concepts/model), [the trap](/docs/guides/gotchas#define-time-vs-runtime))

---

## One-time setup

```bash
git clone git@github.com:julep-ai/julep-v2.git
cd julep-v2
python -m pip install -e '.[dev]'      # authoring + tests + lint/type tooling
```

Python **3.12+** (see [`pyproject.toml`](https://github.com/julep-ai/julep-v2/blob/main/pyproject.toml)). The base install
covers everything in the authoring/compile path; durable backends and providers
are extras — see the [Cheat-sheet](/docs/reference/cheatsheet#install--extras).

Sanity check (no key, no Temporal needed):

```bash
python examples/episode_summary_flow.py
```

Before pushing, run the same gates CI runs — they're listed in
[Contributing](/docs/development/contributing#running-the-checks). The short version:
`ruff check composable_agents`, `python -m mypy composable_agents`, and
`python -m pytest -q`. ([gotcha: use `python -m pytest`, not bare `pytest`](/docs/guides/gotchas#verify-gates))

---

## The authoring loop

The inner loop is fully local, keyless, and deterministic — you should rarely
need a model or a server while iterating.

1. **Write** a `@flow`. Register tools with `@tool`, pure transforms with
   `@pure`, and reasoners with `register_reasoner(...)`.
2. **Compile + run locally** with `deploy(...).dry_run(...)`, passing fake
   reasoners so it stays deterministic and keyless.
3. **Read the result** — `dry_run(...)` returns the interpreter result, so read
   `result.value` (the `Agent` facade's `.run(...)` returns a richer `Result`
   with `.output` / `.status` / `.trace` / `.cost` instead —
   [details](/docs/reference/cheatsheet#agent-facade-controller-loop)).
4. **Read the diagnostics** — a blocked deploy prints actionable `fix:` lines
   (and the source line, with source capture on). Fix until clean.
5. **Verify** — `ruff` / `mypy` / `pytest` green.
6. **Deploy durably** (when needed) — the *same admitted artifact* runs on
   Temporal/DBOS via a worker. ([Deploy on Temporal](/docs/deploy/temporal) ·
   [DBOS](/docs/deploy/dbos) · [Kubernetes](/docs/deploy/kubernetes))

Minimal end-to-end (this is the whole loop):

```python
from typing import TypedDict
from composable_agents import Reasoner, deploy, flow, pure, register_reasoner, think, tool


@tool(effect="read", idempotent=True)
def lookup_ticket(ticket: str) -> dict[str, str]:
    return {"queue": "billing", "summary": "Use the duplicate-charge runbook."}


@pure("ticket_prompt")
def ticket_prompt(hit: dict[str, str]) -> dict[str, str]:
    return {"queue": hit["queue"], "context": hit["summary"]}


class SupportReply(TypedDict):
    reply: str


register_reasoner(Reasoner(
    name="support_reply",
    model="anthropic:claude-haiku-4-5-20251001",
    system="Draft one concise support reply as JSON.",
    reply=SupportReply,
))


@flow
def triage(ticket: str) -> dict[str, str]:
    hit = lookup_ticket(ticket, retries=2, timeout_s=5)   # append a tool step
    prompt = ticket_prompt(hit)                            # append a pure step
    answer = think("support_reply", prompt, timeout_s=10)  # append a reasoner step
    return hit | answer                                    # `|` merges records


deployment = deploy(triage, tools=[lookup_ticket], reasoners=["support_reply"])
result = deployment.dry_run(
    "Customer was charged twice.",
    reasoners={"support_reply": lambda v: {"reply": f"{v['queue']}: {v['context']}"}},
)
print(result.value)
```

Syntax for every surface (`cond`, `switch`, `each`, `reschedule`, per-step
options, `Result` fields, the `Agent` facade, the CLI) is in the
[Cheat-sheet](/docs/reference/cheatsheet).

---

## Which surface do I use?

Pick the highest-level surface that fits; drop down only when you need control.

| You're building… | Use | Where |
|---|---|---|
| A pipeline over tools/reasoners (**the default**) | `@flow` | [Authoring Guide](/docs/guides/authoring-flows) |
| An open-ended controller loop over granted tools | `Agent` facade | [Getting Started](/docs/start/first-agent) |
| Typed, type-checkable composition | `composable_agents.typed` (`as_flow`, `>>`) | [Typed Flow](/docs/internals/typed-flow-calculus) |
| Exact structural control / a new frontend | combinator kernel (`seq`, `par`, `alt`, `each`, `iter_up_to`, `stage`, `app`, `sub`) | [Concepts](/docs/concepts/model) |

All four compile to the **same frozen IR**. `@flow` is primary; the kernel is the
wire-format ground truth underneath it.

> **Use `app`/`Agent` sparingly.** An agent loop is the top of the shape lattice
> — the least statically analyzable shape. Prefer a `@flow` whose structure is
> known ahead of time. ([dispatch boundary](/docs/concepts/dispatch-boundary))

---

## The 30-second mental model

- **Three planes.** *Control* walks the frozen IR and decides what runs next;
  *Reasoners* (LLM `think` steps) and *Tools* (MCP or native) do the work as
  activities; the *Projection* plane derives an append-only trace for
  observability. The projection is **derived, never the source of durability** —
  history is.
- **Shape is inferred, not declared.** Every flow sits on the lattice
  `Pipeline < Dataflow < Branching < Feedback < Staged < Agent`. The shape bounds
  what static guarantees hold. A `sub` (child flow) is **opaque** to its parent.
- **Deny-by-default.** A flow may only call tools/reasoners it was granted.
  Irreversible (`dangerous` / approval-required) tools must sit behind
  `human_gate(...)`, or strict deploy refuses the path.
- **Freeze + replay.** Every tool is content-hashed before execution, so a
  running flow can't silently pick up a changed contract.

Full version: [Concepts](/docs/concepts/model) · [Capabilities & Safety](/docs/guides/capabilities-and-safety).

---

## Where things live

- **`composable_agents/`** — the package. Module map is in the
  [README](/docs#module-map); the pure core never imports `temporalio`
  (only `composable_agents/execution/` may).
- **`examples/`** — a ladder of runnable references, smallest first. Five run
  keyless and deterministic; see [Examples](/docs/guides/examples).
- **`docs/`** — guides (this folder); [Documentation](/docs) is the index.
- **`docs/SPEC.md`** — the normative conformance contract. When behavior is
  ambiguous, the SPEC wins.
- **`tests/golden/`** — the cross-language wire-format contract. Golden hashes
  move **only** for an intentional IR/manifest/diagnostic change, and a PR that
  moves a pin must say so ([CONTRIBUTING](/docs/development/contributing#the-golden-corpus-is-a-contract)).

---

## Getting help

1. **Diagnostics first.** A blocked deploy tells you the rule and the fix in
   `fix:` lines. Most authoring questions are answered there.
2. **[Gotchas & FAQ](/docs/guides/gotchas)** for the recurring traps (determinism,
   capabilities, dev-vs-strict, the PEP 723 footgun).
3. **The deep doc** for the surface you're on (table above).
4. **The SPEC** for "is this behavior intended?" — it defines conformance as
   tested invariants.
5. **The team** — ask in the project channel; link the failing diagnostic or the
   minimal `@flow` that reproduces it.

<!-- ported-by ca-docs-site: development/team-guide -->
