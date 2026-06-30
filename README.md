# Composable Serverless Agents

A framework for building agents as **composable, durable dataflows** instead of ad-hoc loops: flows can crash and resume, retry safely, explain every step through a derived projection, and deny any tool the model was not explicitly allowed to call. The primary authoring surface is define-by-construction `@flow`: ordinary Python names graph steps while registered tools, pures, reasoners, branches, fan-out, retries, and timeouts compile to the same frozen wire-format IR. The pure core stays dependency-free, while the Temporal layer is optional.

---

## Quickstart (10 minutes, no API key)

Install the base package and run this as a normal Python script:

```python
from typing import TypedDict

from composable_agents import Reasoner, deploy, flow, pure, think, tool


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


support_reply = Reasoner(
    name="support_reply",
    model="anthropic:claude-haiku-4-5-20251001",
    system="Draft one concise support reply as JSON.",
    reply=SupportReply,
)


@flow
def triage(ticket: str) -> dict[str, str]:
    hit = lookup_ticket(ticket, retries=2, timeout_s=5)
    prompt = ticket_prompt(hit)
    answer = think(support_reply, prompt, timeout_s=10)
    return hit | answer


def fake_support_reply(value: dict[str, str]) -> SupportReply:
    return {"reply": f"{value['queue']}: {value['context']}"}


deployment = deploy(triage, tools=[lookup_ticket], reasoners=[support_reply])
result = deployment.dry_run(
    "Customer was charged twice.",
    reasoners={"support_reply": fake_support_reply},
)

print(result.value)
```

`@flow` runs once at definition time with data handles. Registered tools, registered pures, `think(...)`, `cond(...)`, `switch(...)`, `each(...)`, and `reschedule(...)` append graph steps instead of doing runtime work; `|` merges records and `h["key"]` plucks fields. `deploy(..., tools=..., reasoners=...)` freezes the tool and reasoner surface, and `dry_run(...)` executes locally with in-memory tools and deterministic fake reasoners. See the larger `@flow` examples in `examples/episode_summary_flow.py` and `examples/cluster_labeling_flow.py`.

---

## Install

```bash
pip install composable-agents            # authoring + compile only (PyYAML)
pip install 'composable-agents[temporal]' # + durable execution on Temporal
pip install 'composable-agents[temporal,http,otel]'  # + native HTTP tools + OTel export
pip install 'composable-agents[cli]'      # + the `ca` developer CLI (see docs-site/content/docs/guides/using-the-cli.md)
```

`composable_agents.HAVE_TEMPORAL` reports whether the runtime is available; the package imports and compiles flows either way.

---

## Developer CLI (`ca`)

`ca` is the developer CLI for a whole **module of agents** — "dbt for agents, terminal-native." Point it at a directory; it discovers every `@flow`/`Agent(...)`, treats each as a node in a cross-agent graph, and gives you one selection grammar across every verb:

```bash
ca ls                                  # list agents (name · kind · tags)
ca graph                               # the cross-agent DAG as Graphviz DOT
ca run triage --input '"TICKET-42"'    # execute locally, stream the trace tree
ca lint +triage                        # validate an agent and everything it depends on
ca deploy triage --env staging         # freeze → publish → record in the deploy ledger
ca status --env staging                # what's deployed where + drift (exit 3 on drift)
```

Selectors compose: `tag:support`, `state:modified` (Slim-CI), `+agent`/`agent+`/`@agent` graph traversal, `a,b` intersection, `--exclude`. Full reference: **[docs-site/content/docs/guides/using-the-cli.md](docs-site/content/docs/guides/using-the-cli.md)**.

---

## Sessions — long-lived, keep-messaging agents

A flow is a one-shot arrow. A **session** is its long-lived counterpart: open it once, keep sending messages, and stream events back while it threads a typed **carrier** (e.g. conversation history) across turns — on the **same** frozen-IR control plane (same interpreter, same capability/budget guards, same projection).

```python
handle = await agent.open(session=chat, backend="temporal")   # or "local" / "cma"
await handle.send(user_msg)
async for ev in handle.events():        # Emit / Turn / Error / Closed (ends on Closed)
    render(ev)
await handle.close()
```

Author with `scan(step, init)` (explicit `(carrier, msg) → (carrier', output)` turn), `loop(...)`, or the `@session` coroutine sugar — all compile to one `Op.LOOP` (the unbounded, `recv`-guarded sibling of `iter_up_to`). Three backends: **local** (in-memory), **Temporal** (durable `SessionWorkflow`; the carrier survives `continue_as_new`), **CMA** (one Anthropic managed-agent session per turn). Drive from the terminal with `ca chat` / `ca trigger` / `ca listen`. Full guide: **[docs-site/content/docs/guides/sessions.md](docs-site/content/docs/guides/sessions.md)**.

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

