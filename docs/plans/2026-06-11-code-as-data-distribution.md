# Code-as-data worker distribution: CAS bundles, wasm pure execution, deps-as-data

> **STATUS: PLANNED (not started).** Architecture reviewed by Codex 2026-06-11 — verdict **SOUND
> WITH CHANGES**; all 7 findings (3 blocking, 4 major) probe-confirmed against the codebase and
> folded into this document. Review artifacts: `.codex-runs/wasm-arch-review/`. Awaiting
> scheduling decision relative to the mem-mcp pilot port (recommendation at the end).

## Context

Every flow deployment today requires building a docker image bundling the framework, the flow
module (pures + tools + reasoner config), and a worker entrypoint; pushing to a registry; and rolling
the worker deployment (`tooling/k3d-flow-demo/Dockerfile` is the current shape). The failure mode
is recent and real: a worker image predating the current IR could not deserialize arr static args
or resolve `std.*` pures, forcing a rebuild+push+rollout just to run a flow. Flows change at
flow-cadence; images should change at framework-cadence.

Goal state: worker deployments are flow-agnostic. Deploying a flow = publishing content-addressed
data — no docker build, no registry push, no rollout in the flow author's loop. Dependencies stop
being installed on production nodes at all: "install" becomes construction of an immutable,
content-addressed artifact at deploy time — the same move flowJson made for workflow definitions.

Settled invariants this design builds on (not re-opened here): content-hash pinning with pures
pinned by source sha256 and verified at worker registration (`purity.py`); deny-by-default
`CapabilityManifest` with effects derived from `ToolContract`; frozen wire-stable `std.*` family
baked in the package; arr static args + Ann retry fields absent-when-unset; the golden corpus
(`tests/golden/golden_hashes.json`) never regenerated; `docs/SPEC.md` as the cross-language wire
contract; Temporal/DBOS/InMemory backends; KEDA scale-to-zero workers (~10s cold start measured).

## Design

### The bets

1. **No flowJson change; runtime identity joins the artifact envelope.** flowJson already pins
   pures by name + source hash and stays byte-identical. Distribution bytes live in a sidecar
   **bundle manifest** — `{artifactHash, pures: [{name, sourceHash, source | binaryRef, envHash?,
   abi}], signature}` — content-addressed in the CAS, never inside flowJson. But identity is
   `artifact_hash`, which hashes the whole envelope (deploy.py `artifact_components`): a versioned
   **`pureRuntimeRefs`** component — `{name: {sourceHash, envHash?, abi, bundleHash,
   executorTier}}` — joins `artifact_components`, absent-when-unset so all existing artifacts and
   the golden corpus are untouched by construction. Two deployments differing only in env or tier
   get different artifact hashes. *(Amended per review: "sidecar only" left runtime identity
   outside the program hash.)*
2. **The bundle reference travels everywhere flowJson travels.** `FlowInput`, `resolveSubflow`,
   the DBOS input shape, and `continue_as_new` payloads carry the envelope (or `bundleHash`)
   alongside flowJson/manifest/pinnedPures, so ref-resolved children and continued segments replay
   against the exact bundle they started with, across worker restarts and CAS updates. *(Added per
   review: these paths today carry only flowJson/manifestJson/pinnedPures.)*
3. **Worker verification contract unchanged; baked and bundled must agree.** A pure may be
   pre-registered (baked) or arrive via bundle: fetch source by hash from CAS, verify sha256,
   register. If a name is both baked and bundled, hashes must agree — error, not precedence.
   `std.*` stays baked and native forever.
4. **Execution tiers are capability-governed; wasm default, fresh instance per call.**
   Bundle-sourced pures execute in a wasm sandbox: a frozen CPython-on-wasm base component
   (componentize-py, toolchain pinned, built component vendored), pure source as payload, JSON
   value + JSON static args in, JSON out, no I/O imports, fuel + epoch deadline. **Default is a
   fresh instance (or reset-to-preinitialized state) per invocation** — instance reuse across
   calls leaks mutable CPython module state (caches, counters, seeded RNGs) and silently breaks
   the determinism the sandbox is supposed to enforce; reuse is permitted only if the spike proves
   deterministic reset with adversarial coverage. A native tier (uv-managed venv, subprocess)
   exists for deps that don't compile to WASI and requires an explicit capability grant.
