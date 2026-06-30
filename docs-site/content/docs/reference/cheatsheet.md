---
title: "Cheat-sheet"
description: "A dense quick reference for the @flow surfaces, registration, deploy/dry_run, the Agent facade, and the CLI."
---

Dense quick reference for `@flow` authoring. For the workflow see the
[Team Guide](/docs/development/team-guide); for the why see [Concepts](/docs/concepts/model); for the
normative contract see [SPEC](/docs/internals/specification).

## Install & extras

```bash
pip install composable-agents                 # authoring + compile + local run (no key)
pip install 'composable-agents[temporal]'     # durable execution on Temporal
pip install 'composable-agents[dbos]'         # durable execution on Postgres/DBOS
pip install 'composable-agents[providers]'    # multi-provider LLM (any-llm)
pip install 'composable-agents[http,otel]'    # native HTTP tools + OTel export
pip install -e '.[dev]'                        # contributing: tests + lint + types
```

Extras: `temporal` · `dbos` · `http` · `cma` · `dotctx` · `providers` · `otel`
· `store` · `wasm` · `dev`. Runtime flags: `composable_agents.HAVE_TEMPORAL`,
`HAVE_DBOS`. Python **3.12+**.

## `@flow` surfaces

| Surface | Form | Lowers to |
|---|---|---|
| Tool / pure / sub-flow step | `out = my_tool(h, retries=2, timeout_s=5)` | one graph step |
| Reasoner step | `out = think("reasoner_name", h, timeout_s=10)` | `Think` step |
| Merge records | `left \| right` | `std.merge` |
| Pluck a field | `h["key"]` | `std.pluck` |
| Binary branch | `cond(pred, subject, then=..., orelse=...)` | Branching |
| Multiway branch | `switch(selector, subject, cases={...}, default=...)` | Branching |
| Fan-out | `each(body, items, max_parallel=3, reducer=...)` | Dataflow |
| Terminal reschedule | `reschedule(state, after_s=60, mark=...)` | continuation |

- The `@flow` body runs **once at define time** with `Handle` values; a step
  call appends graph structure, it does not execute.
- Return a `Handle` produced by the graph. Every parameter must be used.
- Per-step execution options: `retries=`, `retry_interval_s=`, `backoff_rate=`,
  `timeout_s=`. The frozen graph owns them, so interpreter and durable backends
  agree.
- `each` body item parameter is **positional**; enclosing handles/constants are
  **keyword captures**. `cond`/`switch` arm's leftover parameter must match the
  subject handle's label; other values are keyword captures.

## Declaring the pieces

<!-- ca:doctest skip -->
```python
@tool(effect="read", idempotent=True)          # effect: read | write | external | dangerous
def lookup(ticket: str) -> dict[str, str]: ...  # schemas inferred from type hints

@pure("ticket_prompt")                          # register by stable name; raw source is hashed
def ticket_prompt(hit: dict) -> dict: ...

SUPPORT_REPLY = Reasoner(
    name="support_reply",
    model="anthropic:claude-haiku-4-5-20251001",
    system="...",
    reply=SupportReply,                         # a TypedDict reply schema
)
```

