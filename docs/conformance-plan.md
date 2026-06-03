# Spec-Conformance Build Plan

> Drives the Python canonical implementation (`composable_agents/`) to full
> conformance with the spec (`TODO.md`), in dependency-aware batches, **TDD-first**.
> Implementer: **Codex** (`cdx` / `codex exec`). Orchestrator/verifier: Claude.

## Principles

1. **TDD per the spec's own rule.** *"An item is conformant only when its invariant
   holds in code with a test."* For each gap: write the **failing invariant test
   first**, then implement until green. No fix lands without a test that would have
   caught the bug.
2. **The IR is the magic.** Preserve and strengthen the IR's guarantees. Changes to
   `ir.py` / `freeze.py` / `shapes.py` are reviewed with extra care.
3. **Hash churn is intentional and ordered.** The freeze/replay batch (2a) changes
   hash values on purpose. The §13 golden corpus is pinned **last** (Phase 4), once.
4. **Each batch is atomic:** red test → green implementation → commit. The full
   suite (`.venv/bin/python -m pytest`) must pass at every commit.
5. **No silent drift.** When code and spec disagree, fix one on purpose.

## Verified gap status (24 punch-list items)

22 genuinely **open** · 1 **partial** (P1-5) · 1 **already-done** (P2-3, add a
regression test only). Evidence gathered against real code; key anchors below.

| Tier | Item | Status | Key anchor |
|---|---|---|---|
| P0-1 | Race settles on completion, not success | open | `interpreter.py:325`, `harness.py:297` `t.result()` re-raises |
| P0-2 | Hedge starts branches eagerly | open | `harness.py:293`, `interpreter.py:315` `ensure_future(c)` |
| P0-3 | Approval gating unmodeled/unenforced | open | no `approval` on `ToolGrant`; no dangerous-effect gate check |
| P0-4 | Empty grant list = allow-all in agent loop | open | `harness.py:500` `if granted_set and tool not in granted_set` |
| P0-5 | Agent CALLs ignore tool contract for retry | open | `harness.py:515` hardcodes `idempotent_max_attempts` |
| P0-6 | MCP calls carry no idempotency key | open | `activities.py:110` `mcp_call(server, tool, value)` (no cid) |
| P1-1 | `canonical_json(default=str)` coerces | open | `ir.py:248` |
| P1-2 | Pure-drift computed, never verified | open | `purity.source_hash_of` unused at startup |
| P1-3 | Tool hash omits output_schema/contract/asserted | open | `contracts.py:84` `tool_hash` payload |
| P1-4 | No `artifact_hash` | open | `deploy.py` `Deployment` has none |
| P1-5 | `models` gates brain names, not model ids | partial | `capabilities.py:169` |
| P1-6 | `maxCalls` parsed, never enforced | open | `capabilities.py:94`; no counter |
| P1-7 | MCP version pins not enforced | open | `capabilities.py:107`; `enforce_compile` skips version |
| P1-8 | No subflow grant boundary | open | no `subflows` field on `CapabilityManifest` |
| P1-9 | Agent budget checked after controller spent | open | `harness.py:471-492` |
| P1-10 | WHOLE_SESSION par degradation warned, not done | open | `validate.py` warns; `interpreter.py:191` doesn't degrade |
| P1-11 | Human-gate timeout drops input | open | `harness.py:363` `"input": None` |
| P1-12 | Projection cost not charged | open | `interpreter.py:111` `did(...)` no `cost=` |
| P2-1 | Staged plans not bound to parent manifest | open | `staged.py:128`; no `bind_plan_to_manifest` |
| P2-2 | Process-global registries | open | `dotctx._BRAINS`, `purity._REGISTRY`, `activities._CTX` |
| P2-3 | Non-retryable policy errors typed | **done** | `errors.py`; `harness.py:121` — add regression test |
| P2-4 | `Ann.timeout`/`Ann.cache` inert | open | `ir.py:122` `CacheHint` unused; timeout only for gate |
| P2-5 | No py.typed/mypy/ruff/CI matrix | open | absent |
| P2-6 | No CLI / `explain(diagnostics)` | open | absent |

## Phases & batches

### Phase 0 — Guardrails first
- **B0.1 Tooling net:** add `composable_agents/py.typed`; `[tool.ruff]` + `[tool.mypy]`
  (strict on pure core, lenient on `execution/`) to `pyproject.toml`; GitHub Actions
  CI matrix (py 3.10–3.12 × temporal {on, off}) asserting the package imports and
  the suite passes both ways. *(P2-5)*