5. **Envs are pre-initialized component binaries, built at deploy time, content-addressed.** A
   pure declaring deps (PEP 723 inline metadata next to the `@pure`) gets an `envHash` — hash over
   the resolved lockfile, python version, and base-component version — joining `pureRuntimeRefs`
   (and therefore `artifact_hash`). The env artifact is a **pre-initialized wasm component binary**
   (Wizer/component-init style: deps imported at build time, emitted as a new initialized
   component) plus a wasmtime compiled-module cache — *not* a restorable memory blob; no such
   restore API exists. `deploy().publish(store)` builds or requests it and warms the CAS; workers
   fetch, deserialize, instantiate. Rationale for env-in-identity: source hash alone cannot
   distinguish a pure pinned against numpy-1.x from numpy-2.x — a hole in source-only pinning this
   closes as a side effect.

### Architecture (target)

```
deploy(flow).publish(store)                    runtime image (framework cadence)
  flowJson ──────────► CAS (S3 / local-dir) ◄── worker: fetch → verify hash → register
  bundle manifest ───►   pure source            ├─ wasm executor (CPython base, fresh
  env components ────►   env-hash binaries      │   instance per call, fuel+deadline)
                                                └─ native tier (uv venv, capability-gated)
```

- **CAS store**: put/get by sha256; backends local-dir (dev/k3d) and S3 (EKS); OCI only if a
  Spin-based tool fleet ever materializes. **Replay safety rule, effective from P2: CAS objects
  are immutable and are never deleted within workflow-history retention; any future GC takes
  leases against live artifact hashes first.** Replay depends on these blobs; the rule precedes
  the dependence, the GC implementation is an optimization (P5).
- **Runtime image**: framework + interpreter + std + wasmtime host + vendored base component +
  generic executors. Rebuilt only on framework releases.
- **Signing**: ed25519 over the bundle manifest, key allowlist on workers; IAM-restricted bucket
  write is the first-line boundary on EKS.

## Phases

Each phase lands independently green (`python -m pytest` AND `uv run python -m pytest`,
`uv run mypy --strict composable_agents`, `uv run ruff check .`, golden corpus unregenerated).

### P1 — spike (de-risking gate; throwaway-eligible)

- (a) **Wasm load path with numbers**: build the CPython-base component (componentize-py, pinned),
  pre-initialize, wasmtime compiled-module cache; execute a real pure JSON-in/out. Measure: base
  component size, build time, and **per-call cost under the fresh-instance-per-call model**
  (deserialize-from-cache + instantiate + exec). Decide: is per-call instantiation within budget?
  Reuse-with-reset is the fallback and must prove deterministic reset adversarially (module-global
  mutation across calls has no observable effect).
- (b) **Bundle round-trip**: local-dir CAS → worker resolves, verifies, registers; draft
  `pureRuntimeRefs` envelope shape end-to-end.
- Exit criteria: latency/size numbers in tool and a go/no-go on fresh-per-call; envelope shape
  confirmed against `artifact_components`. External-clock risk surfaces here: WASI 0.2→0.3 and
  componentize-py churn — pin the toolchain, vendor the built base component as an artifact.

### P2 — code-as-data, native execution, **dev-gated**

- CAS store module (local-dir + S3), immutability/no-GC rule stated and enforced (no delete path
  shipped at all).
- `pureRuntimeRefs` joins `artifact_components` (versioned, absent-when-unset; golden untouched).
- Bundle manifest build + ed25519 signing in `deploy().publish(store)`; worker key allowlist; CLI
  plumbing (`--store`).
- Worker store-resolution path; baked-vs-bundled hash disagreement is an error with an
  operator-actionable message.
- **Envelope threading**: `FlowInput`, `resolveSubflow`, DBOS input, `continue_as_new` carry the
  bundle reference.
- Gates: golden corpus unregenerated; baked path byte-identical; **a ref-resolved child and a
  continued segment with bundle-sourced pures replay across a worker restart**; demo = author a
  new flow, publish, run **on k3d** with zero docker involvement. Per review, P2 does **not** ship
  to shared/prod EKS: bundle-sourced pures execute in-process inside the deterministic workflow
  path, and runtime-arriving code there is a replay-desync hazard even from honest authors
  (`purity.py` determinism contract). Production acceptance moves to P3.

### P3 — wasm executor tier (production gate moves here)

