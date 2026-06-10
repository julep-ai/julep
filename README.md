# Composable Serverless Agents

A typed framework for building agents as **composable, durable dataflows** instead of ad-hoc loops: flows can crash and resume, retry safely, explain every step through a derived projection, and deny any tool the model was not explicitly allowed to call. You can start with a pure, keyless local `Agent` facade and later deploy the same frozen control flow to Temporal for durable execution; the pure core stays dependency-free, while the Temporal layer is optional.

---

## Quickstart (10 minutes, no API key)

Install the base package and run this as a normal Python script:

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
print(result["status"], result["output"], result["trace"])

# Later, with the temporal extra and a Temporal client:
# await agent.deploy(client, session_id="ticket-123", input="Customer was charged twice.")
```

`llm=` is just a `(brain, payload) -> reply` callable, so examples and tests can stay keyless and deterministic. If you omit `llm`, the facade uses a keyless stub that warns and returns the input unprocessed. See the runnable version in `examples/support_triage.py`.

---

## Install

```bash
pip install composable-agents            # authoring + compile only (PyYAML)
pip install 'composable-agents[temporal]' # + durable execution on Temporal
pip install 'composable-agents[temporal,http,otel]'  # + native HTTP hands + OTel export
```

`composable_agents.HAVE_TEMPORAL` reports whether the runtime is available; the package imports and compiles flows either way.

---

## Why it's different

- **Deny-by-default capabilities.** A hallucinated or ungranted tool call is denied instead of being routed somewhere surprising.
- **Approval gates for irreversible actions.** `dangerous` or approval-required tools must sit behind `human_gate()`; strict deploy refuses ungated paths.
- **Content-hash freeze and replay.** Tool definitions are frozen to hashes before execution, so a running flow cannot silently pick up a changed contract.
- **Explain every step.** The projection plane derives an append-only trace from execution history, including value flow, per-shape cost, pending gates, and OTel span data.
- **Teaching diagnostics.** Blocked deploys render actionable `fix:` lines; with source capture enabled, diagnostics also point at the user line that produced the node.

```text
Blocking diagnostics:
- [CAP_TOOL_DENIED@$] error: tool 'srv/denied' is not granted
    --> app.py:42  (call(mcp("srv", "denied")))
    fix: Add this tool to the capability manifest's tools: allow-list, or remove the call.
```

For iteration, use dev mode: `deploy(..., mode="dev")` or `Agent(..., mode="dev")` warns and continues while `deployment.prod_gap_summary()` tells you what strict production deploy would block. Temporal runs stay prod-strict; dev-mode deployments are for local iteration.

---

## Climb the ladder

1. `Agent.run` for a keyless local loop: `examples/support_triage.py`.
2. Add a budget guard to the same facade: `examples/research_assistant.py`.
3. Add approvals via `human_gate` in a combinator flow: `examples/email_approval.py`.
4. Deploy the same admitted artifact to Temporal with `deploy()` / `agent.deploy(...)`.
5. Drop to raw combinators (`seq`, `par`, `alt`, `iter_up_to`, `stage`, `app`) when you need full control.
6. Study the capstone composition in `examples/elnino/swarm.py`.

---

## Documentation

The documentation index is [docs/README.md](docs/README.md). Newcomers should start with [docs/getting-started.md](docs/getting-started.md), then read [docs/concepts.md](docs/concepts.md).

Key guides:

- [Getting started](docs/getting-started.md)
- [Concepts](docs/concepts.md)
- [Dispatch boundary](docs/dispatch-boundary.md) — what belongs in a flow vs. the dispatch layer
- [Capabilities and safety](docs/capabilities-and-safety.md)
- [Deploy to Temporal](docs/deploy-temporal.md)
- [Deploy on DBOS](docs/deploy-dbos.md) — durable flows and agent loops on Postgres via dbos-transact
- [Examples](docs/examples.md)
- [Specification](docs/SPEC.md) — the normative contract.

---

## Typed composition (the `Flow` surface)

The `composable_agents.flow` layer is a **typed authoring wrapper** over the same
`Node` IR — it carries Python types while you build, then *elaborates to the
identical IR and disappears before freeze* (the golden corpus never moves). Tools,
flows, and agents become first-class **values** you import, type-check, and
recombine — closing the gap between the ergonomic facade and the composable algebra.

```python
from composable_agents.flow import flow, seq          # typed combinators
from composable_agents.flow_adapters import as_type    # explicit Any-edge cast

# A @tool is a typed leaf; >> threads types (a mismatch is a mypy error):
research = search >> classify                 # Flow[Query, Priority]

