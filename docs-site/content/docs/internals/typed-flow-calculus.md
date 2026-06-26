---
title: "Typed Flow Calculus"
description: "The algebraic model behind the typed authoring surface."
---

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
  quorum/human_gate`) *are* the composable algebra, but they reference reasoners/
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
tool / pure / reasoner / sub before freeze. All naming, hashing, routing, and
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
| a reasoner / `think` | leaf | `think(reasoner)` (`ThinkStep`) |
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
  threaded IR value into kwargs at the tool boundary. `Flow`'s `In` is the packed
  shape; the IR still threads one value (contract unchanged).
- **Reasoners are values too.** Reference-by-value extends to reasoners:
  `Agent(reasoner=claude_sonnet)` / `think(claude_sonnet)` take an imported `Reasoner`
  value (import-resolved, rename-safe), not a string model-id. They still lower to
  the reasoner *name* in the IR.
- **Identity is derived, opt-in nameable.** Anonymous flows get a content-hash
  *local* name (debug/inline/one-shot artifacts only). `.named("ref.v1")` mints a
  **durable** ref.
  - **`.named()` is affine, not sticky.** Any `with_/replace/without` that changes
    structure/tools/reasoner/contracts/budget/instructions **drops the name** by
    default; `.renamed(...)` (or `.named(..., replace=True)`) reasserts identity
    intentionally. (A durable name surviving a structural mutation would make
    content-addressing dishonest.)
  - **Rule:** anonymous → may inline; named → may be referenced; **split → must be
    named.**
- **A `FlowRegistry`** backs named flows/sub-flows (today `sub(ref)` is just a
  string). Names live in one space with a **collision policy**: tool-ref vs
  sub-ref vs reasoner-name collisions are detected and **fail deploy**.

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
**cheap checks the in-tool values already make possible** — e.g. a `dangerous`/
approval-required tool in an agent's capability list, duplicate/colliding
capability names, or an unknown effect are rejected *at construction* (the `Tool`
values carry their contracts; no snapshot needed). Checks that require the
snapshot/manifest — tool resolution, MCP version pins, race admission, pure
registration, approval-gate dominance across the whole tree — run at `.deploy()/
.run()`. `.check()` forces the full validation without executing.

## 9. Decompose & recombine

Components are immutable values. Read parts (`a.tools`, `a.reasoner`) and derive
variants ergonomically:

```python
base = Agent(reasoner=claude, tools=[lookup, classify])
pro  = base.with_tools(add=[escalate]).replace(reasoner=opus)   # name dropped (affine)
lite = base.without(classify)
parts = base.tools          # plain access; share across agents
```

Plain reconstruction always works (`Agent(reasoner=base.reasoner, tools=[*base.tools, x])`).

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
13. Reasoners are **first-class typed values** (reference-by-value), like tools/flows.
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

## The algebra (algebra.hs)

The typed surface is backed by a small algebraic model. The full sketch follows verbatim.

```haskell
{-# LANGUAGE GADTs #-}
-- Composable, Algebraic Agents — revised cut (v2; pseudo-Haskell, illustrative, not meant to compile)
--
-- THESIS (sharpened): agents and workflows differ by WHO OWNS THE CONTINUATION.
--   workflow         : the continuation lives in the static control graph
--   dynamic workflow : the continuation is synthesized ONCE into a reified Plan, then the runtime owns it
--   agent            : the continuation stays under online model control
-- Managed Agents supply the deployment boundary (reasoners / tools / sessions / events / isolated
-- subagents); this calculus exposes exactly those boundaries and no more.
--
-- WHAT CHANGED FROM v1 (and why):
--   * Tier -> Shape. We never measured determinism. A Think is stochastic, a Call can fail — none of
--     that changes whether the CONTROL TOPOLOGY is schedulable. Shape measures schedulability.
--   * + Staged / Plan. Dynamic workflows are NOT App: the script is generated, frozen, inspectable,
--     rerunnable, and a runtime (not the model turn-by-turn) owns the loop. That is its own shape.
--   * Think carries its context dependency explicitly (no hidden global session read), so :*** is
--     honestly parallel and the Session can be a partial order.
--   * Bounded loops are schedulable, not success-total (IterUpTo returns Either).
--   * Tools are typed up top, erased to the universal tool interface at the boundary.

module AlgebraicAgents where

type Name   = String
type NodeId = String
type CallId = String
data Value                                  -- opaque payloads at the boundary
data Schema a                               -- output-format / input type of a primitive
data Crit                                   -- a critique / correction carrier (loop state)


-- ============================================================
-- Shape — control-topology schedulability (NOT determinism)
-- ============================================================
data Shape
  = Pipeline    -- static sequence
  | Dataflow    -- static independent product / fanout
  | Branching   -- finite, known branch universe
  | Feedback    -- statically bounded recurrence
  | Staged      -- runtime-generated, then FROZEN, schedulable workflow   (dynamic workflow)
  | Agent       -- online synthesized continuation / unbounded control
  deriving (Eq, Ord, Show)
-- cuts:  buildTimeWorkflow = shape <= Feedback ;  dynamicWorkflow = Staged ;  onlineAgent = Agent


-- ============================================================
-- Primitives  (typed up top; the "hole" is the awaited result slot)
-- Step is profunctor-SHAPED (an input slot + an output slot). It is NOT itself a lawful
-- profunctor; the free arrow over Step supplies the compositional structure.
-- ============================================================
data Tool  i o = Tool  { toolName :: Name, inSchema :: Schema i, outSchema :: Schema o }
data Reasoner x y = Reasoner { reasonerName :: Name, promptSchema :: Schema x
                       , replySchema :: Schema y, ctxPolicy :: ContextPolicy }

-- The model's dependency on prior context is DECLARED, not smuggled in from global state.
data ContextPolicy = NoCtx | LocalThreadCtx | ParentSummaryCtx | WholeSessionCtx
  deriving (Eq, Ord, Show)

data    AgentRef x y  = AgentRef Name
newtype AgentContract = AgentContract { contractShape :: Shape }   -- what a sub promises, opaquely

data Step x y where
  Call  :: Tool  i o -> Step i o                       -- run a tool; the Output is the hole
  Think :: Reasoner x y -> Step x y                       -- model fills a typed hole from x + declared ctx
  Sub   :: AgentRef x y -> AgentContract -> Step x y   -- contract-bound delegation (closure)


-- ============================================================
-- Flow — the control algebra.  Shape = which constructors a term uses.
-- INVARIANT: Flow values are FINITE syntax trees. Recursion enters ONLY through IterUpTo (bounded),
-- EvalPlan (reified), or App (online) — never through host-language knots (let f = f :>>> g ...).
-- ============================================================
-- Pure glue is NAMED so it can be shipped/inspected, not an opaque host closure.
data Pure x y = Pure { pureName :: Name, runPure :: x -> y }

-- A Plan is a finite, generated, inspectable workflow artifact.
-- INVARIANT: surfaceShape (unPlan p) <= Feedback  (its own wiring is a workflow); it MAY still
-- contain Sub nodes whose contracts are Agent — closedShape sees through to those.
newtype Plan x y = Plan { unPlan :: Flow x y }

-- Operational facts ride as annotations; they NEVER alter control shape. (cost/risk/cache/effect/...)
data Annotation = Annotation { costHint, riskHint, cacheHint, effectHint, timeout :: Maybe Value }
noAnn :: Annotation
noAnn = Annotation Nothing Nothing Nothing Nothing Nothing

data Flow x y where
  Prim     :: NodeId -> Annotation -> Step x y -> Flow x y
  Ident    :: Flow x x
  Arr      :: Pure x y -> Flow x y
  (:>>>)   :: Flow x y -> Flow y z -> Flow x z
  (:***)   :: Flow a b -> Flow c d -> Flow (a, c) (b, d)
  (:|||)   :: Flow a z -> Flow b z -> Flow (Either a b) z
  IterUpTo :: Word -> Flow (a, s) (Either s b) -> Flow (a, s) (Either s b)  -- bounded; NOT success-total
  EvalPlan :: Flow (Plan a b, a) b           -- generated-then-frozen workflow   => Staged
  App      :: Flow (Flow a b, a) b           -- online arbitrary continuation     => Agent


-- ============================================================
-- Shape analysis — two readings of the same term.
--   surfaceShape : Sub is OPAQUE (parent stays schedulable regardless of child internals).
--   closedShape  : Sub contributes its contract shape (the deployment may host an agent).
-- A parent can be a surface workflow while closing over an agent behind a Sub. Feature, not bug.
-- ============================================================
surfaceShape :: Flow x y -> Shape
surfaceShape f = case f of
  Prim _ _ _   -> Pipeline                   -- includes Sub: opaque at the surface
  Ident        -> Pipeline
  Arr _        -> Pipeline
  a :>>> b     -> surfaceShape a `max` surfaceShape b
  a :*** b     -> Dataflow  `max` surfaceShape a `max` surfaceShape b
  a :||| b     -> Branching `max` surfaceShape a `max` surfaceShape b
  IterUpTo _ g -> Feedback  `max` surfaceShape g
  EvalPlan     -> Staged
  App          -> Agent

closedShape :: Flow x y -> Shape
closedShape f = case f of
  Prim _ _ (Sub _ c) -> contractShape c      -- read the sub's promised shape
  Prim _ _ _         -> Pipeline
  Ident              -> Pipeline
  Arr _              -> Pipeline
  a :>>> b           -> closedShape a `max` closedShape b
  a :*** b           -> Dataflow  `max` closedShape a `max` closedShape b
  a :||| b           -> Branching `max` closedShape a `max` closedShape b
  IterUpTo _ g       -> Feedback  `max` closedShape g
  EvalPlan           -> Staged               -- static view; given a concrete Plan, recurse: closedShape (unPlan p)
  App                -> Agent

isBuildTimeWorkflow, isClosedWorkflow :: Flow x y -> Bool
isBuildTimeWorkflow = (<= Feedback) . surfaceShape
isClosedWorkflow    = (<= Feedback) . closedShape


-- ============================================================
-- Session — durable causal trace.  A free PARTIALLY-COMMUTATIVE monoid (a trace monoid / pomset):
-- independent branches have NO canonical left-before-right order. This is the honest upgrade of
-- v1's "free monoid" once :*** is real concurrency. Recovery folds the trace; the harness is cattle.
-- ============================================================
type EventId  = String
type ThreadId = String
newtype Session = Session [Event]            -- read as a pomset keyed by (eventId, causes)
data Event = Event
  { eventId :: EventId
  , node    :: NodeId
  , thread  :: ThreadId
  , causes  :: [EventId]                     -- causal parents = the partial order
  , kind    :: EventKind }
data EventKind
  = Planned CallId Name Value                -- INTENT logged before the effect (idempotent recovery)
  | Did     CallId Name Value Value
  | Asked   ContextPolicy
  | Said    Value
  | Joined  Value                            -- a child's SUMMARIZED result (not its scratch events)
  | Failed  Value


-- ============================================================
-- Harness — interpreter. Threads Tools (DI) and the trace.
-- Effectful calls are idempotent under replay via stable call ids + intent logging.
-- ============================================================
-- Tools take a CallId so replay can dedupe real-world side effects.
type Tools m = CallId -> Name -> Value -> m Value

run :: Monad m => Tools m -> Session -> Flow x y -> x -> m (y, Session)
run hs s flow x = case flow of

  Prim n _ (Call tool) -> do                 -- intent-log, then execute, unless already in the trace
    let cid = stableCallId n x
    case recall cid s of
      Just v  -> pure (out v, s)             -- replay hit: do NOT re-fire the effect
      Nothing -> do
        let s1 = append s (Planned cid (toolName tool) (box x))
        v <- hs cid (toolName tool) (box x)
        pure (out v, append s1 (Did cid (toolName tool) (box x) v))

  Prim _ _ (Think reasoner) -> do               -- context is the DECLARED projection, not a global read
    let ctx = project (ctxPolicy reasoner) s x
        s1  = append s (Asked (ctxPolicy reasoner))
    y <- decide reasoner x ctx
    pure (y, append s1 (Said (box y)))

  Prim n _ (Sub ref c) -> do                 -- child runs in its OWN session; parent sees a summary
    (y, child) <- runSub ref c x
    pure (y, append s (Joined (summarize child)))

  Ident        -> pure (x, s)
  Arr p        -> pure (runPure p x, s)
  a :>>> b     -> do (y, s1) <- run hs s a x; run hs s1 b y
  a :*** b     -> do                         -- independent BY CONSTRUCTION: fork, run, merge traces
        let (l, r) = x
        (bl, sl) <- run hs (fork "L" s) a l
        (br, sr) <- run hs (fork "R" s) b r
        pure ((bl, br), merge s sl sr)        -- merge = union of causal traces (partial order kept)
  a :||| b     -> either (run hs s a) (run hs s b) x
  IterUpTo k g -> iterUpTo hs s k g x
  EvalPlan     -> let (Plan p, a) = x in run hs s p a   -- runtime owns the FROZEN plan's loop
  App          -> let (g,      a) = x in run hs s g a   -- online: the next Flow arrived AS DATA

-- Reboot a crashed harness: same `run`; the replay cursor lives in `recall`, recovery is a fold.
wake :: Monad m => Tools m -> Flow x y -> Session -> x -> m (y, Session)
wake hs flow s x = run hs s flow x

-- LAW: a branch declaring WholeSessionCtx forfeits free parallelism; the analysis degrades that
-- :*** edge to sequential. Only NoCtx / LocalThreadCtx branches are freely parallelizable.

-- stubs (runtime concerns, deliberately outside the control algebra)
stableCallId :: NodeId -> x -> CallId;                                       stableCallId = undefined
recall    :: CallId -> Session -> Maybe Value;                               recall    = undefined
append    :: Session -> EventKind -> Session;                                append    = undefined
project   :: ContextPolicy -> Session -> x -> Value;                         project   = undefined
decide    :: Monad m => Reasoner x y -> x -> Value -> m y;                       decide    = undefined
runSub    :: Monad m => AgentRef x y -> AgentContract -> x -> m (y, Session); runSub    = undefined
summarize :: Session -> Value;                                               summarize = undefined
fork      :: ThreadId -> Session -> Session;                                 fork      = undefined
merge     :: Session -> Session -> Session -> Session;                       merge     = undefined
iterUpTo  :: Monad m => Tools m -> Session -> Word
          -> Flow (a, s) (Either s b) -> (a, s) -> m (Either s b, Session);  iterUpTo  = undefined
box :: x -> Value;  box = undefined
out :: Value -> o;  out = undefined


-- ============================================================
-- Combinator algebra — the named patterns (sharper than v1)
-- ============================================================
pipeline :: Flow x y -> Flow y z -> Flow x z
pipeline = (:>>>)

parallel :: Flow a b -> Flow c d -> Flow (a, c) (b, d)               -- scale-out
parallel = (:***)

fanout :: Flow a b -> Flow a c -> Flow a (b, c)
fanout f g = Arr (Pure "dup" (\a -> (a, a))) :>>> (f :*** g)

route :: Flow a (Either l r) -> Flow l z -> Flow r z -> Flow a z     -- finite specialization
route r l h = r :>>> (l :||| h)

critique :: Word -> Flow (a, Crit) (Either Crit b)
         -> Flow (a, Crit) (Either Crit b)                           -- bounded refinement
critique = IterUpTo

stage :: Flow p (Plan a b) -> Flow (p, a) b                          -- model-as-workflow-compiler
stage planner = (planner :*** Ident) :>>> EvalPlan

escalate :: Flow a (Flow a b) -> Flow a b                            -- model-as-online-controller
escalate chooser = fanout chooser Ident :>>> App

subagent :: AgentRef x y -> AgentContract -> Flow x y                -- contract-bound delegation
subagent ref c = Prim "sub" noAnn (Sub ref c)

-- vocabulary, by shape:
--   parallel = scale-out (Dataflow)      route    = finite specialization (Branching)
--   critique = bounded refinement (Feedback)
--   stage    = model writes a workflow, runtime freezes & runs it (Staged)  <- dynamic workflows
--   escalate = model keeps choosing the next arrow online (Agent)
--   subagent = contract-bound delegation (opaque at surface; closedShape reads its contract)


-- ============================================================
-- Laws / framing
-- ============================================================
-- 1. WHO OWNS THE CONTINUATION: workflow -> static graph; dynamic workflow -> a frozen Plan owned by
--    the runtime; agent -> the model, online. The Shape lattice is exactly this ownership axis.
-- 2. CONTEXT HONESTY: any read from global session state is a control dependency until DECLARED.
--    ctxPolicy makes it explicit; hidden global reads are the main source of semantic drift.
-- 3. :*** is independent BY CONSTRUCTION (forked sessions); WholeSessionCtx forfeits that.
-- 4. Bounded loops are schedulable, not success-total (IterUpTo returns Either).
-- 5. Effects are idempotent under replay (stable CallId + Planned-before-Did); recovery is a fold.
-- 6. Flow is FINITE syntax; recursion enters only via IterUpTo / EvalPlan / App.
-- 7. App is where static extraction stops (ArrowApply == Monad). EvalPlan is its safer cousin:
--    same runtime-control shape, but the data is a VALIDATED workflow artifact, not an arbitrary Flow.
```

<!-- ported-by ca-docs-site: internals/typed-flow-calculus -->