- Vendored base component; sandboxed exec (no I/O imports, fuel + epoch deadline); fresh instance
  per call (or proven reset); executor selection policy — bundle-sourced → wasm, baked std →
  native.
- Gates: wasm-vs-native behavior parity on both examples' dry_run; adversarial probes — pures
  attempting filesystem/network/clock access fail closed with span-bearing diagnostics in the
  house style; cross-call module-state mutation has no observable effect. **EKS acceptance demo
  lands here**: publish + run on EKS, zero docker, cold start within the P1 budget.

#### P3 status — what landed (branch `code-as-data`)

Landed and locally gated (`pytest` + `mypy --strict composable_agents` + `ruff`, golden corpus
unregenerated/byte-identical):

- **Wasm executor host + vendored component.** Process-global, lazily-initialized `WasmExecutor`
  runs each bundle-sourced pure in a fresh wasmtime CPython component instance per call (one
  Engine `wasm_component_model`+`consume_fuel`, one Component deserialized once with a lazily-built
  `.cwasm` cache, bare Linker, fresh Store+fuel per call, optional epoch deadline). The vendored
  `executor.wasm` is committed; the `.cwasm` cache and componentize-py bindings are gitignored.
- **Registry-shim/by-name ABI.** The component replicates the `@pure(...)` registry shim so the
  SAME bundle source runs identically native and in wasm.
- **Single-seam selection.** `Registry.get_pure` returns a wasm-bound callable for `executor ==
  "wasm"` (bundle-sourced) and the native fn for `native` (baked + all `std.*`). All three backends
  (Temporal harness, DBOS, CMA) inherit the tier through the registry; the Temporal worker passes
  `wasmtime` through the workflow sandbox; bundle resolution is ungated (the P2 `JULEP_BUNDLE_NATIVE_EXEC`
  dev gate is gone) and lands on the wasm tier end to end.
- **Gates met locally.** wasm-vs-native parity on the grade-scores demo flow's dry_run
  (`tests/test_wasm_parity.py`); adversarial probes (clock/fs/net/entropy) fail closed as a
  structured `PureExecutionError` with `error_type` ∈ {`WasmSandboxTrap`,`WasmFuelExhausted`,
  `WasmDeadlineExceeded`} naming the offending pure and pointing at the runbook — not a bare
  `WasmtimeError` (`tests/test_wasm_sandbox.py`); cross-call module-state mutation has no observable
  effect; executor-selection policy (bundle→wasm, baked `std.*`→native, and a bundle may not ship a
  `std.*` pure) (`tests/test_executor_selection_policy.py`); plus per-backend routing and a full e2e
  Temporal flow whose only pure is bundle-sourced (`tests/test_bundle_wasm_backends.py`).
- **Infra/docs.** k3d demo worker Deployment carries `STORE_URL`/`JULEP_BUNDLES`/`JULEP_BUNDLE_ALLOWED_SIGNERS`;
  the EKS-target `tooling/sandbox-k8s/worker.yaml` carries them as a documented P3 wasm-tier block.
  `docs/ops/wasm-tier-runbook.md` covers signing tiers, executor tiers, the failure taxonomy, and CAS
  retention. `pyproject` ships the build-only `wasm` extra (`wasmtime>=45,<46`).

**Live EKS zero-docker acceptance run — DONE (2026-06-20).** Ran on the live EKS cluster
`julep-v2-temporal-demo` (us-east-1), KEDA + in-cluster Temporal (RDS). The grade-scores flow was
published as a signed bundle to an S3 CAS (`s3://julep-v2-cad-cas-<account-id>/cad`) and run by the
**generic** worker image (`…worker:cad-wasm-v2`, `composable_agents[temporal,store,wasm]`, built
once — no per-flow image): the three `cad.demo.*` pures arrived only as the S3 bundle and executed
in the wasm sandbox on the pod. KEDA scaled the worker **0 → 1 → 0** on queue backlog; result
correct (`passRate 0.8`, tally A1/B2/C1/F1) across three runs. **Cold start: ~15s warm-image**
(KEDA + S3 bundle fetch + wasm), at the P1 budget; ~20–23s including a first-time image pull.
Tooling: `tooling/eks-cad-demo/{publish.py,worker.yaml}`. The run surfaced and fixed a real
pre-existing bug — `startTrajectory`/`flushStructural` were missing from `worker.ACTIVITIES`, so
trajectory capture silently no-op'd under the best-effort swallow (now registered + guarded by
`tests/test_worker_activity_registration.py`). The local gates also exercise the full bundle→wasm
path against a Temporal time-skipping server, the DBOS env, the CMA env, and a real signed bundle.