# An Agent IS a Flow — it composes as a node, and decomposes:
inbox = Agent(brain="claude-sonnet-4-6", tools=[search])
pipeline = fetch >> inbox >> notify           # an agent mid-pipeline
vip      = inbox.with_tools(add=[escalate]).replace(brain="opus")

# Capabilities are uniform: Tools (→ call) and named Flows/Agents (→ sub).
# A sub-agent runs with its OWN authority — the parent never inherits its tools:
triage = Agent(brain="haiku", tools=[search, classify]).named("triage.v1")
desk   = Agent(brain="claude-sonnet-4-6", tools=[lookup, triage])   # triage = an attenuated sub-agent

# Scale a part independently: pass it as a split capability (own worker/queue):
desk_scaled = Agent(brain="claude-sonnet-4-6",
                    tools=[lookup, triage.as_sub(queue="triage-pool")])

r = desk.run("ticket text")    # r: Result[Any] — r.output / r.status / r.cost, and r["status"] (dict-compatible)
```

Typing is **hybrid and honest**: leaves and pipelines are typed; the agent/LLM/JSON
boundary is `Any`, made *loud* by `as_type(...)`/`expect(...)` adapters and the
`any_edges(...)` reporter rather than hidden. The string DSL and the original
`Agent` facade keep working unchanged — this surface is additive.

---

## The mental model

**Three planes.** A *Control* plane (a Temporal workflow) walks a frozen IR tree and decides what runs next. It dispatches to *Brains* (LLM `Think` activities, rendered from `.ctx` brain definitions) and *Hands* (stateless tool activities — MCP tools or native HTTP endpoints on Cloud Run / Lambda). A *Projection* plane derives an append-only, causally-linked event log (a "pomset") for observability — value store, per-shape cost, OTel spans, replay UI. **The projection is derived, never the source of durability**; history is.

**The shape lattice.** Every flow has an inferred *shape* on the lattice

```
Pipeline < Dataflow < Branching < Feedback < Staged < Agent
```

Shape is computed (`surface_shape`), not declared, and it bounds what static guarantees hold. A pipeline is fully analyzable; an agent is an open-ended controller loop at the top. A `Sub` (child flow) is **opaque** at the surface — it looks like a `Pipeline` to its parent (`surface_shape`) while its real contracted shape is visible only when you ask for the closed shape (`closed_shape`). This is the "Joined firewall": a child's internal complexity does not leak into the parent's analysis or projection.

---

## Authoring DSL

**Structural combinators** (the name documents the shape it produces):

| Combinator | Shape | Meaning |
|---|---|---|
| `seq(a, b, ...)` | Pipeline | run in sequence, threading output -> input |
| `par(a, b, ...)` / `fanout(...)` | Dataflow | run concurrently on the same input, collect results |
| `each(body, max_parallel=..., reducer=...)` | Dataflow | run `body` once per element of the input list, collect in order |
| `alt(pred, if_true, if_false)` | Branching | choose a branch by a registered pure predicate |
| `iter_up_to(max, body, until=...)` | Feedback | iterate `body` up to `max` times, optional convergence predicate |
| `stage(planner=...)` | Staged | a brain emits a plan; it is compiled, admitted (§8), and run as IR |
| `app(controller, tools=..., subflows=..., budget=..., max_rounds=...)` | Agent | open-ended controller loop (use sparingly) |
| `sub(ref, contract=None)` | Pipeline (opaque) | an opaque child flow carrying its contract across the firewall; omitted contract defaults to `Contract.of(Shape.PIPELINE)` |

**Leaves:** `native(name)` and `mcp(server, tool)` build tool refs; `call(ref_or_name)` invokes a tool ref or a bare native-tool name. Also: `think(brain)`, `brain_from_ctx(path)`, `ident()`, `arr(pure_name)`.

**Derived combinators** lower to a uniform, analyzable race spine:

- `race([a, b, ...], reduce=...)` or `race(a, b, ...)` — first to finish wins, cancel the rest.
- `hedge([a, b, ...], hedge_ms=N, reduce=...)` — start the first branch; reveal the rest only after a delay.
- `quorum([a, b, ...], k=K, reduce=...)` — settle once `K` branches succeed.
- `map_n` / `map_reduce` / `vote` / `review` — common fan-out patterns.
- `human_gate(prompt=..., timeout_s=...)` — pause for a human decision (a durable signal-wait).

Leaves accept `ctx=` (a `ContextPolicy`) and `ann=` (`Ann`: `cost_usd`, caching hints, effects, `timeout_s`).

---

## The compile pipeline (`deploy`)

`deploy(flow, snapshot, capabilities=...)` runs four static gates in order; any blocking diagnostic aborts (`strict=True`, the default) or is returned on the `Deployment` for triage:

1. **Freeze** — snapshot every tool (MCP version + schema + annotations, or a native contract) to a **content hash** and bind each `call` to it, so the tool set can never shift under a running flow. The flow is deep-copied to a clean tree (cycles rejected, sharing removed, ids normalized to deterministic paths like `$.L`, `$.R`).
2. **Validate** — per-op well-formedness, schema edges, and a non-blocking warning where a `par` branch reads the whole session (sequential degrade).
3. **Capability enforcement (§9)** — the flow may only use granted tools, brains, memory scopes, and MCP servers. A capability manifest (YAML/dict) also supplies **contract assertions**: the only way a non-read tool becomes legal inside a race.
4. **Race admission (§5)** — every branch of a `race`/`hedge`/`quorum` must be read-only or contract-asserted idempotent, so a duplicated branch can do no harm. MCP "read-only" *hints* are untrusted — a tool must be **asserted** in the capability manifest to race.

`freeze`, `validate`, and the §8/§9/§5 checks are all exposed individually for finer control.

---

## Execution on Temporal

The execution layer is the only part that imports `temporalio`, and it does so behind a guarded import.

- **`FlowWorkflow`** walks the frozen IR. The same deterministic interpreter (`composable_agents.execution.interpreter.interpret`) runs here and in tests; only the injected `Env` differs (Temporal activities vs. in-memory callables). It verifies deploy-pinned pure source hashes via `verifyPures` at workflow start, before running the interpreter. Per-tool retry policy is derived from each frozen contract — reads/idempotent tools retry liberally; non-idempotent writes retry cautiously behind an `Idempotency-Key` the `callHand` activity sends. Policy-decision errors (`CapabilityDenied`, `PlanRejected`, `ValidationError`, `FreezeError`, `PureDriftError`) are non-retryable.
- **`AgentWorkflow`** is the `app` loop. It is bounded by construction: each round the controller returns one of a closed action set — *finish*, *escalate*, call one **granted** tool, or invoke one registered **sub-flow** — and a **budget guard** stops the run before any action that would exceed the capability budget. History growth is bounded by **continue-as-new** (a configurable seam). It is a separate workflow precisely so its continue-as-new truncates only the agent's history, not the parent flow's.
- **`Sub`** is a child `FlowWorkflow` resolved by `ref`; the firewall is structural (the surface shape is already opaque), so a child's value crosses while its shape does not. Child flows verify their own pure pins when the subflow registry entry supplies `pureSourceHashes`/`pinnedPures`; pins are not inherited from the parent.
- **Human gates** are a `submitHuman` signal plus a durable `wait_condition`. Two queries support a review UI: `projection` (the full pomset snapshot — events, `costByShape`, `pending`) and **`openGates`** (the precise activation ids currently parked on a gate — exactly what to signal, excluding structural `seq`/`par` activations).

`run_flow` / `start_flow` are client helpers; `build_worker` / `run_worker` host the workflows and the six activities (`verifyPures`, `callHand`, `invokeBrain`, `compilePlan`, `resolveSubflow`, `resolveAgentSpec`).

Going to production is the same deploy artifact plus a worker process that wires the environment once:

```python
import asyncio
from temporalio.client import Client
from composable_agents import (
    call, mcp, think, seq, deploy, snapshot_from_listings,
    register_brain, Brain,
)
from composable_agents.execution.worker import run_worker