- **B0.2 Test infra:** `tests/invariants/` package + a golden-corpus **harness**
  (`tests/golden/` with the 10 fixtures *defined*, hashes **not yet pinned** —
  asserted in Phase 4). Helpers for fast/slow/failing fake hands.

### Phase 1 — P0 safety (correctness & effect authorization)
- **B1a Concurrency core** *(P0-1, P0-2)* — change the `Env` concurrency API to take
  branch **thunks** `Callable[[], Awaitable]` (not pre-started coroutines) in the
  `Env` Protocol, `InMemoryEnv`, and `_TemporalEnv`; update `interpreter._eval_par`.
  - `race`: return first **successful** branch; ignore failures until *all* fail,
    then raise aggregate. `quorum`: first **K successes**. `hedge`: branch 0 starts
    immediately; branch *i* starts only after `hedge_ms` without enough successes.
    Cancel losers on settlement. Branch order is the success tie-breaker.
  - **Tests first:** fast-failure+slow-success (slow success wins); all-fail →
    aggregate error; cancel-of-losers (loser side effect never runs); hedge laziness
    (later branch not constructed if branch 0 succeeds before `hedge_ms`).
- **B1b Effect-authorization model + deploy gates** *(P0-3, P0-4 compile side)* —
  `ToolGrant.approval: bool`; `enforce_compile` emits a **blocking** diagnostic when
  a `dangerous`-effect or `approval:required` tool is referenced outside a
  `human_gate`; normalize `None`=unconstrained vs `[]`=deny-all in every grant check.
  - **Tests first:** deploy rejects ungated dangerous tool; `[]` denies, `None` allows.
- **B1c Agent-loop runtime enforcement** *(P0-4 loop side, P0-5, P1-9)* —
  deny-all + approval refusal in the loop; thread tool **contracts** into the agent
  spec so CALL retry/effect uses `_retry_policy_for(contract, policy)` like the flow
  path; **budget pre-check before** the controller call (terminate `over_budget`
  without spending), then charge, then pre-check each action.
  - **Tests first:** `[]` grant denies in loop; approval-required tool refused
    without open gate; write-tool CALL gets cautious retry; controller call that
    would exceed budget terminates without invoking it.
- **B1d Transport idempotency** *(P0-6)* — thread the deterministic `cid` as an
  idempotency key on **MCP** calls too (extend `McpCaller` signature); a transport
  that cannot carry the key MUST NOT be admitted as `required`.
  - **Tests first:** MCP caller receives the cid; retried MCP call reuses it.

### Phase 2 — P1 integrity & capability consistency
- **B2a Replay/freeze hash chain** *(P1-1 → P1-3 → P1-4 → P1-2)* — strict
  `canonical_json` (drop `default=str`, raise on non-JSON); fold
  `output_schema`/`contract`/`asserted` into the tool **execution hash**; expose a
  single `artifact_hash` on `Deployment` over flow+manifest+pure-source-hashes+brain
  defs+execution policy+capability manifest+framework version; verify pure-source-hash
  drift at workflow start (fail before any execution).
  - **Tests first:** non-JSON payload raises; two tools differing only in
    output_schema/contract get different hashes; `artifact_hash` stable & changes
    when any input changes; drifted pure source fails at startup.
- **B2b Remaining grants** *(P1-5, P1-6, P1-7, P1-8)* — resolve `Brain.model` and
  gate the **model id**; enforce `maxCalls` with a deterministic counter in
  interpreter + Temporal Env (keyed by tool ref/hash); enforce MCP **version pins**
  against frozen `server_version`; add a `subflows` grant section gating `SUB`.
  - **Tests first:** one per grant (deny path + allow path), incl. counter exhaustion.
- **B2c Runtime semantics** *(P1-10, P1-11, P1-12)* — degrade a `par` that reads
  WHOLE_SESSION to sequential + annotate the projection (validator warning and
  runtime behavior must agree); human-gate timeout returns decision **and** original
  input; charge projection cost (`Ann.cost` → default leaf estimate → brain
  token/cost metadata) so `costByShape` is populated in real runs; emit scheduling
  attrs (`merge`/`winner`/`cancelled`).
  - **Tests first:** degraded par runs sequentially + annotation present; timeout
    result carries input; `costByShape` non-empty after a real run; race emits winner.