### P4 — deps as data

- PEP 723 parsing at deploy; `envHash` (lockfile + python version + base-component version) joins
  `pureRuntimeRefs`/identity; SPEC in lockstep.
- Env builder (deploy-machine first; builder job later) producing pre-initialized component
  binaries keyed by envHash; worker env cache; uv-venv native tier behind capability grant.
- Validator: a dep-declaring pure with no buildable env and no native grant is blocking.
- Gates: a pure using a **currently supported wasi-wheel dep (pydantic-core or regex)** runs
  end-to-end from a published env; an off-list dep runs via the native tier only with the grant;
  envHash distinguishes dep versions of otherwise-identical source. **numpy is explicitly not a
  gate** — wasi-wheels does not cover it today; "private numpy WASI wheel builds and pins" is a
  separate spike, scheduled only if mem-mcp needs it in-pure.

### P5 — runtime image + infra + docs

- Runtime image replaces the per-flow image; k3d + EKS manifests gain `STORE_URL`; KEDA untouched.
  Status: the canonical runtime image lives at `tooling/runtime-image/`, and the k3d/EKS
  manifests carry the `JULEP_PURE_NATIVE_DEPS` native-tier grant commented off by default.
- GC implementation (leases against live artifact hashes) as the optimization of P2's standing
  rule.
- `docs/SPEC.md`: bundle manifest format + `pureRuntimeRefs` (wire commitments); AUTHORING: PEP
  723 deps on pures; ops/trust runbook (signing, tiers, CAS retention).
- Acceptance: brand-new flow with a dep'd pure → publish → EKS run, no docker anywhere in the
  loop, cold start within budget.

#### P5 status — what landed (2026-06-20, on `main` `67cfd93`)

GC leases (`composable_agents/gc.py`), the first-class runtime image (`tooling/runtime-image/`),
AUTHORING PEP-723-deps + ops/trust runbook, and a CI native-tier exec test all landed; 1070
passed / 24 skipped, mypy/ruff clean, golden byte-identical.

**EKS acceptance — partial (no-dep regression PROVEN; dep'd-pure deferred).** The generic
runtime image rebuilt from `main` (`…worker:cad-p5`) ran the no-dep `grade_scores` flow on the
EKS Temporal+KEDA worker end to end: the latest P4/P5 code re-published a **byte-identical**
bundle (JULEP_BUNDLES unchanged → publish path is golden-safe), the generic pod resolved it from S3,
ran it, returned the exact expected result (`passRate 0.8`, tally A1/B2/C1/F1), KEDA scaled
**0→1→0**, ~28s cold start incl. a fresh image pull. This re-confirms the whole code-as-data
pipeline under all the P4/P5 changes.

**Dep'd-pure-in-wasm on EKS — DONE (2026-06-21, regex).** After landing the wasm-wheel close
(`d32aa43`: `regex==2024.11.6` rebuilt against componentize-py 0.24.0's exact interpreter —
`dicej/cpython@v3.14.0-wasi-sdk-30` + wasi-sdk 33 — plus a top-level pre-init import so the
`--stub-wasi` snapshot bakes the module in), a wasm-tier `regex` dep'd pure
(`examples/regex_extract_flow.py`) ran end to end on the EKS Temporal+KEDA generic worker (image
`…worker:cad-p6`): the env component bundling the regex wheel was published to S3, the generic pod
resolved it, ran regex **in the `--stub-wasi` wasm sandbox** (regex never installed on the worker),
returned the correct rollup (`emails` ×4, `rows` 4, `rowsWithEmail` 3, `totalMatches` 6), KEDA
**0→1→0**. The dep traveled as data; zero docker in the per-flow loop; deps-as-data closed for the
wasi-wheel set on the durable harness.

Caveats: (1) `pydantic-core` stays **blocked** — a host-side gap, not a wheel defect: PyO3 0.20
(pinned by pydantic-core 2.14.5) imports private CPython symbols (`_PyLong_AsByteArray`/
`_PyLong_NumBits`) that componentize-py 0.24.0's interpreter doesn't export; needs a pydantic-core
on a newer PyO3 (public-API only) or componentize exporting them. (2) The **native** (uv-venv) tier
remains Temporal-incompatible by design (`FIXME(P5-3)`). (3) Cold-compiling the env component blocks
the worker's asyncio health loop on a small node (worked around with a startupProbe + CPU headroom
in `tooling/eks-cad-demo/worker.yaml`; real fix = compile off-loop / cache the `.cwasm`). (4) Env
component **output** bytes aren't bit-reproducible (componentize `--stub-wasi` bakes a fresh PRNG
seed) so a dep'd bundle's `envComponent`/`bundleHash` varies build-to-build though `envHash` is
stable — P4-1 input-reproducibility done, output-reproducibility open. All tracked in TODOS.md.

