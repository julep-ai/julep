# TODOS

## mem-mcp adoption review follow-ups (deferred from the 2026-07-01 review; not Phase 3/4 scope)

Captured 2026-07-03 while shipping Phase 4 (`docs/plans/2026-07-01-mem-mcp-adoption-phase3-4-agent-loop-and-preconditions.md` lists these as explicit non-goals "tracked in TODOS.md").

- **Rate limiting / backoff jitter.** Provider-side 429/overload handling is retry-ladder
  only; no client-side request pacing or jittered backoff policy knob exists.
- **Budget-semantics unification across backends.** Cost/budget enforcement differs in
  detail between local, Temporal, DBOS, and CMA loop paths; unify the semantics and test
  them cross-backend.
- **Native-downgrade latch refinement.** The native-tools fallback latch (Phase 3) is
  coarse — once latched, a run stays downgraded; consider per-round re-probe or
  latch-expiry.

## Phase 4 minor findings (non-blocking, from review + live run)

- **`subflowQueues` merge precedence** — `execution/harness.py` (~`:2042`): a registered
  agent spec's `subflowQueues` wholesale-replaces the inline APP config dict instead of
  merging; inconsistent with other spec-vs-inline precedence. Cosmetic today (specs and
  inline configs are not mixed in practice).
- **CMA ignores controller `reasoning_effort`/`temperature`/`max_tokens`.** The
  2026-07-03 live-run fix threads all four Reasoner provider fields into agent-loop
  controllers; CMA rejects `prompt_cache` loudly but silently no-ops the other three
  (session creation only carries name/model/tools/system). Decide: reject loudly or wire
  through the CMA session API.

## Trajectory plane: standing determinism gate (capture must stay additive)

- **What:** Make "trajectory capture does not alter flow result or projection" a
  permanent golden-hash CI gate, not just a one-time unit test.
- **Why:** The trajectory plane is additive-by-contract (it must never change
  interpretation or correctness). A future refactor could accidentally let the
  capture path perturb `interpret()` results or the projection. A standing gate
  catches that regression the moment it lands.
- **Pros:** Locks the core invariant forever; cheap to run; reuses the existing
  golden-hash diff harness.
- **Cons:** One more CI job; needs a stable serialization of the projection for
  byte-comparison.
- **Context:** Run a representative flow + agent twice, capture ON and OFF, assert
  identical terminal result AND identical projection event stream (canonical JSON
  bytes). Capture lives in the backend-neutral effect layer + a process-global
  `TrajectorySink` (mirroring `_PROJECTION_SINK`), so the OFF case = no sink
  installed. See `julep/projection.py`,
  `julep/execution/effects.py`.
- **Depends on:** Trajectory plane v1 (A-prime, boundary-aware capture) landed.

## bundle_runner: harden the FlowInput decode-swallow (fail-closed follow-up)

- **What:** `_resolve_activation_bundles` wraps the `from_payloads([...], [FlowInput])`
  decode in `except Exception: continue` (`julep/execution/bundle_runner.py`).
  A `FlowWorkflow` activation whose payload can't decode as `FlowInput` silently
  skips bundle resolution and runs against ambient/stale registry state.
- **Why:** Same fail-open class as the (now-fixed) `_bundle_entries` silent-skip.
  `_bundle_entries` now raises on a present-but-malformed ref; this decode path is
  the remaining swallow. Left as a follow-up because distinguishing a genuinely
  bundle-less activation from a corrupt one needs care, and a hard raise in
  `WorkflowInstance.activate()` is a heavier failure mode to get right.
- **Pros:** Closes the last fail-open in the signed-bundle resolution path.
- **Cons:** Risk of rejecting legitimate activations if the decode can fail for
  benign reasons; needs the P2.6 author's eye.
- **Context:** Decide intended semantics (reject vs. proceed-without-bundle) and
  surface decode failures as span-bearing diagnostics rather than a bare swallow.
- **Depends on:** P2.6 code-as-data bundle path; coordinate with the P3 wasm/EKS
  production-gate work.

## P4 deps-as-data: review follow-ups + wasm-wheel e2e closure

