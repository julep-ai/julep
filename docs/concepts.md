# Concepts

This is the conceptual reference for composable-agents. It expands the mental
model in the [README](../README.md) and points to [SPEC.md](SPEC.md) for
normative rules. The spec is the source of truth; this page explains the shape
of the system rather than restating every MUST.

## North star

> A flow is a frozen, typed, capability-bounded IR tree whose dynamic escape
> hatches can only choose *structure* over *already-authorized effects*.

That sentence is the framework's contract ([SPEC §1](SPEC.md#1-north-star)).
The model may choose a branch, emit a bounded plan, or drive an agent loop, but
those choices are made inside an already frozen tool surface and an already
granted capability envelope. What this buys is separability: control flow can be
durable and replayable, tool authority can be reviewed before deploy, and the
observable trace can explain decisions without becoming the source of recovery.

## The three planes

The runtime has three planes ([SPEC §3](SPEC.md#3-architecture--three-planes)):

```text
          frozen JSON IR + manifest + capabilities
                              |
                              v
Control       deterministic interpreter walks the IR
              Temporal workflow, or the same interpreter under InMemoryEnv
                              |
                 schedules activities through Env
                              v
Brains+Hands  Think activities and stateless tool activities
              LLM calls, MCP tools, native HTTP hands; all IO lives here
                              |
                  derived from execution history
                              v
Projection    append-only pomset view: causal events, costs, spans, gates
              derived observability, never durability
```

The control plane owns ordering and continuation. Brains are `ThinkStep` leaves
rendered from named brain definitions. Hands are `CallStep` leaves against
native tools or MCP tools. Projection is a derived pomset view
([SPEC §11](SPEC.md#11-projection)): it is useful for value stores, cost by
shape, OTel spans, replay UI, and open human gates, but correctness and recovery
come from workflow history, not from the projection store
([SPEC §2 invariant 6](SPEC.md#2-invariants-normative)).

## The IR is a frozen tree

Authoring surfaces emit a finite `Node` tree. The core node operators are
`prim`, `ident`, `arr`, `seq`, `par`, `each`, `alt`, `iter_up_to`, `eval_plan`,
and `app`. `prim` carries one of three step kinds: `call`, `think`, or `sub`.
`par` may carry a merge policy (`all`, `race`, `hedge`, or `quorum`); `each`
fans its body out over a runtime list ([SPEC §8.12](SPEC.md#812-each-dynamic-fan-out)).

Freeze turns the authored tree into canonical JSON: cycles are rejected, shared
host-language objects are unshared through a JSON round-trip, ids are normalized
to deterministic paths such as `$.L` and `$.R`, and every tool call is bound to
a frozen manifest entry. Canonical JSON is strict, compact, and sorted
([SPEC §6.3](SPEC.md#63-canonical-json-is-strict)); the deployment artifact hash
identifies the intended program ([SPEC §6.2](SPEC.md#62-artifact-hash)).

The frozen IR is not just a Python implementation detail. The golden corpus
pins the language-neutral wire contract: input flow, frozen IR JSON, manifest,
validation diagnostics, and surface/closed shapes. See
[SPEC §13](SPEC.md#13-golden-corpus-cross-language-contract) and
[`tests/golden/`](../tests/golden/).

## The shape lattice

Every flow has an inferred `Shape`, ordered from cheapest to costliest in
`composable_agents.kinds.Shape`:

```text
Shape.PIPELINE < Shape.DATAFLOW < Shape.BRANCHING < Shape.FEEDBACK < Shape.STAGED < Shape.AGENT
```

The join is the maximum in that order. Composition cannot claim a cheaper shape
than its children or its operator floor ([SPEC §4.1](SPEC.md#41-shape-lattice)).

| Shape | Produced by | Static guarantee |
|---|---|---|
| `Pipeline` | `ident`, `arr`, `call`, `think`, `sub`, and `seq` of pipeline-shaped children | Straight-line control. The next continuation is known once the previous value exists. |
| `Dataflow` | `par`, `fanout`, `each`, `map_n`, `map_reduce`, `vote`, `review` | Concurrent fan-out/fan-in exists. `par`-family branches are structurally present before execution; `each` has one structural body whose fan-out width is the runtime list length (so it is never admissible in a staged plan). |
| `Branching` | `alt` | A deterministic pure chooses one continuation, so the full set of possible continuations is still statically present. |
| `Feedback` | `iter_up_to` | A bounded loop owns the continuation across rounds; the bound keeps the tree analyzable. |
| `Staged` | `stage` / `eval_plan` | Runtime structure is model-produced and admitted before execution; the plan may be rich up to `Feedback` but may not stage another plan or open an agent loop ([SPEC §9](SPEC.md#9-staged-plans)). |
| `Agent` | `app` | The top of the lattice: an open-ended controller loop with a closed action vocabulary and budget guard ([SPEC §10](SPEC.md#10-agent-loop)). |

There are two reads of the same tree ([SPEC §4.2](SPEC.md#42-surface-vs-closed-shape)).
`surface_shape` is what the parent scheduler sees. A `SubStep` is opaque at this
surface and costs `Pipeline`: the parent can schedule it as one child workflow
without inspecting the child. `closed_shape` is what budgeting and admission
see: the `SubStep.contract.shape` is charged without loading the child tree.

That gap is the Joined firewall, called the Sub firewall in the spec
([SPEC §2 invariant 5](SPEC.md#2-invariants-normative)). A sub-flow's value can
cross to the parent; its internal shape and projection do not leak upward.

The other leaf enums are part of the same contract surface. `Effect` is
`READ`, `WRITE`, `EXTERNAL`, `DANGEROUS`. `Idempotency` is `REQUIRED`, `NATIVE`,
`BEST_EFFORT`, `NONE`. `ContextScope` is `NONE`, `LOCAL`, `SUMMARY`,
`WHOLE_SESSION`. These drive retry shaping, race admission, and context
scheduling rather than being ambient runtime facts.

## The compile pipeline

Deploy is a fixed sequence of gates ([README](../README.md#the-compile-pipeline-deploy),
[SPEC §5](SPEC.md#5-compile-pipeline)). The deeper safety discussion belongs in
[capabilities-and-safety.md](capabilities-and-safety.md).

**Freeze.** `freeze` is pure: the live tool snapshot is an input, and the output
is a frozen tree plus a manifest. Native hands use declared contracts; MCP tools
are snapshotted with schemas, version, and annotations, but unasserted MCP hints
are conservative for admission. Every post-freeze `call` carries a `frozenHash`
into the manifest, and `app` inline tools are also resolved into the same
manifest surface.

**Validate.** `validate` checks structure and decidability: finite tree, unique
ids, per-op well-formedness, named registered pures for `arr` and `alt`,
manifest resolution after freeze, conservative schema compatibility across
typed `seq` edges, and the warning that `WHOLE_SESSION` context inside `par`
will degrade scheduling to sequential evaluation
([SPEC §8.2](SPEC.md#82-whole_session-degradation)).

**Capability enforcement.** `CapabilityManifest.enforce_compile` applies the
deploy-time allow-list. It gates tools, brains, model ids, memory scopes, MCP
servers and version pins, subflows, approval requirements, `maxCalls`, and app
inline grants. Absent sections are unconstrained; present-but-empty sections
deny all ([SPEC §7.1](SPEC.md#71-absent-vs-empty)). A granted tool can also
assert `(effect, idempotency)`, which is the trusted contract surface used by
freeze and race admission ([SPEC §7](SPEC.md#7-capabilities-deny-by-default)).

**Race admission.** The race family (`race`, `hedge`, `quorum`) lowers to a
`par` spine with a merge marker, then `check_race_admission` verifies the flat
branch set. A cancelled loser may already have touched the world, so branches
must be read-only or asserted `native`/`required` idempotent, and subflows inside
race branches are rejected because their effects are opaque. Runtime settlement
is success-based and cancels losers ([SPEC §8.3](SPEC.md#83-race--hedge--quorum)).

## Dynamic escape hatches

The two model-shaped escape hatches are `app` and `stage`. Both choose
composition at runtime; neither can widen effects
([SPEC §2 invariants 2-3](SPEC.md#2-invariants-normative)).

`app(controller, tools=..., subflows=..., budget=..., max_rounds=...)` is an
agent loop. The controller speaks a closed vocabulary: finish, escalate, call
one granted tool, or invoke one granted subflow. The budget is checked before
the controller call and before each action. Tool calls resolve through the same
frozen contracts used by ordinary flow calls, so retry and effect checks do not
fork between "flow mode" and "agent mode" ([SPEC §10](SPEC.md#10-agent-loop)).

`stage(planner=...)` asks a brain to emit a plan. The plan is parsed as IR,
bound to the parent frozen manifest, validated, checked for shape and budget,
and race-admitted before it runs ([SPEC §9](SPEC.md#9-staged-plans)). The
important distinction is that a staged plan may choose a procedure, but every
call must bind to an already frozen parent tool. Invented or ambiguous calls are
rejected. Plan extraction is the offline complement: an observed agent trace can
be generalized, checked, and promoted to a replayable plan; the agent discovers
a procedure, and the plan freezes it into ordinary IR.

## Typed authoring surface

The `composable_agents.typed` layer is a typed authoring surface over the same
IR. `Flow[In, Out]`, typed tools, `>>`, typed combinators, adapters such as
`as_type` / `expect`, and the `Agent` facade carry Python types while authoring,
then elaborate to the identical `Node` tree before freeze. Types do not enter
the wire format, do not weaken freeze isolation, and do not change the golden
IR contract. See [design/typed-flow.md](design/typed-flow.md).

## Pure core vs Temporal layer

The split is load-bearing, not packaging convenience. The pure core contains
the lattice, IR, shape analysis, contracts, freeze, validate, DSL, derived
combinators, capability checks, staged-plan admission, projection, dotctx,
agent loop, deployment artifact construction, and the deterministic
interpreter. It has no Temporal dependency.

The same interpreter runs under an injected `Env`: `InMemoryEnv` for tests and
plain asyncio, Temporal `Env` for durable execution. Workflow code remains
deterministic; non-determinism and IO live behind activities. The execution
layer binds that seam to Temporal workflows, activities, workers, and OTel. See
[deploy-temporal.md](deploy-temporal.md) for deployment, [getting-started.md](getting-started.md)
for first use, [examples.md](examples.md) for worked flows,
[README.md](README.md) for the docs index, [algebra.hs](design/algebra.hs) for
the algebra sketch, and [CONTRIBUTING.md](../CONTRIBUTING.md) for conformance
workflow.