### Phase 3 — P2 ergonomics & DX
- **B3a Staged-plan manifest binding** *(P2-1, §10.1)* — `bind_plan_to_manifest`
  resolves each plan `ToolRef` against the parent manifest and sets `frozen_hash`
  (zero matches → reject; multiple → reject unless hash-pinned); call from
  `admit_plan` / `compilePlan`; enrich trace entries toward honest extraction.
- **B3b Explicit `Registry`** *(P2-2)* — a `Registry` (brains, pures, worker ctx)
  injected instead of module globals; keep thin global shims for back-compat.
- **B3c Annotation wiring** *(P2-4)* — honor `Ann.timeout` per call/brain activity;
  wire `Ann.cache` or remove `CacheHint`.
- **B3d Regression + DX** *(P2-3, P2-6)* — test asserting policy errors are typed
  non-retryable; `cli.py` (`freeze`/`validate`/`inspect`/`run-local`/`graph`) +
  `explain(diagnostics)`; `[project.scripts]` entry point. Tighten mypy-strict on core.

### Phase 4 — Capstone: §13 golden corpus
Pin **known-value** hashes across all 10 fixtures: simple pipeline · subagent
firewall · race · quorum · hedge · human gate · staged plan · agent app · frozen
manifest · capability manifest. Each fixture pins: input flow, frozen IR JSON,
manifest with tool hashes, validate diagnostics, surface/closed shapes. Port useful
ideas from `composable_agents_alt_ts/.../golden-fixtures.ts`. A refactor that changes
the IR or hashing must break these tests.

## Codex execution protocol (per batch)

1. Claude dispatches a batch to Codex with: the spec section(s), the failing-test
   requirement, the implementation sketch, files in scope, and acceptance criteria.
2. Codex writes the failing test(s), confirms red, implements, confirms green with
   `.venv/bin/python -m pytest`, and reports a summary + diff stat.
3. Claude verifies independently (re-runs the suite, reviews the diff, may run an
   adversarial review agent), then commits the batch. On failure, Claude sends a
   correction via `codex exec resume`.
4. Independent, non-file-overlapping batches may run as parallel Codex sessions;
   anything touching the same module stays sequential.

## Addendum — locked decisions (from `elnino_capacity_swarm.py`, the DX north-star)

The El Niño example is *specification-by-example* for the public API. Decisions:

- **Full rename, drop old names.** The algebra-faithful surface is canonical:
  `seq` (was pipeline), `par` (parallel), `alt` (route), `iter_up_to` (critique),
  `sub` (subagent), `app` (escalate), `mcp`/`native` ref builders + `call(ref)`
  (was mcp_call / call(name)). Old names are **removed**; README + all tests are
  updated. Signature ergonomics: `race/hedge/quorum` accept a list + `k=`/`reduce=`/
  `hedge_ms=`; `human_gate(prompt=, timeout_s=)`; `Ann(cost_usd=, timeout_s=)`;
  `Brain(system=)`; `sub(ref)` with a default contract. Caps gain
  `brains:`/`subflows:`/`approval:`/`maxCalls:`/version-pins.
- **El Niño = acceptance test (deploy-clean + InMemoryEnv dry-run).** A corrected,
  runnable version lands under `examples/elnino/` and is asserted in Phase 4.

### Phase A — API surface (runs after Phase 0, before Phase 1)
- **A1 Mechanical rename + signature ergonomics.** Renames + list/kwarg signatures +
  caps section parsing (parse/store only; enforcement stays in B1b/B2b). `alt` stays
  **binary** here. Suite + ruff stay green throughout.
- **A2 IR generalization (TDD).** Generalize `ALT` to a **classifier+cases multiway
  switch**: `alt(select=<pure→key>, cases={key: flow}, default=…)`, with binary
  `alt(pred, a, b)` as 2-case sugar — **one** branching construct, IR stays minimal.
  Extend the `APP` node to carry inline agent config (`tools`/`subflows`/`budget`/
  `max_rounds`) as data; enforcement wires in B1c/B2b. Hash changes are fine
  (golden corpus pinned in Phase 4).

Phases 1–3 then proceed in the new API. Phase 4 adds the El Niño acceptance test
alongside the golden corpus.
