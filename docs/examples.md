# Examples

The `examples/` directory is a ladder. Start with the keyless local facade, then add budget, approval, durable execution, and finally the full combinator surface.

## `examples/support_triage.py`

What it teaches: a deterministic, keyless `Agent.run(...)` loop over granted read-only tools.

Rung: local facade, deny-by-default tool calls.

Key APIs: `Agent`, `@tool(effect="read", idempotent=True)`, `llm=scripted_llm`, `Agent.run(...)`, `Result` dict access, `trace`.

Run:

```bash
python examples/support_triage.py
```

This example needs no API key, Temporal server, network, clock, or random source. The scripted controller first calls `search_kb`, then `classify_priority`, then returns `{"output": ...}`.

## `examples/research_assistant.py`

What it teaches: the same facade with a controller budget.

Rung: local facade plus budget guard.

Key APIs: `Agent`, `@tool`, `budget_usd=8.0`, multi-round `llm=scripted_llm`, `Agent.run(...)`, `spentUsd`, `trace`.

Run:

```bash
python examples/research_assistant.py
```

This example is keyless and deterministic. The `web_search` tool is an in-memory corpus, not a network search. The budget is declared on the facade and is carried into the app configuration.

## `examples/email_approval.py`

What it teaches: approval structure for an effectful flow.

Rung: combinator flow with human approval and local interpreter execution.

Key APIs: `seq`, `call`, `human_gate`, `deploy`, `CapabilityManifest`, `NativeToolSpec`, `ToolContract`, `InMemoryEnv`, `ProjectionEmitter`, `InMemoryProjection`, `interpret`, `Deployment`.

Run:

```bash
python examples/email_approval.py
```

This example is keyless and does not need Temporal. It builds a flow `draft_email -> human_gate -> send_email`, declares `send_email` as `dangerous` and `approval: required`, deploys the flow, and dry-runs it through `InMemoryEnv`. The gate is serviced by a local `gate=` callback.

## `examples/temporal_durable_agent.py`

What it teaches: running a facade `Agent` durably on a real Temporal server.

Rung: durable execution path.

Key APIs: `Agent`, `@tool`, `Agent.deployment()`, `Agent.deploy(...)`, `WorkerContext`, `build_worker`, Temporal `Client`, HTTP native hands.

Run a Temporal dev server in another terminal:

```bash
temporal server start-dev
```

Then run:

```bash
python examples/temporal_durable_agent.py
```

The controller is still keyless: `scripted_controller` is a deterministic async callable. The durability comes from Temporal. The example starts a tiny stdlib HTTP hand server, builds a worker with `WorkerContext`, runs `AgentWorkflow`, and prints the terminal result. For the production worker shape, see [Deploy on Temporal](deploy-temporal.md).

## `examples/elnino/swarm.py`

What it teaches: capstone composition across the largest part of the public surface.

Rung: read-last reference for typed, durable, capability-bounded dataflows.

Key APIs: `seq`, `par`, `alt`, `iter_up_to`, `stage`, `app`, `sub`, `call`, `think`, `mcp`, `native`, `hedge`, `quorum`, `human_gate`, `pure`, `Brain`, `register_brain`, `Budget`, `CapabilityManifest`, `McpSnapshot`, `McpServerSnapshot`, `McpToolSpec`, `NativeToolSpec`, `ToolContract`, `deploy`, `start_flow`.

Run:

```bash
python examples/elnino/swarm.py
```

The file prints its own reference text when run directly. Treat it as a source-reading example rather than the first program to execute. It shows a heterogeneous planning swarm, read-only forecast races, quorum reduction, subflow opacity, bounded adaptive agents, staged plan compilation, approval gates for dangerous tools, and a capability manifest that attenuates authority.

## Run the keyless local examples

```bash
python examples/support_triage.py
python examples/research_assistant.py
python examples/email_approval.py
```

These three do not require an API key or a Temporal server. The durable example requires `temporal server start-dev`; the capstone is the largest reference and should be read after the smaller examples.

Related docs: [Getting Started](getting-started.md), [Concepts](concepts.md), [Capabilities and Safety](capabilities-and-safety.md), [Deploy on Temporal](deploy-temporal.md), [SPEC](SPEC.md), [Typed Flow](design/typed-flow.md), [README](../README.md), [docs index](README.md), and [CONTRIBUTING](../CONTRIBUTING.md).