1. Start with `@flow` authoring and local `dry_run`: `examples/episode_summary_flow.py` teaches the core loop plus CAS-guarded writes.
2. Scale the same surface: `examples/cluster_labeling_flow.py` teaches fan-out, closure captures, `switch`, inferred parallel reasoner steps, and retry options.
3. Use the `Agent` facade for a keyless local controller loop: `examples/support_triage.py`.
4. Add a budget guard to the facade: `examples/research_assistant.py`.
5. Add approvals via `human_gate` in a combinator-kernel flow: `examples/email_approval.py`.
6. Deploy the same admitted artifact to Temporal with `deploy()` / `agent.deploy(...)`.
7. Drop to raw combinators (`seq`, `par`, `alt`, `iter_up_to`, `stage`, `app`) when you need full control, or use `composable_agents.typed` when you want typed composition as an escape hatch.

---

## Documentation

The documentation index is [docs-site/content/docs/index.mdx](docs-site/content/docs/index.mdx). Newcomers should start with the quickstart above, then read [docs-site/content/docs/guides/authoring-flows.md](docs-site/content/docs/guides/authoring-flows.md) and [docs-site/content/docs/concepts/model.md](docs-site/content/docs/concepts/model.md).

Key guides:

- [Getting started](docs-site/content/docs/start/first-agent.md)
- [Authoring guide](docs-site/content/docs/guides/authoring-flows.md)
- [Concepts](docs-site/content/docs/concepts/model.md)
- [Sessions](docs-site/content/docs/guides/sessions.md) — long-lived, keep-messaging agents on local / Temporal / CMA
- [Dispatch boundary](docs-site/content/docs/concepts/dispatch-boundary.md) — what belongs in a flow vs. the dispatch layer
- [Capabilities and safety](docs-site/content/docs/guides/capabilities-and-safety.md)
- [Deploy to Temporal](docs-site/content/docs/deploy/temporal.md)
- [Deploy on DBOS](docs-site/content/docs/deploy/dbos.md) — durable flows and agent loops on Postgres via dbos-transact
- [Examples](docs-site/content/docs/guides/examples.md)
- [Specification](docs-site/content/docs/internals/specification.md) — the normative contract.

---

## Typed Composition Escape Hatch

The `composable_agents.typed` layer is a **typed authoring wrapper** over the same
`Node` IR — it carries Python types while you build, then *elaborates to the
identical IR and disappears before freeze* (the golden corpus never moves). Use
it when type-checkable composition is clearer than `@flow`; it is not the primary
authoring path.

```python
from composable_agents import tool
from composable_agents.typed import as_flow


@tool(effect="read", idempotent=True)
def fetch(ticket: str) -> dict[str, str]:
    return {"ticket": ticket}


@tool(effect="read", idempotent=True)
def classify(hit: dict[str, str]) -> dict[str, str]:
    return {"priority": "normal", **hit}


pipeline = fetch >> classify
named = pipeline.named("support.triage.v1")

print(named.local_name)
print(as_flow(fetch).local_name)
```

Typing is **hybrid and honest**: leaves and pipelines are typed; the agent/LLM/JSON
boundary is `Any`, made *loud* by `as_type(...)`/`expect(...)` adapters and the
`any_edges(...)` reporter rather than hidden. The combinator kernel and the
`Agent` facade keep working unchanged; this surface is additive.

---

## The mental model

**Three planes.** A *Control* plane (a Temporal workflow) walks a frozen IR tree and decides what runs next. It dispatches to *Reasoners* (LLM `Think` activities, rendered from `.ctx` reasoner definitions) and *Tools* (stateless tool activities — MCP tools or native HTTP endpoints on Cloud Run / Lambda). A *Projection* plane derives an append-only, causally-linked event log (a "pomset") for observability — value store, per-shape cost, OTel spans, replay UI. **The projection is derived, never the source of durability**; history is.

**The shape lattice.** Every flow has an inferred *shape* on the lattice

```
Pipeline < Dataflow < Branching < Feedback < Staged < Agent
```

Shape is computed (`surface_shape`), not declared, and it bounds what static guarantees hold. A pipeline is fully analyzable; an agent is an open-ended controller loop at the top. A `Sub` (child flow) is **opaque** at the surface — it looks like a `Pipeline` to its parent (`surface_shape`) while its real contracted shape is visible only when you ask for the closed shape (`closed_shape`). This is the "Joined firewall": a child's internal complexity does not leak into the parent's analysis or projection.

---

## Combinator Kernel

`@flow` compiles through the combinator kernel. The kernel is still fully
supported, and the frozen IR it emits is the wire-format ground truth. Reach for
it when you need exact structural control or when you are implementing another
frontend.

**Structural combinators** (the name documents the shape it produces):

