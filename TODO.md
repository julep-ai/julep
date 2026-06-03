# Composable Serverless Agents — Specification

> **Canonical implementation:** Python (`composable_agents`).
> The IR is **language-neutral JSON**. Python is the reference frontend; other
> frontends MAY emit the same JSON later. This document defines the invariants
> every implementation MUST satisfy. Where the current code diverges, see
> [§12 Conformance](#12-conformance).

**Status:** reference implementation, hardening toward canonical.
**Spec version:** 0.1 · **Last updated:** 2026-06-03

Normative keywords (MUST / MUST NOT / SHOULD / MAY) follow RFC 2119.

---

## 1. North star

> **A flow is a frozen, typed, capability-bounded IR tree whose dynamic escape
> hatches can only choose *structure* over *already-authorized effects*.**

Every design decision resolves to this sentence. A model may pick composition
at runtime (which tools, in what shape, how many times within budget). A model
may **never** introduce a new effect, a new tool, a new capability, or a tool
whose contract was not authorized at deploy time.

---

## 2. Invariants (normative)

These are the non-negotiables. An implementation that violates any of them is
not conformant.

1. **Freeze isolation.** A frozen flow MUST NOT depend on live tool shape at run
   time. All schemas, contracts, and versions are snapshotted at freeze and
   addressed by content hash.
2. **Effects are authorized statically.** Every effect a run can produce MUST be
   traceable to a capability grant present at deploy time. Dynamic paths
   (staged plans, agent loops) MUST NOT widen the effect set.
3. **Staged plans choose composition, not effects.** A model-generated plan MUST
   bind every call to a tool already frozen in the parent deployment, inheriting
   that tool's real contract. Unbound or invented calls MUST be rejected.
4. **Concurrency settles on success.** `race`/`hedge`/`quorum` MUST settle on
   *successful* branches and cancel losers; a failed branch MUST NOT win or
   block a still-pending success. (See [§8.3](#83-racehedgequorum).)
5. **Sub is a one-way mirror.** A sub-agent's *surface* shape is opaque
   (Pipeline); its internal shape MUST NOT leak into the parent projection. Its
   *closed* shape charges the parent the sub's full contract.
6. **History is the source of truth; projection is derived.** Temporal workflow
   history is the durable record. The projection plane is a derived view and
   MUST NOT be required for correctness or recovery.
7. **Pures are named, deterministic, and hash-checked.** Pure functions used in
   control flow MUST be registered by name, MUST be deterministic, and their
   source hash MUST be verified against the deployment artifact before
   execution.
8. **Capabilities are deny-by-default where present.** A present-but-empty grant
   list means *deny all*, not *allow all*. Absent sections mean *unconstrained*.
   (See [§7.1](#71-absent-vs-empty).)
9. **Agents speak a closed vocabulary under a bounded budget.** The agent loop's
   action set is fixed (FINISH / ESCALATE / CALL / SUB). Every action is
   budget-checked *before* it is taken, including the controller call itself.
10. **Workflow code is deterministic.** No wall-clock, RNG, ambient IO, or
    non-canonical serialization inside the workflow. All non-determinism lives
    behind the activity boundary.

---

## 3. Architecture — three planes

| Plane | What it is | Where it runs |
|---|---|---|
| **Control** | The durable interpreter walking a frozen IR tree | Temporal workflow (deterministic sandbox) |
| **Brains + Hands** | Model calls and tool calls — all IO and non-determinism | Temporal activities (outside the sandbox) |
| **Projection** | A derived pomset view (causal events, cost, scheduling decisions) | In-workflow logical clock for live query; durable sink fed out-of-band from history |

The interpreter is **host-agnostic**: the same `interpret()` runs under
`InMemoryEnv` (tests, plain asyncio) and under the Temporal `Env`. Concurrency
and effects are injected through the `Env` seam. This separation is load-bearing
and MUST be preserved — it is what makes control flow unit-testable without a
server.

---

## 4. The IR

A flow is an immutable tree of `Node`s. Each node carries an id, a `step`, an
optional annotation (`Ann`: cost, timeout, cache hints), and children.

### 4.1 Shape lattice

Shapes form a total order. A node's shape is the join of its own floor and its
children's shapes.

```
Pipeline  <  Dataflow  <  Branching  <  Feedback  <  Staged  <  Agent
```

| Op | Role | Shape floor |
|---|---|---|
| `call` / `think` / `gate` | Leaf effect | Pipeline |
| `seq` | Sequential composition | join of children |
| `par` | Concurrent fan-out / fan-in | Dataflow |
| `alt` / `branch` | Data-dependent choice | Branching |
| `iter` / `loop` | Bounded feedback | Feedback |
| `stage` | Runtime-compiled plan | Staged |
| `app` / `agent` | Controller loop | Agent |
| `sub` | Nested flow | Pipeline at the surface (see firewall) |

### 4.2 Surface vs closed shape

- **Surface shape** is what the *parent* sees. A `sub` is opaque: surface
  Pipeline regardless of the child's internals.
- **Closed shape** is the node's true internal complexity, used for cost and
  admission inside its own scope.

The gap between the two is the **Sub firewall** (Invariant 5): a sub's value
crosses the boundary; its shape does not.

### 4.3 Contracts

A tool contract is `(effect, idempotency)`:

- `effect ∈ {read, write, dangerous}`
- `idempotency ∈ {none, native, required}`

`required` means *the caller guarantees an idempotency key is honored*. An
implementation that cannot supply that key for a given transport MUST NOT treat
the tool as `required` (see [§8.5](#85-idempotency-keys)).

---

## 5. Compile pipeline

Deploy runs a fixed pipeline. Each stage is a gate; a blocking diagnostic stops
the deploy.

1. **freeze** — bind every `ToolRef` to a content-hashed `FrozenTool`; produce a
   clean tree (cycles rejected, sharing unshared, ids normalized) plus a
   hash-keyed manifest.
2. **validate** — structural + schema checks: every post-freeze `call` resolves
   to a manifest entry; adjacent schemas are compatible; shapes are decidable.
3. **capability** — `enforce_compile`: deny-by-default checks for tools, brains,
   memory scopes, MCP servers, and (new) approval requirements.
4. **race-admission** — every branch in a `race`/`hedge`/`quorum` MUST be
   race-safe: read-only, or asserted native/required idempotent. Untrusted MCP
   hints do not count; the tool MUST be asserted in the capability manifest.
   Sub-agents inside a race branch are rejected (`RACE_SUB`).

The output is a **Deployment**: a frozen flow + manifest + capability manifest +
execution policy + an artifact hash ([§6.2](#62-artifact-hash)).

---

## 6. Freeze & replay integrity

### 6.1 Tool hashing — two concepts

A single `tool_hash` that omits behaviorally significant fields lets two
different tools collide. Split it:

- **Definition hash** — what the provider says: `ref`, `input_schema`,
  `output_schema`, `server_version`, MCP annotations snapshot.
- **Execution hash** — what this deployment uses: `definition_hash` +
  `contract` + `asserted` flag + native endpoint identity + retry policy class.

Every `call` binds to the **execution hash**. (Minimum acceptable interim fix:
fold `output_schema`, `contract`, and `asserted` into the existing hash.)

### 6.2 Artifact hash

The Deployment MUST expose a single `artifact_hash` over: frozen `flow_json`,
frozen `manifest_json`, the source hashes of every referenced pure, referenced
brain definitions, the execution policy, the capability manifest, and the
framework version. This is the clean identity of *the intended program* — the
answer to "what exactly did we run?"

### 6.3 Canonical JSON is strict

Canonical serialization MUST be `sort_keys=True`, compact separators, and **MUST
NOT** silently coerce non-JSON values (no `default=str`). Non-serializable
payloads MUST raise. Silent coercion produces unstable or colliding hashes and
is incompatible with Invariant 1.

### 6.4 Pure-function drift

At deploy, collect the source hash of every pure referenced by the flow and pin
it in the artifact. At worker startup (or workflow start) the registered pure
hashes MUST be compared against the artifact; a mismatch MUST fail before any
execution. Pures SHOULD be versioned semantically (`route.is_urgent.v1`) and
MUST NOT be mutated in place — add `.v2`.

---

## 7. Capabilities (deny-by-default)

The capability manifest declares what a flow is *allowed* to touch.

### 7.1 Absent vs empty

This distinction is normative and applies uniformly to every grant section:

- **Absent section** → unconstrained (no check).
- **Present-but-empty** → deny all.

`None` means unconstrained; `[]` means deny-all. This MUST hold in the static
`enforce_compile` path **and** in the agent loop. An empty grant list MUST NOT
grant ambient access.

### 7.2 Grant sections

| Section | Gates | Notes |
|---|---|---|
| `tools` | tool refs (by key) | each grant MAY assert `effect`/`idempotency` (makes it race-eligible) and `maxCalls` |
| `brains` | named brain configs | rename from `models`; gates the brain name |
| `models` | model IDs | optional; resolve `Brain.model` and check the actual model id |
| `memory` | context scopes | |
| `mcp_servers` | server → optional version pin | version pin MUST be enforced against the frozen tool's `server_version` |
| `network` | egress domains | enforced for native hands at call time |
| `subflows` | invokable sub-flow refs | distinct from tool grants; a sub may encapsulate powerful effects |
| `budget` | usd / tokens / wall-seconds | inherited by agents unless overridden |
| `approval` | tools requiring a human gate | see §7.3 |

### 7.3 Approval gating (new — required)

A tool whose effect is `dangerous` or whose grant carries `approval: required`
MUST NOT execute without a human gate. This MUST be enforced:

- at **deploy**: a flow that references such a tool outside a `human_gate` is a
  blocking diagnostic;
- at **run time**: both the flow interpreter and the agent loop MUST refuse to
  invoke an approval-required tool that is not behind an open, satisfied gate.

### 7.4 max_calls

A `maxCalls` grant MUST be enforced with a deterministic counter in workflow
state keyed by tool ref/hash — in the interpreter and Temporal `Env`, not only
in the agent loop. A grant that is parsed but unenforced is misleading and
non-conformant.

---

## 8. Execution semantics

### 8.1 seq / par

`seq` runs children in order, threading the value. `par` fans out concurrently
and joins.

### 8.2 WHOLE_SESSION degradation

If any `par` branch reads `WHOLE_SESSION` context, the runtime MUST degrade that
`par` to sequential evaluation (left then right), preserving output shape, and
MUST annotate the projection with the degraded-scheduling decision. The
validator's warning and the runtime behavior MUST agree — implement the
degradation or remove the warning.

### 8.3 race / hedge / quorum

Settlement is on **success**, not completion (Invariant 4):

- **race** — return the first *successful* branch result; ignore failures until
  *all* branches fail (then surface the aggregate failure).
- **hedge** — same settlement as race, but branches start **lazily**: branch 0
  starts immediately; each subsequent branch is constructed and started only
  after `hedge_ms` elapses without enough successes. Branches MUST NOT be
  eagerly started up front.
- **quorum** — return the first *K successful* results; fail only when fewer than
  K successes remain possible.
- **Determinism:** branch order is the tie-breaker among successes available at
  the same logical instant.
- **Cancellation:** losers MUST be cancelled once settlement is reached.

To support lazy hedge, the `Env` concurrency API MUST take branch **thunks**
(`Callable[[], Awaitable]`), not pre-started coroutines. This applies to both
`InMemoryEnv` and the Temporal `Env`. Tests MUST cover *fast-failure +
slow-success* and *cancellation of losers*.

### 8.4 Retry shaping

Retry policy is derived **per tool contract**: liberal attempts for reads /
native-idempotent tools; cautious attempts for writes. This MUST apply uniformly
to flow calls **and** agent calls — the agent path resolves the same contract
surface and uses the same policy. Unbound/unknown calls default to the
conservative `write/none` contract.

### 8.5 Idempotency keys

A retryable call to a `native`/`required` idempotent tool MUST carry a
deterministic idempotency key (the activation id). This MUST be threaded on
**every** transport that claims idempotency, including MCP. If a transport
cannot carry the key, its tools MUST NOT be admitted as `required`.

### 8.6 Human gate

A human gate is a durable wait (signal + condition) with an optional timeout.

- On signal, the gate releases with the human's decision.
- On **timeout**, the gate MUST return the decision *and the original input*:
  `{"approved": false, "reason": "timeout", "input": <value>}` — the input is
  what a reviewer needs later.
- The workflow MUST expose the set of currently open gates by activation id for
  a review UI.

### 8.7 Non-retryable policy errors

Settled policy decisions (`CapabilityDenied`, `PlanRejected`, `ValidationError`,
`FreezeError`) MUST be raised as explicitly non-retryable application errors —
not matched by class-name string — so the contract survives refactors.

---

## 9. Staged plans

A `stage` compiles a model-generated plan at run time, inside an activity (so a
rejected plan fails cleanly without corrupting the deterministic workflow).

`compilePlan` MUST:

1. parse model output into IR;
2. normalize ids under a staging prefix;
3. **bind every `call` to the parent frozen manifest** (`bind_plan_to_manifest`):
   resolve each `ToolRef` against the parent manifest and set `frozen_hash`.
   Zero matches → reject. Multiple matches for one logical ref → reject unless
   the plan pins a hash;
4. validate against the manifest;
5. run plan validation (budget estimate, shape);
6. run race admission if the plan contains `race`/`hedge`/`quorum`;
7. return the bound plan JSON.

The effect of binding (Invariant 3): a staged call inherits the **real**
contract of its frozen tool — correct retry shaping, schema checking, and proof
the model did not invent a tool — instead of falling back to a conservative
default.

---

## 10. Agent loop

The controller runs in its own workflow so `continue_as_new` truncates only the
agent's history.

- **Closed vocabulary:** `FINISH`, `ESCALATE`, `CALL` (one granted tool), `SUB`
  (one granted sub-flow). Nothing else.
- **Budget ordering (Invariant 9):** before invoking the controller, check
  whether a controller call would exceed budget; if so, terminate `over_budget`
  without spending. Charge after the call. Apply the same pre-check to each
  action.
- **Grant enforcement:** a `CALL` is allowed only if the tool is granted
  (`None` = unconstrained, `[]` = deny-all); a `SUB` only if the sub-flow is
  granted. Approval-required tools require an open gate.
- **Contract resolution:** the agent spec MUST carry tool **contracts**, not
  just names, so retry shaping and effect/approval checks match the flow path.
- **Controller contract:** strict by default — a malformed controller reply is
  `controller_error`, not an implicit FINISH. A permissive mode MAY exist for
  demos but MUST be opt-in.
- **Continue-as-new:** carry config, granted tools (with contracts), and state
  across segments to bound history.

### 10.1 Trace richness

Trace entries MUST be rich enough to support honest plan extraction:
`decision`, `ref`, content-addressed `input_ref` / `output_ref`, `schema_ref`,
`shape`, `cost`. Until extraction infers patterns/branches/loops/reducers from
these, it is **macro-recording**, not procedure discovery — name it honestly.

---

## 11. Projection

The projection is a derived pomset, not a durable record (Invariant 6).

- **Cost:** events MUST charge cost — `Ann.cost` when present, a default leaf
  estimate otherwise, and actual model token/cost metadata from `invokeBrain`.
  `costByShape` MUST be populated in real runs, not just in tests.
- **Scheduling decisions:** `par`, `race`, `hedge`, `quorum`, context
  degradation, and cancellation MUST emit explicit attrs
  (`{"merge": "race", "winner": ..., "cancelled": [...]}`). This is the
  difference between "a trace exists" and "debugging is pleasant".
- **Bounded memory:** the in-workflow projection store MUST be bounded (cap or
  ring-buffer); it exists only for causal-id threading and the live query.
- **Durable sink:** the Postgres/OTel sink is fed out-of-band from history. Its
  status (interface-only vs production) MUST be stated honestly ([§12](#12-conformance)).

---

## 12. Conformance

The spec above is the **target**. This section tracks where the current
implementation diverges, as a punch list. An item is *conformant* only when its
invariant holds in code with a test.

### 12.1 Implemented

IR · shape lattice · freeze · validation · capability basics · race admission
(static) · pure interpreter · Temporal harness · human gate · agent loop ·
local projection.

### 12.2 Seam / experimental

Production projection sink · full replay-artifact verification · plan-extraction
quality · per-run freeze · cost accounting · OTel export completeness.

### 12.3 Known gaps (fix in priority order)

**P0 — execution semantics & effect authorization**

- [ ] **Race settles on first completion, not first success** (`finished()`
      re-raises on a failed branch). Both `Env`s. → §8.3
- [ ] **Hedge starts all branches eagerly** (the lazy "reveal" is cosmetic). →
      §8.3 (requires the thunk-based `Env` API)
- [ ] **Approval gating is not modeled or enforced.** → §7.3
- [ ] **Empty grant list = allow-all in the agent loop.** → §7.1
- [ ] **Agent tool calls ignore the tool contract for retry/effect.** → §8.4,
      §10
- [ ] **MCP calls carry no idempotency key.** → §8.5

**P1 — replay integrity & capability consistency**

- [ ] **`canonical_json(default=str)` silently coerces.** → §6.3
- [ ] **Pure-function drift is computed but never verified.** → §6.4
- [ ] **Tool hash omits output_schema / contract / asserted.** *(verify the
      `FrozenTool.hash` body before treating as fact.)* → §6.1
- [ ] **No artifact hash.** → §6.2
- [ ] **`models` gates brain names, not model ids.** → §7.2
- [ ] **`maxCalls` parsed, never enforced.** → §7.4
- [ ] **MCP server version pins not enforced.** → §7.2
- [ ] **No subflow grant boundary.** → §7.2
- [ ] **Agent budget checked after the controller already spent.** → §10
- [ ] **WHOLE_SESSION `par` degradation warned but not implemented.** → §8.2
- [ ] **Human-gate timeout drops the input.** → §8.6
- [ ] **Projection cost not charged (`costByShape` empty in real runs).** → §11

**P2 — ergonomics & guardrails**

- [ ] **Staged plans not bound to the parent manifest** (fall back to
      conservative default; no invented-tool check). → §9
- [ ] Explicit `Registry` instead of process-global registries.
- [ ] Non-retryable policy errors raised as explicit application errors. → §8.7
- [ ] `Ann.timeout` honored only for human gates; `Ann.cache` inert — wire or
      remove. → §4, §8.4
- [ ] `py.typed` marker, mypy (strict on core), ruff, CI matrix with/without the
      `temporal` extra.
- [ ] CLI (`freeze` / `validate` / `inspect` / `run-local` / `graph`) and a
      user-facing `explain(diagnostics)`.

---

## 13. Golden corpus (cross-language contract)

Because Python is canonical and other frontends are deferred, the wire format is
preserved by a language-neutral golden corpus — the conformance suite any future
frontend MUST pass. It pins, for each fixture: the input flow, the frozen IR
JSON, the manifest with tool hashes, the validate diagnostics, and the
surface/closed shapes. Required fixtures:

simple pipeline · subagent firewall · race · quorum · hedge · human gate ·
staged plan · agent app · frozen manifest · capability manifest.

The golden hashes MUST be asserted as known values (not merely "deterministic"),
so a refactor that changes the IR or the hashing is caught immediately.

---

*This spec is the contract. When code and spec disagree, fix one of them on
purpose — never let them drift silently.*
