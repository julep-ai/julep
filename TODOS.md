# TODOS

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
  installed. See `composable_agents/projection.py`,
  `composable_agents/execution/effects.py`.
- **Depends on:** Trajectory plane v1 (A-prime, boundary-aware capture) landed.

## bundle_runner: harden the FlowInput decode-swallow (fail-closed follow-up)

- **What:** `_resolve_activation_bundles` wraps the `from_payloads([...], [FlowInput])`
  decode in `except Exception: continue` (`composable_agents/execution/bundle_runner.py`).
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
  `composable_agents/execution/_wasm/wasi_wheels/regex/`. (2) **`--stub-wasi` stat trap** —
  the env component now imports each declared dep at MODULE TOP LEVEL (generated
  `env_component.py`), so componentize's pre-init snapshot bakes the module into
  `sys.modules`; the pure body's runtime `import regex` then resolves with no fs stat.
  Both `tests/...::test_real_regex_wheel_env_component_imports_and_runs` now PASS.
  Remaining: pydantic-core wheel against the same pair (PyO3/maturin build).
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
- **FIXME(P4-3) major — weak validation.** `deps.parse_pep723` coerces invalid
  `requires-python` to null (envHash collision) and does not PEP 508-validate deps.
  Reject both at parse/publish.
- **FIXME(P4-4) minor — non-canonical manifest accepted.** `worker_store._manifest_pures`
  accepts explicit `executorTier:"wasm"` and absent-vs-null; enforce SPEC §6.5 canonical
  presence. (Bounded: manifest is content-addressed + signed.)
- **FIXME(P4-5) minor — tar extraction.** `env_builder._safe_extract` lacks
  `filter='data'`; add it / refuse symlink+hardlink members.
- **FIXME(P4-6) nit — vestigial baked-deps parse.** `register_pure` parses PEP 723 but
  module-top is dropped, so baked native pures always get `deps=()`; wire consistently or
  drop the parse.
- **Native tier real e2e (not yet exercised).** The `uv`-venv native tier
  (`native_venv_executor`) resolves/registers behind `CA_PURE_NATIVE_DEPS` but its in-venv
  subprocess execution is not run in CI (needs uv + network). A numpy pure through the
  native tier on a worker is the natural P5 dep'd-pure acceptance. Manifest wiring for
  `CA_PURE_NATIVE_DEPS` in the k3d/EKS worker manifests is done.

## P5 runtime/infra/docs: review follow-ups

Captured 2026-06-20 after the P5 build (commits `ed6ffb1..8140e8d`). Final codex review:
0 blocking, 7 non-blocking. Deferred (breadcrumbed `FIXME(P5-n)` in source). Plan: P5
section of `docs/plans/2026-06-11-code-as-data-distribution.md`.

- **FIXME(P5-1) major — GC vs publish TOCTOU.** `gc.gc()` can sweep a bundle that is
  mid-publish (blobs written, lease not yet acquired) as an orphan. Publish must acquire the
  lease within/before the publish transaction, or GC must honor a grace window for recently
  written objects. (`composable_agents/gc.py` + `deploy.py` publish path.)
- **FIXME(P5-2) major — lease signature_digest optional (fail-open).** `gc.Lease` allows a
  null `signature_digest`, but the detached ed25519 signature is a hard replay dependency; a
  lease without it lets the signature blob be collected. Require it / always fold it in.
- **FIXME(P5-3) major — native pure fails LATE on the Temporal harness.** `harness.get_pure`
  raises for a `native_venv` pure at pure-call time mid-workflow (fail-closed but late);
  reject native bundle pures at `worker_store.resolve_and_register` so it fails fast.
- **P5-4 minor — runbook overclaims tier uniformity.** `docs/ops/wasm-tier-runbook.md` says
  the tier decision "applies uniformly" across all three backends; native tier is not
  supported on the Temporal harness (see P5-3). Correct the doc.
- **P5-5 minor — AUTHORING native tier caveat.** `docs/AUTHORING.md` presents the native tier
  as generally supported without the Temporal-harness limitation; add the caveat.
- **P5-6 nit — `GCResult.deleted` redundant** (recomputable from `collectable`).
- **P5-7 nit — `_delete_local_object` shard-dir rmdir** best-effort can race shard recreation.
- **S3CAS GC unimplemented** — `gc()` raises `GCError` for `S3CAS` (paginated list+delete
  deferred); implement if S3-backed CAS retention is needed.
- **Live EKS dep'd-pure acceptance (P5 final gate, still pending).** Brand-new flow with a
  dep'd pure → publish → EKS run via the native tier (`CA_PURE_NATIVE_DEPS` granted on the
  pod), cold start within budget — the real-cluster acceptance, run deliberately like the P3
  EKS run (not in the autonomous build workflow).