Decorate the **raw** function — never a wrapper, closure, or lambda (pins are
source hashes). [Determinism contract →](/docs/guides/authoring-flows#determinism-contract)

## Compile + run a `@flow` locally

<!-- ca:doctest skip -->
```python
deployment = deploy(flow, tools=[...], reasoners=[SUPPORT_REPLY])   # -> Deployment; strict by default
deployment = deploy(flow, tools=[...], mode="dev")        # warn + continue while iterating

result = deployment.dry_run(input, reasoners={"name": fake_fn})   # keyless, deterministic
print(result.value)                                              # the produced value
print(deployment.prod_gap_summary())                             # what strict prod would block
```

`dry_run(...)` returns the **interpreter `Result`** (a dataclass), *not* the
facade `Result` below: `.value` (produced value), `.reported_cost`, `.event_id`,
`.attrs`. `dry_run` requires `deploy(..., tools=...)` so it can bind native tools.

## `Agent` facade (controller loop)

<!-- ca:doctest skip -->
```python
agent = Agent(reasoner="claude-sonnet-4-6", tools=[...], llm=controller,
              budget_cost=8.0, max_rounds=8, instructions="...", mode="dev")
result = agent.run(input)              # or:  await agent.arun(input)
```

`agent.run(...)` returns the **facade `Result`** — a dict subclass with attribute
access (`result.status` **or** `result["status"]`):

| Field | Meaning |
|---|---|
| `.output` | terminal value |
| `.status` / `.ok` | terminal status / success bool |
| `.trace` | append-only step trace |
| `.cost` | terminal cost (abstract units, not dollars) |
| `.rounds` | agent-loop rounds taken |
| `.reason` | terminal reason / failure detail |
| `.prod_gap` | what strict production would block (dev mode) |

- `llm` is `(reasoner_name, payload) -> reply`. `payload` has `"input"` and the
  append-only `"trace"`. Reply: `{"tool": "<granted>", "input": v}` to call a
  tool, `{"output": v}` to finish.
- Omit `llm` → keyless default reasoner: emits one `RuntimeWarning` and returns
  input unprocessed. ([why](/docs/guides/gotchas#keyless-default-reasoner))
- Multi-provider: `pip install 'composable-agents[providers]'`, then
  `llm=make_local_reasoner()` (from `composable_agents.execution.llm`) and
  `reasoner="openai:gpt-4o"` / `"gemini:gemini-2.5-flash"` / etc.
- Durable: `agent.deploy(client, session_id=..., input=...)`.

## Sessions (long-lived, keep-messaging)

- Author a turn loop: `scan(step, init)` (step `(carrier, msg) -> (carrier', output)`), `loop(body, ...)`, or `@session` straight-line sugar. `recv`/`emit` are the channel leaves.
- Open + drive: `handle = await agent.open(session=chat, backend="local"|"temporal"|"cma")`; then `await handle.send(msg)`, `async for ev in handle.events()` (`Emit`/`Turn`/`Error`/`Closed`), `await handle.state()`, `await handle.close()`.
- CLI: `ca chat <agent>` / `ca trigger <agent> <event>` / `ca listen <agent> --forward-to URL`.
- Full guide: [Sessions](/docs/guides/sessions).

## Combinator kernel (drop-down)

What `@flow` compiles to; reach for it for exact structure or a new frontend.

| Combinator | Shape | Meaning |
|---|---|---|
| `seq(a, b, ...)` | Pipeline | run in sequence, thread output→input |
| `par(a, b, ...)` / `fanout(...)` | Dataflow | concurrent on same input, collect |
| `each(body, max_parallel=, reducer=)` | Dataflow | body per list element, in order |
| `alt(pred, if_true, if_false)` | Branching | choose by registered pure predicate |
| `iter_up_to(max, body, until=)` | Feedback | iterate up to `max`, optional convergence |
| `stage(planner=)` | Staged | reasoner emits a plan → compiled, admitted, run |
| `app(controller, tools=, subflows=, budget=, max_rounds=)` | Agent | controller loop (use sparingly) |
| `sub(ref, contract=None)` | Pipeline (opaque) | opaque child flow across the firewall |

Leaves: `native(name)`, `mcp(server, tool)`, `call(ref)`, `think(reasoner)`,
`reasoner_from_ctx(path)`, `ident()`, `arr(pure_name)`.
Derived (lower to an analyzable race chain): `race(...)`, `hedge(..., hedge_ms=)`,
`quorum(..., k=)`, `map_n`, `map_reduce`, `vote`, `review`, `human_gate(prompt=, timeout_s=)`,
`delay(...)`. Leaves accept `ctx=` (`ContextPolicy`) and `ann=` (`Ann`: `cost_usd`,
caching, effects, `timeout_s`).

Typed escape hatch (`composable_agents.typed`): `as_flow(t).named("x.v1")`,
compose with `>>`; elaborates to the same IR and disappears before freeze.

## CLI (`composable-agents`)

| Command | Purpose |
|---|---|
| `validate <flow.json> [--manifest]` | validate a flow JSON artifact |
| `freeze <flow.json> <snapshot.json> [--caps]` | freeze a flow against a snapshot |
| `inspect <flow.json> [--manifest --caps]` | shape, node, manifest, capability data |
| `run <flow.json> <input.json> [--mode strict\|dev]` | run locally via the interpreter |
| `graph <flow.json>` | emit Graphviz DOT for the IR tree |
| `worker [--address --namespace --task-queue]` | host a durable worker (Temporal) |

## Common errors

`CapabilityDenied` · `PlanRejected` · `ValidationError` · `FreezeError` ·
`PureDriftError` · `AdmissionError` · `BudgetExceeded` · `RaceAllFailed` ·
`ResilienceExhausted` · `UnsupportedShapeError` · `PrincipalRequired` (all under
`ComposableAgentsError`). Define-time rewrites and what triggers them:
[Gotchas](/docs/guides/gotchas) · [Authoring Guide](/docs/guides/authoring-flows#define-time-errors).

<!-- ported-by ca-docs-site: reference/cheatsheet -->
