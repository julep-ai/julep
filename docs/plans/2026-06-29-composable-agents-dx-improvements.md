# Composable-Agents DX Improvements — Design

**Date:** 2026-06-29
**Status:** Draft for review (pre-implementation)
**Author:** Diwank + Claude (from a clean-room DX experiment)

## 1. Context & method

We ran a clean-room developer-experience experiment to find where
`composable-agents` actually hurts a first-time user. The instrument was an
external coding agent (codex `gpt-5.4-mini@high`) acting as a developer who had
**never seen the framework**, given **only**:

- the 51 published user-doc pages (`docs-site/content/docs`), and
- a fresh venv with `composable-agents` installed from the **local 1.0.0rc1
  wheel** (so docs and package matched exactly; no repo source, tests, internal
  design docs, or internet; no API keys — forcing the documented keyless/fake
  path).

Task: build a small-medium **batch "returns triage"** pipeline (fan-out over
requests, per-request routing, a faked reasoner email draft, run via
`deploy`+`dry_run`) — deliberately aimed at the novel/frictional surfaces
(`each`, branching, source-hash pures, fake reasoners). The agent journaled a
structured DX review as it worked; every headline finding below was then
**independently reproduced and root-caused against the installed package
source**.

Verdict from the run: **5/10 overall** — "promising authoring model, but I would
not depend on the current CLI/tooling story without fixes." Time-to-first-success
was ~22 min (a working `python returns_triage.py`); the `ca` CLI stretch goal
**never worked**.

The artifacts (the agent's `DX_REVIEW.md`, its `returns_triage.py`, and the
reproduction notes) live under the experiment lab; key evidence is inlined below.

## 2. Goals / non-goals

**Goals (this design):**

1. Make the `ca` CLI's inner loop (`ca run`, `ca lint`) actually work for the
   documented authoring style — the **Critical** finding.
2. Stop the docs from claiming outputs that the shipped package does not produce
   — make the docs **executable in CI** against the built wheel.
3. Make define-time **error messages teach** the framework's rules at the two
   specific places newcomers fall through to raw Python errors.
4. Smooth the **on-ramp**: a progressive tutorial and lower-friction branching,
   because the experiment showed the branch combinators are being avoided.
5. Land the cheap **trust fixes** (version string, broken link, install command,
   stale shape claim) alongside (2).
6. Make registration **consistent and declarative** — object-first reasoners,
   with no imperative `register_*` call in the common authoring path.

**Project stage:** early. **Hard cut-overs are acceptable and preferred** — no
backward-compat shims, no deprecation cycles. When an API changes, change it and
its callers/docs outright.

**Non-goals:**

- Redesigning the core model (define-by-construction, the IR, the shape lattice).
  The experiment confirmed the *core is liked*; the pain is the on-ramp and
  tooling.
- Temporal/DBOS/CMA/sessions DX (not exercised in this experiment).
- Performance work.

## 3. Evidence summary (what we verified)

| # | Severity | Finding | Status |
|---|---|---|---|
| 1 | 🔴 Critical | `ca run`/`ca lint` fail with `UNKNOWN_PURE` for **any** flow using a `@pure`, including the verbatim canonical quickstart, while `python script.py` works. | Reproduced + root-caused |
| 2 | 🟠 High | Canonical quickstart claims `SHAPE: Pipeline`; package prints `Dataflow`. | Reproduced |
| 3 | 🟢 Already fixed on main | `__version__` reported `0.1.0` against the **stale 24-Jun wheel** (hardcoded). Current `main` derives it from `importlib.metadata` and reports `1.0.0rc1`. Real gaps: the `dist/` wheel is stale, and there's no regression test pinning `__version__` to the dist metadata. | Verified vs main source |
| 4 | 🟠 High | Define-time errors fall through to unhelpful raw Python at two key spots (pure arity; method-style `flow.each(...)`). | Reproduced |
| 5 | 🟡 Medium | Branch combinators (`cond`/`switch`) avoided entirely — the agent did its routing with a ternary inside a `@pure`. | Observed in code |
| 6 | 🟡 Medium | `gotchas.md` tells pip users to `pip install -e '.[cli]'` (needs a source checkout). | Reproduced |
| 7 | 🟡 Low | `concepts/model.md:188` has a malformed/broken doc link. | Reproduced |
| 8 | 🟠 High | Imperative `register_reasoner(Reasoner(...))` + string refs clash with the declarative `@tool`/`@pure` idiom; `Reasoner` also duplicates `reply`/`reply_schema`. | Observed in docs + signature |

