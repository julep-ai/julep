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
| `budget` | cost / tokens / wall-seconds | inherited by agents unless overridden |
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

### 8.8 Reserved hand: `__sleep__`

A `call` to the reserved native hand `__sleep__` is a durable timer, not an
HTTP call. The duration in seconds rides on the node's `ann.timeout`. Freeze
resolves it synthetically (no snapshot entry) with an asserted
read/naturally-idempotent contract, so it is race-safe. Capability semantics
match `__human_gate__`: under a `tools:` allow-list it must be granted
explicitly.

### 8.9 Continuation (chaining) convention

A flow whose final value is `{"__continue__": <next input>}` requests
re-dispatch with that input as a fresh segment. Backends MUST run the next
segment under the same frozen flow + manifest and SHOULD carry cumulative
`maxCalls` counts across segments. Backends MAY enrich the sentinel object with
bookkeeping keys; consumers MUST read the next input only from `__continue__`.

### 8.10 The dispatch boundary

Triggering (schedules, debounce, dedup ids, webhooks, queue routing) is not
representable in the IR by design. See docs/dispatch-boundary.md.

### 8.11 Run principal

A run MAY carry a **principal**: an opaque, JSON-serializable object
(`RunPrincipal`) naming the tenant and a credential *reference* on whose behalf
the run executes.

- **Input, not artifact.** The principal is workflow input (`principal` on
  `FlowInput`/`AgentInput` and the DBOS payloads), so it is replay-stable and
  identical across activity retries. It MUST NOT enter the frozen artifact:
  freeze hashes and the golden corpus do not move when a principal is supplied.
- **Opaque.** The framework MUST NOT interpret the principal. It is threaded
  into every effect payload (`callHand`, `invokeBrain`, `compilePlan`) and
  handed to the worker's callers as one extra argument
  (`McpCaller`/`LlmCaller`); native hands MAY resolve it into transport headers
  via a worker-supplied `principal_headers`.
- **Never a secret.** The principal names a credential reference (e.g.
  `{"storeId": 413, "tokenRef": "cred_abc"}`); the worker resolves the actual
  token from its own secret store at call time. Workflow history is a durable,
  replayable record — bearer tokens MUST NOT enter it.
- **Children inherit.** Sub-flows and sub-agents receive the parent's principal
  unchanged; there is deliberately no API to substitute a different principal
  on a `sub`. Every `continue_as_new` segment MUST carry the principal forward.
- **Failure semantics.** A worker that requires a principal and receives `None`
  MUST fail fast with `PrincipalRequired`, a non-retryable policy error
  (joins `CapabilityDenied` et al., §8.7).
- **Back-compat.** `configure` MUST wrap legacy callers (without the trailing
  `principal`) once at configure time so they keep working unchanged.

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

> **Status: conformant.** Every P0/P1/P2 item below holds in code with a test,
> the §13 golden corpus is pinned, and the El Niño worked example
> (`examples/elnino/`) deploys clean and dry-runs end-to-end. The suite passes
> with and without the Temporal extra; `mypy --strict` is clean and `ruff` is
> clean.

### 12.1 Implemented

IR · shape lattice (incl. n-ary `alt` switch) · freeze (definition+execution
hash) · validation · capabilities (deny-by-default, approval gating, model-id /
`maxCalls` / version-pin / subflow / app-grant attenuation) · race admission ·
pure interpreter · Temporal harness · human gate · agent loop (strict
controller, budget pre-check, contract retry) · projection (cost + scheduling
attrs) · staged-plan manifest binding · artifact hash · pure-drift verification ·
explicit Registry · CLI + `explain` · golden corpus · py.typed + mypy-strict + CI.

### 12.2 Seam / experimental

Production projection durable sink (Postgres/OTel are interface + data; fed
out-of-band from history) · plan-extraction quality (honest *macro-recording*,
not yet procedure discovery, §10.1) · per-run freeze · `Ann.cache` (forwarded to
the hand as advisory; no framework cache backend).

### 12.3 Closed gaps (all conformant — invariant holds in code with a test)

**P0 — execution semantics & effect authorization**

- [x] **Race/quorum/hedge settle on first SUCCESS** (thunk `Env`; failures
      ignored until impossible; losers cancelled). → §8.3 · `7c210c7`
- [x] **Hedge is lazy** (branch *i* starts only after `hedge_ms`). → §8.3 · `7c210c7`
- [x] **Approval gating** modeled + enforced (deploy dominance check + runtime
      refusal; `app`-grant attenuation). → §7.3 · `7bc0e93`, `fca8499`, `e33d4af`
- [x] **Deny-by-default** (`None`=unconstrained vs `[]`=deny) at compile + loop. → §7.1 · `7bc0e93`, `fca8499`
- [x] **Agent CALLs use the tool contract** for retry/effect. → §8.4, §10 · `fca8499`
- [x] **MCP calls carry a deterministic idempotency key.** → §8.5 · `2f8e7a8`

**P1 — replay integrity & capability consistency**

