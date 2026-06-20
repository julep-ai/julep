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