## 4. Workstream 1 — CLI pure-registry fix (Critical)

### 4.1 Problem

```
$ ca lint triage   → ERROR triage: UNKNOWN_PURE — arr function not registered: 'ticket_prompt'
$ ca run  triage   → error: "unknown pure 'ticket_prompt'; register it with @pure('ticket_prompt') on a worker"
$ python triage.py → works
```

Nearly every real flow uses at least one `@pure`. As shipped, the flagship
"dbt for agents" inner loop is dead-on-arrival from a pip install.

### 4.2 Root cause (confirmed in source)

The `ca` resolve boundary runs in two processes:

- **Child** (`composable_agents/ca/_resolve_child.py`): imports the user module
  — which runs every `@pure` decorator and registers it **in the child's**
  registry — then for the `resolve` action emits **only the IR**:
  `_emit({"ir": node.to_json(), "name": target})` (line 206). The pure registry
  is discarded.
- **Parent**: `resolve_agent` (`ca/resolve.py:57`) returns `ResolvedAgent{name,
  ir}`. `ca lint` then runs `validate(Node.from_json(resolved.ir))`
  (`ca/lint.py:41`) and `ca run` runs `interpret(node, …)` (`ca/runner.py:72`),
  both **in the parent**, where no `@pure` decorator ever executed. `validate`
  resolves `arr`/pure names against the global registry (`validate.py:219`) and
  the interpreter resolves pures at runtime — both find an empty registry.

The `freeze`/`freeze_check` action does **not** hit this because it calls
`deploy()` *inside the child* (`_resolve_child.py:_freeze_agent`). So `ca deploy`
works while `ca lint`/`ca run` do not — exactly the split the experiment saw.

### 4.3 Approaches

**Approach A — ship pure sources across the boundary, re-register parent-side
(recommended; minimal blast radius).**

- Child: in the `resolve` action, for every pure name referenced by the node
  (`alt` selector/predicate, `each` reducer, `arr` functions), collect its
  registered raw source (the registry already holds it for source-hash pinning)
  and emit `{"ir": …, "name": …, "pures": {name: source}}`.
- Parent: extend `ResolvedAgent` with `pures: dict[str, str]`. In `lint.py` and
  `runner.py`, re-register each shipped pure source into the parent registry
  before `validate`/`interpret`.
- Why it fits: re-registration *by raw source* is precisely the determinism
  contract the framework is already built on (pure pins are source hashes); pure
  source is already shipped to CAS on `deploy`, so there is no new trust surface.
- Blast radius: widen one payload + add re-register calls at two sites. No
  relocation of the runner/projection logic.
- Risk: the parent's global registry accumulates pures across a multi-agent
  invocation; same-name/different-source collisions are already a global-registry
  property and validate is per-agent. Acceptable; add a guard that errors on a
  genuine source-hash collision.

**Approach B — run `validate`/`interpret` in the child (CHOSEN).**

Everything that needs the pure registry runs in the one process where the
registry is live (the child that imported the user module), mirroring how the
`freeze` action already calls `deploy()` in-child. This guarantees
`ca run` ≡ `dry_run` parity by construction and removes the entire class of
"parent has an empty registry" bugs rather than patching the two current call
sites.

Concrete design:

- **`_resolve_child.py`** gains two new actions alongside `resolve`/`freeze`:
  - `lint`: discover the agent → `validate(node)` *in-child* → emit
    `{"diagnostics": [<serialized Diagnostic>...]}`.
  - `run`: discover → build the echo env in-child → `interpret(node, value, env)`
    → emit `{"value": <json>, "events": [<ProjectionEvent json>...], "error":
    <str|null>}`. Relocate the echo-stub + projection-ownership helpers
    (`_echo_tools`/`_echo_reasoners`/`_echo_subs`/`_echo_agents`,
    `_clear_frozen_hashes`, the `InMemoryProjection` ownership) from `runner.py`
    into the child. The run `value` and events are already JSON-serializable
    (they round-trip through the `.julep/runs/` trace cache today).