### P6 — parked: tools out-of-process

MCP tool executor + Spin pilot (true scale-to-zero tool fleet). Deliberately its own arc — authn
and idempotency tokens crossing the wire are independent design questions.

## Verification

```bash
uv sync --extra dev
python -m pytest && uv run python -m pytest    # both envs; backend tests must not silently skip
uv run mypy --strict composable_agents
uv run ruff check .
# golden corpus passes unregenerated in every phase
# P2: publish→run on k3d, replay-across-restart gate
# P3: EKS zero-docker acceptance + adversarial sandbox probes
# P4: wasi-wheel dep end-to-end; native tier requires grant
```

## External review

Codex architecture review 2026-06-11 (fenced: verdict + ≤8 ranked findings; artifacts in
`.codex-runs/wasm-arch-review/`): **SOUND WITH CHANGES.** All findings probe-confirmed against the
code and folded in: (B1) runtime identity must join `artifact_hash` via `pureRuntimeRefs`
(deploy.py `artifact_components`) → bet 1 amended; (B2) P2 in-process exec of runtime-arriving
code inside the workflow path is a determinism hazard, not just a trust one (purity.py contract) →
P2 dev-gated, EKS acceptance moved to P3; (B3) `FlowInput`/`resolveSubflow`/`continue_as_new`
carry no bundle pointer → bet 2 added, P2 deliverable + replay-across-restart gate; (M) instance
reuse leaks module state → fresh-per-call default; (M) Wizer "memory memcpy" misstated →
pre-initialized component binaries + compiled-module cache, P1 measures that path; (M) numpy
wasi-wheel gate not real today → gate swapped to pydantic-core/regex, numpy a separate spike;
(M) CAS GC deferred past replay dependence → immutability/no-delete rule effective from P2.

## Risks

- **WASI / componentize-py churn** (external clock): pinned toolchain + vendored base component;
  P2 ships the headline value with zero wasm dependence, so churn cannot block the arc.
- **Per-call instantiation latency**: if fresh-per-call misses budget and reset can't be proven
  deterministic, chatty glue pures stay on the native tier and wasm covers dep'd/heavy pures —
  degraded but sound. The spike makes this call cheap.
- **wasi-wheels coverage is thin** (pydantic-core, regex today): the curated-closure honesty from
  the design discussion stands — off-list C extensions use the granted native tier.
- **CAS becomes a replay dependency**: immutability rule + no delete path until leases exist;
  bucket versioning/backup in the runbook.
- **Python version skew**: envHash includes interpreter + base-component versions by construction.
- **Two execution tiers to maintain**: accepted cost; mirrors the two-dialect cost accepted in the
  @flow arc, mitigated by wasm-default policy.

## Open questions (for Diwank)

- Cold-start and per-call latency budgets — numbers the P1 spike should be held to (proposal:
  ≤15s KEDA cold start incl. CAS fetch; ≤10ms per pure call fresh-per-call).
- Confirm P6 stays parked; confirm S3 (which bucket/account) for the EKS store and where the
  signing keypair lives.
- Scheduling: recommendation is **P1+P2 before or alongside the mem-mcp pilot port** — after P2,
  every ported workflow iterates without image rebuilds, so the port itself gets faster; P3–P5
  can land while the pilot proceeds.

## Build mechanics

Same machinery as the @flow arc: sequential Codex TDD batches per phase (prompt files under
`.codex-runs/<batch>/`), orchestrator runs gates and commits, parallel verify panel per phase
(independent gates + plan-conformance reader + fenced `codex review`), blocking findings
probe-confirmed before fixing.