- [x] **Strict `canonical_json`** (no `default=str`; raises on non-JSON). → §6.3 · `e766411`
- [x] **Pure-function drift verified** at workflow start (non-retryable). → §6.4 · `01dd702`
- [x] **Definition + execution hash** (folds output_schema/contract/asserted). → §6.1 · `e766411`
- [x] **`artifact_hash`** over flow+manifest+pures+brains+caps+version. → §6.2 · `e766411`
- [x] **`models` gates model ids**; `brains` gates brain names. → §7.2 · `1eae744`
- [x] **`maxCalls` enforced** (deterministic counter; inherited across SUB). → §7.4 · `1eae744`, `e33d4af`
- [x] **MCP server version pins enforced.** → §7.2 · `1eae744`
- [x] **Subflow grant boundary** (compile + agent SUB). → §7.2 · `7bc0e93`, `1eae744`
- [x] **Agent budget pre-checked** before the controller spends. → §10 · `fca8499`
- [x] **WHOLE_SESSION `par` degraded** to sequential + annotated. → §8.2 · `753f667`
- [x] **Human-gate timeout returns the input.** → §8.6 · `753f667`
- [x] **Projection charges cost** (`costByShape` populated; scheduling attrs). → §11 · `753f667`

**P2 — ergonomics & guardrails**

- [x] **Staged plans bound to the parent manifest** (invented-tool rejection). → §9 · `276fe9d`
- [x] Explicit `Registry` (back-compat shims). · `83dc37a`
- [x] Non-retryable policy errors raised as typed application errors. → §8.7 · `ef6f3cc`
- [x] `Ann.timeout` honored per node; `Ann.cache` forwarded as advisory. → §4, §8.4 · `e546007`
- [x] `py.typed`, mypy (strict on core, 0 errors), ruff, CI matrix with/without
      the `temporal` extra. · `74d9055`, `3ae8a99`, `a84600d`
- [x] CLI (`freeze`/`validate`/`inspect`/`run-local`/`graph`) + `explain(diagnostics)`. · `ef6f3cc`

### 12.4 Beyond the punch-list

- Public API renamed to the algebra-faithful surface (`seq`/`par`/`alt`/
  `iter_up_to`/`sub`/`app`/`mcp`/`native`); clean typed re-exports. · `af472e2`, `3ae8a99`
- n-ary `alt(select, cases)` multiway switch added to the IR. · `88b9c77`
- Final adversarial review (two independent passes) closed 10 cross-batch issues
  incl. an `app`-inline-grant capability bypass. · `e33d4af`, `a84600d`

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

## 14. dotctx rich layout

One loader, one format. `load_dotctx(path)` reads the minimal layout
(settings-only, inline/`system_file` prompt, optional `schema_file`) unchanged.
A package carrying any of `prompt.j2`, `messages/`, `schema.pyi`, `tools.pyi`
is **rich** and is loaded by `composable_agents.dotctx_rich`, which requires
the `composable-agents[dotctx]` extra (jinja2). Importing the rich loader
without jinja2 MUST raise — a package with a template and a loader that cannot
render it never degrades to a plain-string prompt.

```
<name>.ctx/
├── settings.yaml      # name, model, temperature, max_rounds, max_tokens, agent, sub, context, tools
├── schema.pyi         # `Output` stub -> JSON Schema -> Brain.reply_schema
├── tools.pyi          # tool stubs (+ module-level __server__) -> grants + expected schemas
├── prompt.j2          # single system template, OR
└── messages/          # 00_system.yml + 01_user.yml (role + Jinja2 content)
eval.py / eval.yaml    # consumer-side; ignored, never an error
```

### 14.1 Templates become registered renderers

A template never lives on the `Brain` and never enters the artifact. Loading
compiles each template and registers one renderer per template, named
`dotctx/<package>/<role>@v<sha256(content)[:12]>` and source-hashed by template
content, so §6.4 drift detection covers prompt edits. The Brain carries only
the renderer names (`system_render`, and `user_render` for bundles);
`Brain.system` stays `""`. Rendering is strict (`StrictUndefined`, no
filesystem loader at render time): renderers read only the projected `Context`,
and a template referencing a variable the Context does not carry fails at first
render with the package name and variable. Bundles are one system message plus
at most one user message; anything else is rejected at load with the file name.
The rendered user string is the user turn in `complete_brain`; without
`user_render` the value-as-JSON behavior is unchanged.

### 14.2 Settings

Settings keys are an allow-list; unknown keys are a load-time error listing the
offending keys. `max_tokens` rides on the `Brain` and is forwarded to the
provider call. Model strings keep `@low/@medium/@high/@none` reasoning-effort
suffixes untouched (an LlmCaller convention, not a framework concern).
`user_render` / `max_tokens` enter the brain identity (`userRender` /
`maxTokens`) only when set, so existing artifacts hash byte-identically.

### 14.3 tools.pyi asserts, never creates

`.pyi` compilation is dependency-free (stdlib `ast` -> JSON Schema: scalars,
lists/dicts/sets/tuples, `Optional`/unions, `Literal`, TypedDict with
`Required`/`NotRequired`, nested classes, docstrings as descriptions, constant
defaults — no pydantic). Stubs set `Brain.tools` to toolref keys
(`server/tool` when `__server__` names the MCP server), emit a `ToolGrant`
manifest fragment the caller merges into the deployment's capability manifest,
and record each tool's expected input schema. At freeze, when the snapshot
resolves an expected tool (call leaf, app inline grant, or a referenced brain's
granted tool), the served schema is compared by canonical hash; a mismatch
raises the blocking **`TOOL_SCHEMA_DRIFT`** diagnostic naming the `.ctx` path
and server.

---

*This spec is the contract. When code and spec disagree, fix one of them on
purpose — never let them drift silently.*