- **`resolve.py`** grows a small dispatch so each verb invokes the child with its
  action and parses the matching payload (extend `ResolvedAgent` or add sibling
  result dataclasses: `LintResult{diagnostics, error}`,
  `RunResult{value, events, error}`). The existing `resolve` (IR-only) action
  stays for any caller that only needs IR.
- **`lint.py`** consumes child diagnostics instead of calling `validate` itself;
  **`runner.py`** becomes a thin parent-side wrapper that asks the child to run
  and renders the returned events as the trace tree.
- The input `value` for `run` crosses parent→child as JSON in the action payload
  (same channel the args already use).

Trade-off accepted: more child surface and a value/event JSON round-trip, in
exchange for structural correctness and `ca run` ≡ `dry_run` parity. Approach A
(ship pure sources, re-register parent-side) is recorded as the considered
minimal alternative but not chosen.

### 4.4 Regression test (the linchpin)

The real defect is *we never ran our own published happy path from a clean
install*. Add a test that:

- builds/installs the wheel (or installs the package) into an isolated env,
- writes the **verbatim quickstart** flow,
- asserts `ca lint <flow>` exits 0 with no `UNKNOWN_PURE`, and
- asserts `ca run <flow> --input …` produces the expected value with no
  "unknown pure" error.

This belongs in the same suite as Workstream 2 so the CLI happy path is covered
forever.

### 4.5 Acceptance