| Combinator | Shape | Meaning |
|---|---|---|
| `seq(a, b, ...)` | Pipeline | run in sequence, threading output -> input |
| `par(a, b, ...)` / `fanout(...)` | Dataflow | run concurrently on the same input, collect results |
| `each(body, max_parallel=..., reducer=...)` | Dataflow | run `body` once per element of the input list, collect in order |
| `alt(pred, if_true, if_false)` | Branching | choose a branch by a registered pure predicate |
| `iter_up_to(max, body, until=...)` | Feedback | iterate `body` up to `max` times, optional convergence predicate |
| `stage(planner=...)` | Staged | a reasoner emits a plan; it is compiled, admitted (§8), and run as IR |
| `app(controller, tools=..., subflows=..., budget=..., max_rounds=...)` | Agent | open-ended controller loop (use sparingly) |
| `sub(ref, contract=None)` | Pipeline (opaque) | an opaque child flow carrying its contract across the firewall; omitted contract defaults to `Contract.of(Shape.PIPELINE)` |

**Leaves:** `native(name)` and `mcp(server, tool)` build tool refs; `call(ref_or_name)` invokes a tool ref or a bare native-tool name. Also: `think(reasoner)`, `reasoner_from_ctx(path)`, `ident()`, `arr(pure_name)`.

**Derived combinators** lower to a uniform, analyzable race chain:

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
3. **Capability enforcement (§9)** — the flow may only use granted tools, reasoners, memory scopes, and MCP servers. A capability manifest (YAML/dict) also supplies **contract assertions**: the only way a non-read tool becomes legal inside a race.
4. **Race admission (§5)** — every branch of a `race`/`hedge`/`quorum` must be read-only or contract-asserted idempotent, so a duplicated branch can do no harm. MCP "read-only" *hints* are untrusted — a tool must be **asserted** in the capability manifest to race.

`freeze`, `validate`, and the §8/§9/§5 checks are all exposed individually for finer control.

---

## Execution on Temporal

The execution layer is the only part that imports `temporalio`, and it does so behind a guarded import.

- **`FlowWorkflow`** walks the frozen IR. The same deterministic interpreter (`composable_agents.execution.interpreter.interpret`) runs here and in tests; only the injected `Env` differs (Temporal activities vs. in-memory callables). It verifies deploy-pinned pure source hashes via `verifyPures` at workflow start, before running the interpreter. Per-tool retry policy is derived from each frozen contract — reads/idempotent tools retry liberally; non-idempotent writes retry cautiously behind an `Idempotency-Key` the `callTool` activity sends. Policy-decision errors (`CapabilityDenied`, `PlanRejected`, `ValidationError`, `FreezeError`, `PureDriftError`) are non-retryable.
- **`AgentWorkflow`** is the `app` loop. It is bounded by construction: each round the controller returns one of a closed action set — *finish*, *escalate*, call one **granted** tool, or invoke one registered **sub-flow** — and a **budget guard** stops the run before any action that would exceed the capability budget. History growth is bounded by **continue-as-new** (a configurable seam). It is a separate workflow precisely so its continue-as-new truncates only the agent's history, not the parent flow's.
- **`SessionWorkflow`** is the durable **session** loop (`Op.LOOP`): it `recv`s messages (a Temporal **Update** that acks or rejects `ChannelFull`), runs the turn flow, drains a normalized event log to `events()`, and persists the typed carrier via `SessionStore` (cursor = segment) so state survives **continue-as-new**. `agent.open(backend="temporal")` deploys it through the same `target="session"` capability/budget guards as a flow. See [docs-site/content/docs/guides/sessions.md](docs-site/content/docs/guides/sessions.md).
- **`Sub`** is a child `FlowWorkflow` resolved by `ref`; the firewall is structural (the surface shape is already opaque), so a child's value crosses while its shape does not. Child flows verify their own pure pins when the subflow registry entry supplies `pureSourceHashes`/`pinnedPures`; pins are not inherited from the parent.
- **Human gates** are a `submitHuman` signal plus a durable `wait_condition`. Two queries support a review UI: `projection` (the full pomset snapshot — events, `costByShape`, `pending`) and **`openGates`** (the precise activation ids currently parked on a gate — exactly what to signal, excluding structural `seq`/`par` activations).

`run_flow` / `start_flow` are client helpers; `build_worker` / `run_worker` host the workflows and the six activities (`verifyPures`, `callTool`, `invokeReasoner`, `compilePlan`, `resolveSubflow`, `resolveAgentSpec`).

Going to production is the same deploy artifact plus a worker process that wires the environment once:

