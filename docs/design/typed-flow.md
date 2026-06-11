# Typed Composable Flow — design

**Status:** implemented. Every phase was JSON-equality-gated; the golden corpus
never moved; the typed authoring layer sits entirely above the unchanged `Node`
IR.
**Scope:** a typed, composable *authoring* surface that unifies the `Agent`
facade and the combinator algebra, without changing the IR.

> **As-built (2026-06-04).** Modules: `typed.py` (`Flow`/`FlowLike`, `>>`, typed
> `seq`, typed `Tool` leaves, `par`/`alt`, affine `.named()`/`.renamed()`,
> derived local names), `flow_adapters.py` (`as_type`/`expect`, `any_edges`),
> `flow_registry.py` (`FlowRegistry` + collision policy), `result.py`
> (`Result(dict[str,Any], Generic[Out])` — typed *and* dict-compatible), plus
> `agent.py` (Agent is a `FlowLike`; pure construction + lazy freeze + hybrid
> eager checks + `.check()`; uniform Tool/Flow capabilities → `APP.tools`/
> `APP.subflows`; `.as_sub()` split). Notable deviations from the plan below:
> typed `par` returns `Flow[In, Any]` (re-type via `as_type`) rather than a
> reducer-named type; `alt` is typed only in its binary form; a plain-`Flow`
> capability is the parent's *own* authored logic over the parent's granted tools
> (and is compiled through the deploy gates before running — the P1 fix), while a
> **sub-Agent** is the independent-authority/attenuation boundary; the Temporal
> cross-worker execution of `.as_sub(queue=…)` is a documented seam (the `queue`
> is carried for the durable layer; local run is unchanged). The new run-result
> lives at `composable_agents.result.Result` (the top-level `Result` stays the
> execution interpret-result).

---

## 1. Motivation

Two authoring tiers exist today and neither is what we want:

- **The `Agent` facade** is ergonomic (typed tools, `.run()/.deploy()`) but a
  **terminal object**: you build it and run it. It does not compose — you can't
  `seq`/`par`/`sub` an `Agent`, nest it, or have one agent use another. It's a
  "hunky" create-and-run object.
- **The combinators** (`seq/par/alt/iter_up_to/stage/app/sub`, `race/hedge/
  quorum/human_gate`) *are* the composable algebra, but they reference brains/
  tools/sub-flows by **string name**, losing the two things the OOP style gives:
  import resolution (jump-to-def, find-refs, rename-safety) and static type
  checking.

**Goal.** One currency that is *both* composable and typed/import-resolved.
Components should be **intermixable, composable, and decomposable**: recombine in
new ways, scale parts independently, and borrow parts across agents.

## 2. North star (and the one hard rule)

A typed wrapper **`Flow[In, Out]`** that **elaborates to the existing `Node` IR
and disappears before freeze**. Types live only in the authoring layer; the frozen
tree stays pure JSON, content-addressed, replayable, and cross-language — exactly
as today. The current DSL is already pure sugar over `Node`; `Flow[In,Out]` is the
next layer *above* it, never a mutation of the IR.

**Hard rule (freeze isolation):** a `Flow` value carries no executable payload
into the frozen representation. Every Python callable must already be a *named*
tool / pure / brain / sub before freeze. All naming, hashing, routing, and
type-resolution happen **before** workflow start; workflow code keeps seeing only
`Node` + manifest + contracts + refs + JSON values.

**Honesty over false safety:** Python typing cannot make agent/LLM/JSON output
safe. The design makes `Any` edges **loud** (a lint + explicit adapters), it does
not hide them.

## 3. The model

Everything is a `Flow[In, Out]` value:

| Building block | Is a | Lowers to |
|---|---|---|
| `Tool[In,Out]` (a `@tool`) | typed leaf | `call(ref)` (`CallStep`) |
| a brain / `think` | leaf | `think(brain)` (`ThinkStep`) |
| `Agent(...)` | `Flow[Any,Any]` | `app(controller, tools=, subflows=, ...)` |
| a composed pipeline | `Flow[In,Out]` | `seq/par/alt/...` nodes |
| a named/split component | `Flow[In,Out]` | `sub(ref, contract)` |

`Agent(...)` and `app(...)` **converge**: an agent is a flow value with `.run/
.deploy` conveniences that also nests as a node.

## 4. Typing (hybrid, typed edges)

- **`>>` is the precise binary primitive.** `Flow[I,M] >> Flow[M,O] -> Flow[I,O]`
  (mypy threads the TypeVars through `__rshift__`).
