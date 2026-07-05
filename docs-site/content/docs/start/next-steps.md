---
title: "Next Steps"
description: "A signpost through the julep ladder, from a keyless local agent to the capstone swarm example."
---

The examples below form a ladder. Each rung teaches one concept and is runnable on its own.

## The ladder

### 1. Local keyless agent

Start with no API key, no network, and no Temporal server. A scripted controller drives the loop.

- Example: [examples/support_triage.py](https://github.com/julep-ai/julep-v2/blob/main/examples/support_triage.py)
- Guide: [Getting Started](/docs/start/first-agent)

What it teaches: `Agent`, `@tool(effect="read", idempotent=True)`, `llm=scripted_llm`, `Agent.run(...)`, `Result` dict access, `trace`.

```bash
python examples/support_triage.py
```

### 2. Budget guard

Add a cost ceiling with `budget_cost=`. The facade carries it into the app configuration.

- Example: [examples/research_assistant.py](https://github.com/julep-ai/julep-v2/blob/main/examples/research_assistant.py)

What it teaches: `budget_cost=8.0`, multi-round `llm=scripted_llm`, `cost`, `trace`.

```bash
python examples/research_assistant.py
```

### 3. Approval structure

Add `human_gate(...)` to require explicit approval before any dangerous tool runs.

- Example: [examples/email_approval.py](https://github.com/julep-ai/julep-v2/blob/main/examples/email_approval.py)
- Guide: [Capabilities and Safety](/docs/guides/capabilities-and-safety)

What it teaches: `seq`, `call`, `human_gate`, `deploy`, `CapabilityManifest`, `NativeToolSpec`, `ToolContract`, `InMemoryEnv`, `interpret`, `Deployment`.

```bash
python examples/email_approval.py
```

The flow is `draft_email -> human_gate -> send_email`. The gate is serviced by a local `gate=` callback; no Temporal needed.

### 4. Durable execution on Temporal

Run the same admitted artifact as a durable Temporal workflow.

- Example: [examples/temporal_durable_agent.py](https://github.com/julep-ai/julep-v2/blob/main/examples/temporal_durable_agent.py)
- Guide: [Deploy on Temporal](/docs/deploy/temporal)

What it teaches: `Agent.deployment()`, `Agent.deploy(...)`, `WorkerContext`, `build_worker`, Temporal `Client`.

```bash
# In one terminal:
temporal server start-dev
# In another:
python examples/temporal_durable_agent.py
```

The controller remains keyless. Durability comes from Temporal.

### 5. `@flow` authoring

Switch to the primary define-by-construction surface. Two examples cover the core loop and fan-out patterns.

- [examples/episode_summary_flow.py](https://github.com/julep-ai/julep-v2/blob/main/examples/episode_summary_flow.py) — core `@flow` loop plus CAS-guarded writes
- [examples/cluster_labeling_flow.py](https://github.com/julep-ai/julep-v2/blob/main/examples/cluster_labeling_flow.py) — fan-out, closure captures, `switch`, retry options
- Guide: [Authoring Flows](/docs/guides/authoring-flows)

```bash
python examples/episode_summary_flow.py
python examples/cluster_labeling_flow.py
```

Both examples are keyless and deterministic.

### 6. Raw combinators

Drop to the combinator kernel when you need full control: `seq`, `par`, `alt`, `iter_up_to`, `stage`, `app`, `sub`, `race`, `hedge`, `quorum`.

- Reference: [Concepts](/docs/concepts/model)
- Type calculus: [Typed Flow Calculus](/docs/internals/typed-flow-calculus)
- Normative spec: [Specification](/docs/internals/specification)

### 7. Capstone

Read [examples/elnino/swarm.py](https://github.com/julep-ai/julep-v2/blob/main/examples/elnino/swarm.py) last. It covers a heterogeneous planning swarm, read-only forecast races, quorum reduction, subflow opacity, bounded adaptive agents, staged plan compilation, approval gates, and a capability manifest that attenuates authority.

```bash
python examples/elnino/swarm.py
```

The file prints its own reference text when run directly. Treat it as a source-reading example rather than the first program to run.

---

## Sessions (long-lived state)

After the ladder, explore sessions for long-lived stateful interactions across turns.

- Example: [examples/session_demo.py](https://github.com/julep-ai/julep-v2/blob/main/examples/session_demo.py)
- Guide: [Sessions](/docs/guides/sessions)

What it teaches: `scan`/`loop`/`@session`, `recv`/`emit`, `agent.open(session=..., backend="local"|"temporal"|"cma")`, `SessionHandle`.

```bash
# Source your .env first:
set -a; source .env; set +a
uv run --extra dev --extra providers python examples/session_demo.py local
uv run --extra dev --extra providers python examples/session_demo.py temporal
```

## Further reading

- [Examples overview](/docs/guides/examples) — all examples in one place
- [Provider resilience](/docs/guides/providers-and-resilience) — retry, fallback, and hedging
- [Using the CLI](/docs/guides/using-the-cli) — the `julep` developer CLI
- [Gotchas](/docs/guides/gotchas) — common pitfalls
- [Contributing](/docs/development/contributing) — repository workflow and contribution rules

<!-- ported-by ca-docs-site: start/next-steps -->