```python
from composable_agents import (
    Reasoner,
    call,
    deploy,
    mcp,
    seq,
    snapshot_from_listings,
    think,
)
from composable_agents.registry import DEFAULT_REGISTRY

# Combinator-kernel + snapshot deploy has no reasoners=[obj] collection point, so
# register the reasoner directly and reference it by name with think("summarize").
DEFAULT_REGISTRY.register_reasoner(Reasoner(name="summarize", model="claude-...", system="Summarize."))
flow = seq(call(mcp("search", "web")), think("summarize"))
snapshot = snapshot_from_listings(
    {
        "search": {
            "web": {
                "inputSchema": {"type": "object"},
                "annotations": {"readOnlyHint": True, "idempotentHint": True},
            }
        }
    }
)
deployment = deploy(flow, snapshot)


async def run_on_temporal(client: object) -> object:
    return await deployment.run(
        client,
        session_id="run-1",
        input={"q": "temporal vs dbos"},
    )
```

A worker hosts the workflow + activities:

```python
from typing import Any

from composable_agents import Reasoner
from composable_agents.registry import DEFAULT_REGISTRY
from composable_agents.execution.worker import run_worker


async def my_async_mcp_caller(
    server: str,
    tool: str,
    value: Any,
    idempotency_key: str | None,
) -> Any:
    return {"server": server, "tool": tool, "value": value, "key": idempotency_key}


async def my_async_llm(reasoner: str, value: Any) -> Any:
    return {"reasoner": reasoner, "value": value}


DEFAULT_REGISTRY.register_reasoner(Reasoner(name="summarize", model="claude-...", system="Summarize."))


async def serve_worker() -> None:
    await run_worker(
        target_host="localhost:7233",
        tool_urls={"native_tool": "https://my-tool.run.app"},
        mcp_call=my_async_mcp_caller,
        llm=my_async_llm,
        capabilities=None,
    )
```

Temporal activity retries re-use the same deterministic activation `cid`, so `callTool` passes a stable idempotency key to both native HTTP tools and MCP callers. MCP transports therefore carry the key required for `required` idempotent tools to be admitted.

---

## Staged plans and plan extraction

`stage(planner=...)` lets a reasoner emit a plan at runtime. The plan is parsed, **admitted under §8** (it may loop but not itself stage or app, must use only granted tools, and must fit the budget), then run as ordinary IR. Because an admitted plan is not re-frozen, its calls are **late-bound** by tool ref at execution time (`call_ref_key` / `call_contract`).

The offline complement is **plan extraction**: an observed agent action trace can be generalized into a candidate plan (`generalize_trace_to_plan`), checked (`extract_plan`), and promoted to a cheap, replayable stage (`promote_plan`, which enforces admission). The agent discovers a procedure; the plan freezes it.

---

## The pure core vs. the Temporal layer

This split is deliberate and load-bearing:

- **Pure core** (`kinds`, `ir`, `shapes`, `contracts`, `freeze`, `validate`, `define`, `typed`, `dsl`, `derived`, `capabilities`, `staged`, `projection`, `dotctx`, `agent_loop`, `deploy`, and `execution.interpreter`) has **no Temporal dependency**. The interpreter takes an injected `Env` of effect handlers and concurrency primitives, so the same control-flow logic runs under Temporal *and* under an in-memory `InMemoryEnv` in tests.
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
  define.py         define-by-construction @flow frontend
  typed.py          typed authoring escape hatch over the same IR
  dsl.py            structural combinators + Contract helpers
  derived.py        race/hedge/quorum/map/vote/human_gate + §5 admission
  capabilities.py   §9 capability manifest, budget, grants, overrides
  staged.py         §8 plan cost estimation + plan admission
  projection.py     pomset events, value store, in-memory/Postgres sinks, OTel data
  resilience.py     provider fallback policy, error taxonomy, circuit breaker
  dotctx.py         §3.2 Reasoner definitions and lowering to Think nodes
  agent_loop.py     P4 agent loop logic + plan extraction (pure)
  agent.py          Agent facade + @tool decorator + Agent.open (sessions)
  session.py        sessions: scan/loop/@session, recv/emit, SessionHandle (local), SessionEvent
  deploy.py         the compile pipeline + Deployment artifact
  errors.py         the error taxonomy
  execution/
    interpreter.py  the deterministic IR interpreter + InMemoryEnv (pure)
    harness.py      FlowWorkflow, AgentWorkflow, SessionWorkflow, Temporal Env, client helpers
    activities.py   callTool / invokeReasoner / compilePlan / resolve* activities
    session_store.py durable session carrier store (cursor-CAS, claim-check codec, blobs)
    cma_session.py  CMA per-turn SessionHandle backend
    worker.py       Client + Worker wiring
    serve.py        container worker entrypoint (env config, SIGTERM drain, probes)
    debounce.py     dispatch-layer batch collator (Temporal signal-with-start)
    otel.py         OpenTelemetry export of the projection
```

---

## License

This project is licensed under Apache-2.0. See [LICENSE](LICENSE).
