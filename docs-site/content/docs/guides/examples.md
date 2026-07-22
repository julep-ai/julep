---
title: "Examples"
description: "Runnable examples that show @flow, the facade, approvals, budgets, and lower-level combinators."
---

The `examples/` directory is a ladder. Start with define-by-construction
`@flow`, then use the facade, approval, durable execution, and combinator
kernel examples as focused references.

## `examples/episode_summary_flow.py`

What it teaches: the core `@flow` loop plus artifact store-guarded writes.

Rung: primary authoring surface with keyless `deploy(...).dry_run(...)`.

Key APIs: `@flow`, `@tool`, `@pure`, `Reasoner`, `think`, `cond`, `each`, `deploy(tools=..., reasoners=...)`, `Deployment.dry_run(...)`.

Run:

```bash
python examples/episode_summary_flow.py
```

This example is keyless and deterministic. It reads an episode, runs two fake
reasoner passes in dry-run mode, and writes summary surfaces only if the source
hash is unchanged. The demo rollup stays at two `success`, one `stale_source`,
and one `not_found`.

## `examples/cluster_labeling_flow.py`

What it teaches: fan-out, closure captures, `switch`, inferred parallel reasoner
steps, and retry options.

Rung: product-shaped `@flow` porting example.

Key APIs: `each(..., max_parallel=3)`, keyword closure capture,
`think(...)` siblings from the same source, `switch(...)`, per-step
`retries=`, `retry_interval_s=`, and `backoff_rate=`.

Run:

```bash
python examples/cluster_labeling_flow.py
```

This example is keyless and deterministic. It reads one global macrocluster
snapshot, fans out bounded per-cluster labeling work, then performs a single
transactional artifact store-guarded snapshot write and status tally.

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

Key APIs: `Agent`, `@tool`, `budget_cost=8.0`, multi-round `llm=scripted_llm`, `Agent.run(...)`, `cost`, `trace`.

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

Key APIs: `Agent`, `@tool`, `Agent.deployment()`, `Agent.deploy(...)`, `WorkerContext`, `build_worker`, Temporal `Client`, HTTP native tools.

Run a Temporal dev server in another terminal with `temporal server start-dev`,
then run `python examples/temporal_durable_agent.py`.

The controller is still keyless: `scripted_controller` is a deterministic async callable. The durability comes from Temporal. The example starts a tiny stdlib HTTP tool server, builds a worker with `WorkerContext`, runs `AgentWorkflow`, and prints the terminal result. For the production worker shape, see [Deploy on Temporal](/docs/deploy/temporal).

## `examples/cma_managed_agent.py`

What it teaches: running a facade `Agent` on Anthropic's hosted Claude Managed Agents, where the hosted model drives the loop while the framework stays the capability and budget authority.

Rung: hosted execution path (the one example that talks to a live service).

Key APIs: `Agent`, `@tool`, `Agent.run_on_cma(...)`, `AnthropicCMAClient` (the `julep[cma]` extra), the granted tool surface projected as CMA custom tools, `cost`, `trace`.

Set `ANTHROPIC_API_KEY` first, then run
`python examples/cma_managed_agent.py`.

Without `ANTHROPIC_API_KEY` the example is a clean no-op (it prints how to run). The hosted model picks the tools (`get_weather`, then `to_fahrenheit`); the framework dispatches each call locally, enforces deny-by-default grants and the budget, and records the same `cost`/`trace` as `.run()`. Note that `spent` is in the framework's abstract cost units, not dollars. This example talks to a beta API (`managed-agents-2026-04-01`) and is experimental.

## `examples/session_demo.py`

What it teaches: a long-lived, **stateful** session driven live across all three backends, proving the carrier threads state across turns (plant a codeword on turn 1, recall it on turn 2).

Rung: the session surface (the long-lived counterpart of a flow).

Key APIs: `scan`/`loop`/`@session`, `recv`/`emit`, `agent.open(session=..., backend="local"|"temporal"|"cma")`, `SessionHandle` (`send`/`events`/`state`/`close`), `SessionEvent`.

Run (keys are not shell-exported, so source `.env` first):

```bash
set -a; source .env; set +a
uv run --extra dev --extra providers python examples/session_demo.py local
uv run --extra dev --extra providers python examples/session_demo.py temporal
uv run --extra dev --extra providers --extra cma python examples/session_demo.py cma
```

This one talks to a live service (real `anthropic:claude-haiku-4-5`). `local` and `temporal` thread the carrier natively (recall holds); `cma` opens a fresh hosted session per turn and has no framework carrier, so the driver resends the transcript. Full model: [Sessions](/docs/guides/sessions).

## `examples/elnino/swarm.py`

What it teaches: capstone composition across the largest part of the public surface.

Rung: read-last reference for typed, durable, capability-bounded dataflows.

Key APIs: `seq`, `par`, `alt`, `iter_up_to`, `stage`, `app`, `sub`, `call`, `think`, `mcp`, `native`, `hedge`, `quorum`, `human_gate`, `pure`, `Reasoner`, `Budget`, `CapabilityManifest`, `McpSnapshot`, `McpServerSnapshot`, `McpToolSpec`, `NativeToolSpec`, `ToolContract`, `deploy`, `start_flow`.

Run:

```bash
python examples/elnino/swarm.py
```

The file prints its own reference text when run directly. Treat it as a source-reading example rather than the first program to execute. It shows a heterogeneous planning swarm, read-only forecast races, quorum reduction, subflow opacity, bounded adaptive agents, staged plan compilation, approval gates for dangerous tools, and a capability manifest that attenuates authority.

## `examples/dotctx_issue_dedup.py`

What it teaches: an agent-shaped rich dotctx with a bounded tool loop that lowers to Feedback.

Rung: declarative rich-dotctx contract; tool-loop execution is Phase 3/4 work.

Key APIs: `load_dotctx`, `reasoner_to_flow`, `Reasoner`, `max_rounds`, `require_tool_call`.

Run:

```bash
python -m examples.dotctx_issue_dedup
```

This keyless no-op loads and lowers the issue-dedup contract without calling a provider. It shows why a single structured round cannot honestly stand in for the required search-first tool loop.

## Run the keyless local examples

```bash
python examples/episode_summary_flow.py
python examples/cluster_labeling_flow.py
python examples/support_triage.py
python examples/research_assistant.py
python examples/email_approval.py
```

These five do not require an API key or a Temporal server. The durable example requires `temporal server start-dev`; the capstone is the largest reference and should be read after the smaller examples.

Related docs: [Authoring Guide](/docs/guides/authoring-flows), [Getting Started](/docs/start/first-agent), [Concepts](/docs/concepts/model), [Capabilities and Safety](/docs/guides/capabilities-and-safety), [Deploy on Temporal](/docs/deploy/temporal), [SPEC](/docs/internals/specification), [Typed Flow](/docs/internals/typed-flow-calculus), [README](/docs), [docs index](/docs), and [CONTRIBUTING](/docs/development/contributing).

<!-- ported-by julep-docs-site: guides/examples -->