Captured 2026-06-20 after the P4 build (commits `fd530b7..de7713a`). Final codex
review: 0 blocking, 6 non-blocking. Deferred (start P5; breadcrumb the rest). Plan:
`docs/plans/2026-06-11-code-as-data-distribution.md` (P4). Each item is `FIXME(P4-n)`
in the source.

- **S2 wasm-wheel e2e — the skipped leg. CLOSED for regex (2026-06-20).** A
  `register_pure_from_source` dep'd pure now runs a REAL wasi-wheel in wasm. Both root
  causes fixed: (1) **ABI** — the earlier cp314 wheels were built against the WRONG pair
  (wasi-sdk 27 / a different cpython ref), so componentize linking failed with unresolved
  private symbols (`_PyLong_AsByteArray`, `_PyLong_NumBits`). Rebuilt `regex==2024.11.6`
  against componentize-py 0.24.0's EXACT interpreter — dicej/cpython `v3.14.0-wasi-sdk-30`
  + wasi-sdk 33 (clang 22.1.0-wasi-sdk) — and vendored it into
  `julep/execution/_wasm/wasi_wheels/regex/`. (2) **`--stub-wasi` stat trap** —
  the env component now imports each declared dep at MODULE TOP LEVEL (generated
  `env_component.py`), so componentize's pre-init snapshot bakes the module into
  `sys.modules`; the pure body's runtime `import regex` then resolves with no fs stat.
  Both `tests/...::test_real_regex_wheel_env_component_imports_and_runs` now PASS.
- **pydantic-core in wasm — BLOCKED (host interpreter, not the wheel).** Built
  `pydantic_core==2.14.5` against the SAME matched pair (dicej/cpython v3.14.0-wasi-sdk-30
  + wasi-sdk 33, PyO3/maturin, ABI-verified wasm module). componentize linking still fails
  with `unresolved symbol(s): _PyLong_AsByteArray, _PyLong_NumBits`. Root cause: PyO3 0.20.0
  (pinned by pydantic-core 2.14.5, `pyo3-ffi/src/longobject.rs`) imports those PRIVATE
  CPython symbols; componentize-py 0.24.0's embedded interpreter does NOT export them in its
  dylink table (regex links fine because it uses only PUBLIC `PyLong_*` APIs). This is a
  host-interpreter export-surface gap, independent of the wheel toolchain — rebuilding the
  wheel cannot fix it. The matched wheel is staged at `/home/diwank/wasi-deps-v2/dist/
  pydantic_core/` (NOT vendored, since it cannot link). Close via: (a) componentize-py
  exporting those private symbols / a build that does, or (b) bumping pydantic-core to a
  PyO3 version that uses only public APIs (changes the vendored layout the repo expects).
  `pydantic-core` stays in SUPPORTED_WASI_WHEELS but is unvendored → fails closed.
- **FIXME(P4-1) — wheel-source half CLOSED; componentize-determinism half OPEN.**
  `env_builder` no longer downloads from the mutable `latest` tag — it reads immutable,
  in-repo, content-addressed wheels from `_wasm/wasi_wheels/`, so the env build INPUTS are
  reproducible. BUT componentize-py `--stub-wasi` bakes a fresh PRNG seed into the snapshot
  every build and CPython's pre-init heap snapshot is not byte-stable, so the OUTPUT bytes
  (and thus the `envComponent` CAS digest that feeds bundleHash/publishedArtifactHash) still
  vary build-to-build. `envHash` (the deterministic identity) is stable; only the shipped
  component bytes differ. Close via an upstream componentize determinism mode or a post-link
  canonicalization/seed-pinning pass, then add a real-build determinism assertion.
- **FIXME(P4-2) major — module-top PEP 723 dropped (fail-OPEN).** `register_pure` /
  bundle source use `inspect.getsource(fn)`, which omits a module-top `# /// script`
  block, so a dep'd baked pure publishes as no-dep and imports fail late in wasm. Reject
  pures importing an undeclared third-party module, or support module-top metadata; fix
  `examples/regex_extract_flow.py` to the documented placement.
- **RESOLVED(P4-3) — strict PEP 723 validation.** Unknown keys, invalid PEP 508
  dependencies, and invalid `requires-python` specifiers now fail at parse/publish.
- **RESOLVED(P4-4) — canonical manifest presence.** Worker resolution now rejects
  explicit wasm-tier defaults and null encodings for fields that must be absent.
