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

- **S2 wasm-wheel e2e — the skipped leg.** A `register_pure_from_source` dep'd pure
  cannot yet run a REAL wasi-wheel in wasm. Two causes: (1) **ABI** — upstream
  wasi-wheels ship cp312 `.so` but the base `executor.wasm` is cp314. **SOLVED:**
  cp314 wheels for pydantic-core 2.14.5 + regex are built & ABI-verified at
  `/home/diwank/wasi-wheels-314/dist` with a reproducible `build.sh`. (2) **`--stub-wasi`
  stat trap** — CPython's import machinery `stat()`s and traps (`wasm trap:
  unreachable`); STILL OPEN, orthogonal to ABI. **Close:** vendor the cp314 wheels
  into `composable_agents/execution/_wasm/`, switch
  `env_builder._download_and_extract_wasi_wheel` to local-first/immutable, solve the
  stat trap (non-stub WASI build with a preopened read-only wheel dir, a virtual FS,
  or freeze the `.so`), then unskip
  `tests/test_env_cache.py::test_real_regex_wheel_env_component_imports_and_runs`.
- **FIXME(P4-1) major — non-reproducible env bytes.** `env_builder._WASI_WHEELS_RELEASE`
  is the mutable `latest` tag; componentize-py output is never asserted deterministic.
  `envComponent` feeds bundleHash/publishedArtifactHash, so the same envHash can map to
  different bytes. Fix via the vendored cp314 wheels above + per-wheel content hashes +
  a real-build determinism test.
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
  native tier on a worker is the natural P5 dep'd-pure acceptance, plus wiring
  `CA_PURE_NATIVE_DEPS` into the k3d/EKS worker manifests.