flow = seq(call(mcp("search", "web")), think("summarize"))
snapshot = snapshot_from_listings({
    "search": {"web": {"inputSchema": {"type": "object"},
                       "annotations": {"readOnlyHint": True, "idempotentHint": True}}},
})
deployment = deploy(flow, snapshot)          # raises if any blocking diagnostic

async def main():
    client = await Client.connect("localhost:7233")
    result = await deployment.run(client, session_id="run-1", input={"q": "temporal vs dbos"})
    print(result)

asyncio.run(main())
```

A worker hosts the workflow + activities:

```python
register_brain(Brain(name="summarize", model="claude-...", system="Summarize."))
await run_worker(
    target_host="localhost:7233",
    hand_urls={"native_tool": "https://my-hand.run.app"},
    mcp_call=my_async_mcp_caller,   # async (server, tool, value, idempotency_key) -> result
    llm=my_async_llm,               # async (brain, value) -> reply
    capabilities=my_capability_manifest,
)
```

Temporal activity retries re-use the same deterministic activation `cid`, so `callHand` passes a stable idempotency key to both native HTTP hands and MCP callers. MCP transports therefore carry the key required for `required` idempotent tools to be admitted.

---

## Staged plans and plan extraction

`stage(planner=...)` lets a brain emit a plan at runtime. The plan is parsed, **admitted under §8** (it may loop but not itself stage or app, must use only granted tools, and must fit the budget), then run as ordinary IR. Because an admitted plan is not re-frozen, its calls are **late-bound** by tool ref at execution time (`call_ref_key` / `call_contract`).

The offline complement is **plan extraction**: an observed agent action trace can be generalized into a candidate plan (`generalize_trace_to_plan`), checked (`extract_plan`), and promoted to a cheap, replayable stage (`promote_plan`, which enforces admission). The agent discovers a procedure; the plan freezes it.

---

## The pure core vs. the Temporal layer

This split is deliberate and load-bearing:

- **Pure core** (`kinds`, `ir`, `shapes`, `contracts`, `freeze`, `validate`, `dsl`, `derived`, `capabilities`, `staged`, `projection`, `dotctx`, `agent_loop`, `deploy`, and `execution.interpreter`) has **no Temporal dependency**. The interpreter takes an injected `Env` of effect handlers and concurrency primitives, so the same control-flow logic runs under Temporal *and* under an in-memory `InMemoryEnv` in tests.
- **Execution layer** (`execution.harness`, `execution.activities`, `execution.worker`, `execution.otel`) binds to Temporal and is import-guarded.

**Testing.** The full suite passes with the pure core covered without `temporalio`; install the dev extra to include Temporal E2E coverage when available. Run:

```bash
pip install -e '.[dev]'
pytest                 # full suite incl. Temporal E2E
```

---

## Open seams (§6) — configuration decisions

These are surfaced as explicit knobs rather than hidden defaults:

- **Freeze timing** — `deploy(..., freeze_timing="deploy_time")` (default) freezes once and reuses the artifact for maximal determinism; `"per_run"` keeps a snapshot source so each launch can re-freeze against fresh tool definitions (`Deployment.refresh`).
- **Retry shaping** — `ExecutionPolicy` controls activity timeouts and the read-vs-write retry attempt counts and backoff.
- **Continue-as-new cadence** — `AgentConfig.continue_as_new_after` bounds agent history; `0` disables it.
- **Projection sink** — the in-workflow projection threads causal ids deterministically and is exposed read-only via the `projection` query; the durable sink (Postgres via `PostgresProjection`, or OTel via `execution.otel.export_spans`) is fed out-of-band from history so the workflow performs no projection IO.

---

## Module map

```
composable_agents/
  kinds.py          shape lattice + effect/idempotency/context enums
  ir.py             canonical IR: nodes, steps, merges, tool refs, JSON codec
  shapes.py         surface_shape / closed_shape (the Sub firewall)
  contracts.py      tool contracts, MCP annotation inference, frozen manifest
  purity.py         registry of named deterministic functions (pures)
  transforms.py     cycle detection, id normalization
  freeze.py         snapshot -> content-hash binding of every tool
  validate.py       well-formedness + schema diagnostics
  dsl.py            structural combinators + Contract helpers
  derived.py        race/hedge/quorum/map/vote/human_gate + §5 admission
  capabilities.py   §9 capability manifest, budget, grants, overrides
  staged.py         §8 plan cost estimation + plan admission
  projection.py     pomset events, value store, in-memory/Postgres sinks, OTel data
  resilience.py     provider fallback policy, error taxonomy, circuit breaker
  dotctx.py         §3.2 Brain definitions and lowering to Think nodes
  agent_loop.py     P4 agent loop logic + plan extraction (pure)
  agent.py          Agent facade + @tool decorator for Python-callable hands
  deploy.py         the compile pipeline + Deployment artifact
  errors.py         the error taxonomy
  execution/
    interpreter.py  the deterministic IR interpreter + InMemoryEnv (pure)
    harness.py      FlowWorkflow, AgentWorkflow, Temporal Env, client helpers
    activities.py   callHand / invokeBrain / compilePlan / resolve* activities
    worker.py       Client + Worker wiring
    serve.py        container worker entrypoint (env config, SIGTERM drain, probes)
    debounce.py     dispatch-layer batch collator (Temporal signal-with-start)
    otel.py         OpenTelemetry export of the projection
```

---

## License

This project is licensed under Apache-2.0. See [LICENSE](LICENSE).