- **RESOLVED(P4-5).** P4-1 wheel vendoring removed the extraction path; no tar is extracted in-package.
- **FIXME(P4-6) nit — vestigial baked-deps parse.** `register_pure` parses PEP 723 but
  module-top is dropped, so baked native pures always get `deps=()`; wire consistently or
  drop the parse.
- **Native tier real e2e (not yet exercised).** The `uv`-venv native tier
  (`native_venv_executor`) resolves/registers behind `JULEP_PURE_NATIVE_DEPS` but its in-venv
  subprocess execution is not run in CI (needs uv + network). A numpy pure through the
  native tier on a worker is the natural P5 dep'd-pure acceptance. Manifest wiring for
  `JULEP_PURE_NATIVE_DEPS` in the k3d/EKS worker manifests is done.

## P5 runtime/infra/docs: review follow-ups

Captured 2026-06-20 after the P5 build (commits `ed6ffb1..8140e8d`). Final codex review:
0 blocking, 7 non-blocking. Deferred (breadcrumbed `FIXME(P5-n)` in source). Plan: P5
section of `docs/plans/2026-06-11-code-as-data-distribution.md`.

- **FIXME(P5-1) major — GC vs publish TOCTOU.** `gc.gc()` can sweep a bundle that is
  mid-publish (blobs written, lease not yet acquired) as an orphan. Publish must acquire the
  lease within/before the publish transaction, or GC must honor a grace window for recently
  written objects. (`julep/gc.py` + `deploy.py` publish path.)
- **FIXME(P5-2) major — lease signature_digest optional (fail-open).** `gc.Lease` allows a
  null `signature_digest`, but the detached ed25519 signature is a hard replay dependency; a
  lease without it lets the signature blob be collected. Require it / always fold it in.
- **FIXME(P5-3) major — native pure fails LATE on the Temporal harness.** `harness.get_pure`
  raises for a `native_venv` pure at pure-call time mid-workflow (fail-closed but late);
  reject native bundle pures at `worker_store.resolve_and_register` so it fails fast.
- **P5-4 minor — runbook overclaims tier uniformity.** `docs/ops/wasm-tier-runbook.md` says
  the tier decision "applies uniformly" across all three backends; native tier is not
  supported on the Temporal harness (see P5-3). Correct the doc.
- **P5-5 minor — AUTHORING native tier caveat.** `docs-site/content/docs/guides/authoring-flows.md` presents the native tier
  as generally supported without the Temporal-harness limitation; add the caveat.
- **P5-6 nit — `GCResult.deleted` redundant** (recomputable from `collectable`).
- **P5-7 nit — `_delete_local_object` shard-dir rmdir** best-effort can race shard recreation.
- **S3CAS GC unimplemented** — `gc()` raises `GCError` for `S3CAS` (paginated list+delete
  deferred); implement if S3-backed CAS retention is needed.
- **Live EKS dep'd-pure acceptance (P5 final gate) — DONE 2026-06-21.** A wasm-tier `regex`
  dep'd pure (`examples/regex_extract_flow.py`) ran end-to-end on the EKS Temporal+KEDA generic
  worker (image `…worker:cad-p6` from `d32aa43`): the env component (bundling the cp314 regex
  wheel) was published to S3, the generic pod resolved it, ran regex in the `--stub-wasi`
  sandbox, returned the correct rollup (4 emails, rows 4, rowsWithEmail 3, totalMatches 6),
  KEDA 0→1→0. (The native uv-venv tier remains Temporal-incompatible — FIXME(P5-3) — so the
  wasm tier is the one that closes this gate.)
- **FIXME — env-component compile blocks the health event loop.** The worker cold-compiles a
  dep'd-pure bundle's wasm env component (cranelift) synchronously at startup/first-resolution,
  which blocks the asyncio loop in `julep/execution/serve.py` so `/healthz` times
  out → liveness SIGTERMs the pod mid-compile (only surfaced on a small/constrained node;
  no-dep bundles compile nothing extra). Worked around in `tooling/eks-cad-demo/worker.yaml`
  with a startupProbe + CPU burst headroom. Real fix: run the wasm `Component` compile off the
  loop (`asyncio.to_thread`) and/or cache/pre-warm the env-component `.cwasm` so cold start is
  bounded.