`ca lint`/`ca run` on the canonical quickstart and on a multi-pure + `each` flow
(the experiment's `returns_triage.py`) both succeed; the new regression test
fails on today's code and passes after the fix.

## 5. Workstream 2 — Executable docs in CI (High)

### 5.1 Problem

The first thing a user runs disagrees with the docs:

- `first-flow.md` / `authoring-flows.md` print `SHAPE: Pipeline`; the package
  prints `Dataflow`.
- Multiple fenced examples assert exact stdout that nothing verifies.

### 5.2 Approach

A doc-test harness (greenfield — no such infra exists today) that:

1. Walks `docs-site/content/docs/**/*.{md,mdx}`, extracts fenced ```python```
   blocks (and adjacent ```text``` "expected output" blocks where present).
2. Executes each runnable block against the **built wheel** in a clean
   subprocess (keyless; no network), honoring per-block directives in an
   HTML-comment pragma for blocks that are illustrative-only or expected to raise
   (e.g. `<!-- julep:doctest skip -->`, `<!-- julep:doctest raises=DefineError -->`,
   `<!-- julep:doctest expect-output -->`).
3. For blocks tagged `expect-output`, compares stdout to the following ```text```
   block and fails on mismatch.
4. Runs in CI on every change to docs or the package.

Scope for v1: the `start/` and `reference/cheatsheet.md` examples (the
getting-started surface a new user hits first), then expand to `guides/`.

### 5.3 Quick-win fixes (land with this workstream)

- Fix `__version__` to report the installed distribution version (the
  `importlib.metadata` derivation already exists per the version-derivation work;
  confirm why the wheel reports `0.1.0` and correct it).
- Correct the stale shape claim (regenerate the example's expected output once
  the harness exists, so it can never re-drift).
- `gotchas.md`: give the pip-user install (`pip install 'composable-agents[cli]'`)
  alongside the source-checkout one.
- Fix the malformed link at `concepts/model.md:188`.

### 5.4 Acceptance

CI executes the getting-started code blocks and the suite is red on today's
`Pipeline` claim, green after regeneration; `__version__` matches the wheel.

## 6. Workstream 3 — Teaching error messages (High)

### 6.1 Problem (exact text the agent hit)

- Passing multiple positional args to a pure:
  `TypeError: Pure.__call__() takes 2 positional arguments but 4 were given` —
  a raw Python error with no framework guidance.
- Method-style fan-out `flow.each(...)`:
  `DefineError: unregistered callable 'triage_return.each' … decorate it with
  @pure or @tool …` — *actively misleads* toward registration when the real
  issue is that `each` is a top-level helper, not a method.

The framework already sets a high bar elsewhere (define-time diagnostics with
`fix:` lines). These two cases just fall through.

### 6.2 Approach

In `composable_agents/define.py` (and `dsl.py` where the pure/handle call paths
live):

- **Pure arity:** wrap the pure-application path so that calling a registered
  pure with >1 positional handle raises a `DefineError` with
  `fix: a pure takes one input value; merge multiple handles with 'a | b' (or a
  pure that reshapes one record) before the call`.
- **Method-style combinators:** special-case attribute access for `each`, `par`,
  `seq`, `cond`, `switch`, `map_n`, … on `FlowDef`/`Handle` and raise a
  `DefineError` with `fix: 'each' is a top-level helper — call each(body, items),
  not flow.each(...)`. (Today these resolve to a generic "unregistered callable
  '<x>.each'".)

Both should carry source spans like the existing diagnostics.

### 6.3 Acceptance

The two reproductions emit a framework `DefineError` whose `fix:` line names the
correct rewrite; covered by unit tests asserting the message text.

## 7. Workstream 4 — On-ramp & branching ergonomics (Medium)

### 7.1 Problem

The agent's "what I wish I'd known first" list and its avoidance of `cond`/
`switch` (it routed via a ternary inside a `@pure`) show the steepest part of the
curve is under-supported: define-time vs runtime, single-input pures, top-level
combinators, branch subject-label/keyword-capture rules, and the shape lattice
moving under your feet.

### 7.2 Approach

1. **A progressive "ladder" tutorial** that introduces one surface at a time as
   runnable diffs (tool → pure → reasoner → branch → fan-out → deploy/dry_run),
   each step a file that the Workstream-2 harness executes. End-state mirrors the
   experiment task so it doubles as a worked example.
2. **Branching ergonomics — ship `switch_on` (CHOSEN).** Add a
   `switch_on(subject, key=…, cases=…, default=…)` helper for the dominant
   "branch on a record field" case that auto-derives and registers the selector,
   so users don't hand-write+register a predicate for the common path. The
   derived selector must itself be a **registered, source-pinned pure** so the
   determinism contract is preserved (the helper generates a deterministic,
   content-stable selector keyed on `key=`; same `key` → same pin). Also land the
   docs win: a copy-pasteable `cond`/`switch`-with-captures example in the
   authoring guide that makes the subject-label rule obvious, and route the
   ladder's branching step through `switch_on`.

   Open design points for the implementation plan: how the auto-derived selector
   is named/pinned deterministically (so it doesn't collide across flows yet
   stays stable across runs), and whether `cases` keys are matched by equality on
   the plucked field value.

### 7.3 Acceptance

A new user can follow the ladder end-to-end with every step executing in CI; the
branching example (and/or sugar) lets a field-based route be written without the
capture-rule false starts the experiment hit.

## 8. Workstream 5 — Object-first reasoners & idiom hard cut-over (High)

### 8.1 Problem

The framework is declarative everywhere except reasoner registration, which is
the odd one out on every axis:

| Primitive | Declared via | Referenced in flow as | Passed to `deploy` as |
|---|---|---|---|
| Tool | `@tool` decorator | the object — `lookup(...)` | object — `tools=[lookup]` |
| Pure | `@pure` decorator (but `register_pure` also exists) | the object | (collected) |
| **Reasoner** | **`register_reasoner(Reasoner(...))`** (imperative) | a **string** — `think("name", …)` | a **string** — `reasoners=["name"]` |

The imperative `register_reasoner` (construct-then-mutate-a-global) and the
string references jar against `@tool`/`@pure`, are import-order-sensitive, and
are easy to forget. `Reasoner` also carries **both** `reply=` and `reply_schema=`.

**Constraint:** the frozen IR references reasoners *by name* (the `ThinkStep`
carries the name; the artifact freezes name→model/system/reply; the durable
worker resolves by name), and the string path enables dynamic/late-bound
selection (`reasoner_from_ctx`). So we keep the name registry — we just stop
forcing users to populate it imperatively.

### 8.1a Prior art / lineage

This is the **second half of an explicit terminology program**. The first half —
`Brain → Reasoner`, `Hand → Tool`, retire `Spine`
(`docs/superpowers/specs/2026-06-20-terminology-reasoner-tool-design.md`, branch
`terminology-reasoner-tool`) — has **already landed on `main`** (verified
2026-06-29: the code leftover-grep is clean; `Env.run_call` resolved the
`call_tool` pun exactly as that doc's §9 recommended). That pass fixed the
mixed-metaphor **noun** problem on the principle of *one name per concept*
(DDD Ubiquitous Language, Google AIP-140, "don't pun"): `Reasoner`/`Tool` are now
the literal, durable-register names. It deliberately **kept the verb `think()`**
and explicitly did **not** touch the *registration idiom*.

WS5 closes the gap that pass left open: the nouns are clean, but a reasoner is
still *registered imperatively* (`register_reasoner`) while tools/pures are
*declared*. Same philosophy — literal, consistent, one idiom per concept — now
applied to registration. The terminology branch is doc-only; its design is fully
implemented, so it can be merged-as-record or deleted (it is **not** a WS5
dependency).

### 8.2 Decisions (made)

- **Object-first reasoner surface (chosen).** Declare a `Reasoner(...)` object;
  reference it directly with `think(reasoner_obj, handle, …)`; collect it at
  `deploy(reasoners=[reasoner_obj])` and `Agent(reasoner=reasoner_obj, …)`.
- **Remove `register_reasoner`** from the public API outright.
- **Collapse `reply`/`reply_schema`** to a single public `reply=`; remove
  `reply_schema`.
- **Demote `register_pure`** to internal/advanced; `@pure` is the one public way
  to declare a pure.
- **Keep the string path** (`think("name", …)`, `reasoners=["name"]`,
  `reasoner_from_ctx(path)`) as a *supported, documented* surface for
  **dynamic / late-bound** selection — not legacy.
- **Migrate all docs and examples** to the object-first idiom.
- **No backward compat, no deprecation shims** (early project — hard cut-over).

### 8.3 Approach

- `Reasoner(...)` stays pure data carrying its `name`; construction does not
  mutate any global.
- `think(reasoner_obj, handle, …)` reads `reasoner_obj.name` and records a
  `ThinkStep` with that name — **identical wire format** to today.
  `think("name", …)` still works for dynamic refs.
- `deploy(flow, tools=[...], reasoners=[reasoner_obj | "name", ...])` registers
  each passed `Reasoner` object into the name registry as a *consequence of
  deploying* (mirroring `tools=[...]`); a bare string means "resolve this name
  from the registry/context" (the dynamic path).
- `Agent(reasoner=reasoner_obj | "name", …)` accepts an object or a name.
- Remove `register_reasoner` and `reply_schema` from
  `composable_agents/__init__.py` exports and the `Reasoner` API; stop exporting
  `register_pure` publicly (keep the internal entry the PEP 723 tooling uses).

**Reasoner API family — what goes vs stays** (full surface, from the terminology
doc + current `__init__.py`): **remove** the user-facing imperative
`register_reasoner`; `deploy(reasoners=[obj])` becomes the single registration
point. **Keep** the registry-query / dynamic-resolution family the string path
depends on — `get_reasoner`, `reasoner_from_ctx`, `reasoner_from_settings`,
`reasoner_to_flow`, `make_local_reasoner` — these are how `think("name", …)` /
`reasoners=["name"]` resolve for the dynamic case and are unchanged.

**Wire-format invariants (object-first is authoring-only — the golden corpus must
NOT move).** The change lowers to byte-identical IR/manifest:

- `ThinkStep.reasoner` (the frozen name) is unchanged: `think(obj, …)` lowers to
  the same `ThinkStep(reasoner=obj.name)` as `think("name", …)`.
- the capability **`reasoners`** section is unchanged and stays **distinct from
  the `models` section** (model ids) — the terminology doc's "do not conflate"
  note;
- the `kind="reasoner"` effect/trajectory strings are unchanged.
- `deploy(reasoners=[obj])` freezes the same name→model/system/reply manifest
  entry `register_reasoner` + `reasoners=["name"]` produced before.

Proof obligation in tests: same flow authored both ways → identical
`flow_json`/`manifest_json`/`artifact_hash`, and the golden corpus is untouched.

### 8.4 Blast radius

`composable_agents/__init__.py` (exports); the `Reasoner`/`think`/`deploy`/`Agent`
signatures; the reasoner registry module; every `examples/*` file; every doc page
showing `register_reasoner`/`reply_schema` (`start/first-flow`,
`start/first-agent`, `authoring-flows`, `cheatsheet`, `reference/python-api`,
`guides/*`). Large but mechanical — the golden corpus guards the wire format, so
any behavioral regression surfaces immediately.

### 8.5 Acceptance

No `register_reasoner` or `reply_schema` anywhere in the public API or
docs/examples; the quickstart and `examples/*` run with `think(obj, …)` +
`deploy(reasoners=[obj])`; the golden corpus is unchanged; all gates green.

## 9. Sequencing

1. **WS1 + its clean-install regression test** — Critical; restores the CLI
   inner loop. First, and independent of everything else.
2. **WS5 object-first reasoners + idiom cut-over** — do **before** WS2 locks the
   docs (no point freezing examples we are about to rewrite). Independent of WS1.
3. **WS2 executable docs + quick-wins** — after WS5, so the migrated examples are
   exactly what CI locks; this is also where the WS1/WS5 doc changes get pinned.
4. **WS3 teaching error messages** — independent, small; any time.
5. **WS4 on-ramp ladder + `switch_on`** — last; builds on WS2's harness and the
   WS5 idiom.

## 10. Testing strategy

- WS1: clean-env CLI regression test (quickstart + multi-pure/`each` flow).
- WS2: doc-block execution harness in CI over `start/` + `cheatsheet` first.
- WS3: unit tests asserting the two `DefineError` messages and spans.
- WS4: every ladder step is a harness-executed doc example.
- WS5: golden corpus unchanged (proves the wire format is identical after the
  idiom change); tests that `think(obj, …)` + `deploy(reasoners=[obj])` produce
  the same IR/manifest as the old string+`register_reasoner` form; a leftover-grep
  gate (reusing the terminology cleanup's §6.4 discipline) asserting
  `register_reasoner`/`reply_schema` appear nowhere in `composable_agents/`,
  `examples/`, or `docs-site/`.
- All must keep the existing gates green: `python -m pytest`,
  `uv run mypy --strict composable_agents`, `ruff`.

## 11. Risks & open questions

- **WS1 = Approach B (decided).** Open implementation detail: confirm the run
  `value` and projection events are fully JSON-serializable for every doc/example
  flow, and that moving the echo-stub helpers into the child leaves `runner.py`'s
  trace-tree rendering unchanged.
- **WS4 = ship `switch_on` (decided).** Open: deterministic naming/pinning of the
  auto-derived selector pure; `cases` match semantics (equality on plucked field).
- **WS5 = object-first reasoners, hard cut-over (decided).** Open: confirm
  `deploy(reasoners=[obj])` is the single registration point and nothing else
  relied on import-time `register_reasoner` side effects (e.g. `Agent` built
  before any `deploy`, or `reasoner_from_ctx` resolution order). The string path
  must keep resolving names that were registered via a prior `deploy`/explicit
  registration for the dynamic case.
- **`__version__ == 0.1.0`** — root cause unconfirmed (the wheel metadata is
  `1.0.0rc1`, and a prior change derives `__version__` from `importlib.metadata`).
  Folded into WS2 quick-wins; dig during implementation.
- **Doc-block harness pragmas** — exact directive syntax and how `mdx` JSX blocks
  are skipped need to be pinned in the implementation plan.

## 12. What not to break (the good parts)

The experiment explicitly praised the **define-by-construction model** as
coherent once internalized and the **`dry_run` + fake-reasoner local story** as
an honest, keyless way to run flows. Every change above is additive to that core;
none of it alters the IR, the shape lattice, or the determinism contract.