- **`seq(...)` is canonical at the IR level** and is overloaded up to a practical
  arity (~8) with a final `*flows: Flow[Any,Any] -> Flow[Any,Any]` fallback. `>>`
  and `seq` lower through the **same left-fold** (today's `_binary`).
- **Leaves are typed**; composition is checked where Python allows; the agent/LLM/
  JSON boundary is honestly `Any`.
- **`Any`-edge lint:** a marker/lint surfaces `Flow[Any,T]`, `Flow[T,Any]`, and
  especially `Flow[Any,Any]` — "this edge crosses an agent/LLM/JSON boundary."
- **Explicit boundary adapters** re-type and give validators a schema to check:
  `agent >> as_type(Ticket) >> classify` (or `agent.expect(Ticket)`).

```python
triage = search >> classify          # Flow[Query, Priority]
triage = seq(search, classify)       # identical lowering
plan   = fetch >> inbox >> notify    # inbox: Flow[Any,Any] -> the >> edges are Any (lint-marked)
typed  = inbox >> as_type(Triage) >> route   # boundary made explicit
```

## 5. Composition surface

Functional combinators are canonical; **`>>` is the only operator**.
`par/alt/race/hedge/quorum/iter_up_to/stage` stay named functions (operator soup
ages badly on capability-bearing code).

**`par` is typed via its reducer** (no anonymous tuples downstream):
`par(branches, join=reducer) -> Flow[I, R]` where `reducer` produces the named
output type `R` — consistent with `race`/`quorum`'s existing `reduce`.

## 6. Components are values: tools, identity, registry

- **Tools are multi-arg.** You write `def book(hotel: str, nights: int) -> Conf`;
  the framework derives the object input schema and packs/unpacks the single
  threaded IR value into kwargs at the hand boundary. `Flow`'s `In` is the packed
  shape; the IR still threads one value (contract unchanged).
- **Brains are values too.** Reference-by-value extends to brains:
  `Agent(brain=claude_sonnet)` / `think(claude_sonnet)` take an imported `Brain`
  value (import-resolved, rename-safe), not a string model-id. They still lower to
  the brain *name* in the IR.
- **Identity is derived, opt-in nameable.** Anonymous flows get a content-hash
  *local* name (debug/inline/one-shot artifacts only). `.named("ref.v1")` mints a
  **durable** ref.
  - **`.named()` is affine, not sticky.** Any `with_/replace/without` that changes
    structure/tools/brain/contracts/budget/instructions **drops the name** by
    default; `.renamed(...)` (or `.named(..., replace=True)`) reasserts identity
    intentionally. (A durable name surviving a structural mutation would make
    content-addressing dishonest.)
  - **Rule:** anonymous → may inline; named → may be referenced; **split → must be
    named.**
- **A `FlowRegistry`** backs named flows/sub-flows (today `sub(ref)` is just a
  string). Names live in one space with a **collision policy**: tool-ref vs
  sub-ref vs brain-name collisions are detected and **fail deploy**.

## 7. Capabilities, flow-as-tool, sub-agents

An agent's capabilities are a **uniform list** of Tools and Flows; it is authoring
sugar that lowers to the **existing** split:

```
Tool[...]                 -> APP.tools    += toolref_key(...)   -> controller emits {"tool": "..."}
Flow[...] (stable ref)    -> APP.subflows += ref                -> controller emits {"sub":  "..."}
```

The controller never sees one ambiguous "capability" namespace; the closed CALL/
SUB vocabulary is preserved. Flow-as-tool feeds the **same** capability fields the
compile checker already enforces (`capabilities.enforce_compile`), so attenuation
is unchanged. **Sub-agents fall out**: an agent *is* a flow, a flow can be a
capability, so an agent can be a sub-agent — attenuated (child ≤ parent), no
special-case concept.

## 8. Agent: pure construction, lazy freeze (with cheap eager checks)

`Agent(...)` returns `Flow[Any,Any]` + `.run/.deploy`. **Construction is pure**
(build the IR, hold the parts); **`.deploy()`/`.run()` performs the freeze**
(today `Agent.__init__` freezes eagerly — split that). `Agent` does not pretend to
be typed unless the user supplies schemas/adapters.

**Hybrid validation.** Construction does no freeze/snapshot work, but runs the
**cheap checks the in-hand values already make possible** — e.g. a `dangerous`/
approval-required tool in an agent's capability list, duplicate/colliding
capability names, or an unknown effect are rejected *at construction* (the `Tool`
values carry their contracts; no snapshot needed). Checks that require the
snapshot/manifest — tool resolution, MCP version pins, race admission, pure
registration, approval-gate dominance across the whole tree — run at `.deploy()/
.run()`. `.check()` forces the full validation without executing.

## 9. Decompose & recombine

Components are immutable values. Read parts (`a.tools`, `a.brain`) and derive
variants ergonomically:

```python
base = Agent(brain=claude, tools=[lookup, classify])
pro  = base.with_tools(add=[escalate]).replace(brain=opus)   # name dropped (affine)
lite = base.without(classify)
parts = base.tools          # plain access; share across agents
```

Plain reconstruction always works (`Agent(brain=base.brain, tools=[*base.tools, x])`).

## 10. Scaling: per-component, inline or split

Inline by default. `.as_sub(queue=...)` promotes a **named** child to its own
worker/task-queue. The split child carries **its own frozen manifest/capability
artifact**; the parent only authorizes "may invoke child X" (ref + contract +
granted subset) and **never smuggles the child's internal tool authority upward**
— the A4/C3 attenuation lesson, made structural. Same code, two topologies.

> `SubStep` today carries only `ref` + `SubContract`. Split deployment needs a
> deployment artifact (child ref, contract, grant subset on the parent side; a
> full frozen manifest/capability artifact on the child side).

## 11. Result

`.run()` → `Result[Out]`: `r.output` (typed `Out`; `Any` for an agent edge),
`r.trace`, `r.cost`, `r.status`. One return type that is both the typed answer and
full observability, and a typed handle even where the edge is `Any`.

## 12. Invariants preserved (the checklist)

- **Freeze isolation** — `Flow` has no frozen executable payload; freeze still
  round-trips `flow.to_json()` / `Node.from_json()`.
- **Closed vocabulary** — uniform capabilities lower to `APP.tools` / `APP.subflows`;
  CALL vs SUB stays distinct.
- **Capability attenuation** — flow-as-tool feeds the existing capability fields,
  not a third list; split never widens authority.
- **Golden / cross-language** — `Flow[In,Out]` never appears in JSON; **tested by
  asserting the typed layer emits byte-identical JSON to today's DSL**. Golden
  hashes must not move unless intentionally changed.
- **Deterministic workflow** — all naming/hashing/routing/type-resolution happen
  before workflow start; no introspection or closures in workflow code.
- **Additive / coexist** — string combinators and the current facade keep working
  unchanged; typed values are the preferred surface; migration is gradual.

## 13. Transparency

An **elaboration report** for each typed `Flow`: emitted IR node kinds, tool refs,
sub refs, inferred schemas, dropped names, `Any` edges, and inline/split choices —
catching what the type checker cannot.

## 14. Phasing (conservative; JSON-equality gated)

1. `Flow[In,Out]` as a pure wrapper over `Node` (`to_ir()`, `>>`). No `Agent`
   changes.
2. Typed `Tool[In,Out]` leaves + `seq` overloads. **Assert emitted JSON == current
   DSL.**
3. `Any`-edge lint + explicit `as_type`/`expect` adapters.
4. Refactor `Agent` construction to be pure, returning `Flow[Any,Any]`; keep
   `.run/.deploy`.
5. `FlowRegistry` + `.named()` discipline (affine; explicit names for `sub`/split).
6. Flow-as-tool lowering to `APP.subflows` + collision checks + attenuation tests
   (inline vs split).
7. Per-component split / task-queue controls.

**Success criterion (conservative):** typed authoring catches obvious edges,
elaboration stays transparent, and frozen JSON / golden hashes do not move unless
intentionally changed.

## 15. Decisions log

1. Typing: **hybrid typed edges** (typed leaves; composition-checked; `Any` at
   agent/LLM/JSON with opt-in re-typing).
2. Syntax: **functional + `>>` sugar** (only `>>` as an operator).
3. Compose: **agent-as-node, flow-as-tool, decompose-&-share**.
4. Scaling: **per-component** inline-or-split.
5. Identity: **derived, opt-in nameable**; **affine** naming; **split requires a
   name**.
6. Flow-as-tool: **uniform capability list** → `APP.tools`/`APP.subflows`.
7. Decompose: **plain access + `with_/without/replace`**.
8. Sub-agents: **via flow-as-tool** (attenuated).
9. `.run()` → **`Result[Out]`**.
10. Tools: **multi-arg, framework-packed**.
11. Coexistence: **additive**.
12. `par`: **reducer → named type**.
13. Brains are **first-class typed values** (reference-by-value), like tools/flows.
14. Construction is **lazy/pure with cheap eager checks** (`.check()` forces full
    validation); full freeze-time gates run at `.deploy()/.run()`.
15. Explicit **`as_type`/`expect` adapters** at `Any` boundaries are kept (not
    auto-inserted) — the unsafe edge stays visible.

## 16. Open questions / deferred

- Exact adapter spelling (`as_type(T)` vs `agent.expect(T)` vs both) — concept
  confirmed; spelling open.
- `seq`/`par` overload arity before the `Any` fallback.
- Which checks are cheap enough to run eagerly at construction vs deferred to
  freeze (the §8 hybrid line) — the exact split.
- Multi-arg packing edge cases (optional/variadic params, defaults).
- Whether the elaboration report is a CLI command, a `Flow.explain()` method, or
  both.

## 17. Non-goals

- Changing the IR, the freeze/replay contract, or the golden/cross-language
  hashes.
- Typed safety across the agent/LLM/JSON boundary (made explicit, not eliminated).
- Operators beyond `>>`.
