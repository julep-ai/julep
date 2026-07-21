---
title: "WASM Execution Tier"
description: "Operate the wasm tier for sandboxed pure execution: building wheels, the cwasm cache, and troubleshooting."
---

Bundle-sourced pures (registered via `register_pure_from_source` after arriving
from a signed CAS bundle) execute inside a **wasmtime CPython sandbox** — a fresh
instance per call, with no clock, filesystem, network, or entropy. A bundle pure
with off-list dependencies may instead execute in the explicit native tier,
behind a per-pure operator grant. Baked pures (`register_pure`) and `std.*` keep
running natively in-process, unchanged. This runbook covers the operational and
trust surface of those bundle execution tiers.

## What runs where

| Pure origin | Registration | Executor | Sandbox |
| --- | --- | --- | --- |
| Baked into the worker image | `register_pure` / `@pure(...)` | native (in-process) | none (trusted code) |
| `std.*` library | baked | native | none |
| Signed CAS bundle, no deps or supported WASI-wheel deps | `register_pure_from_source` | **wasm** | wasmtime, fresh per call |
| Signed CAS bundle, off-list deps with `JULEP_PURE_NATIVE_DEPS` grant | `register_pure_from_source` | **native** (`uv` venv subprocess) | none (operator-trusted bundle source) |

The selection is a single seam: `Registry.get_pure(name)` returns a wasm-bound
callable for `executor == "wasm"` entries and a native-venv callable for
capability-granted `executor == "native"` bundle entries. All three backends
(Temporal harness, DBOS, CMA) route pure lookups through the registry, so the
tier decision applies uniformly. The wasm call runs **synchronously** inside the
interpreter (it is deterministic pure compute), not as a Temporal activity, so
it does not perturb the projection/trajectory event stream relative to a native
pure.

## Execution tiers and trust boundaries

The **wasm tier** is the default for bundle pures. Bundle-shipped source runs in
the wasmtime sandbox, fresh per call, with no clock, filesystem, network, or
entropy. Treat this as the untrusted-code-safe tier for deterministic pure
compute.

The **native tier** exists only for bundle pures whose declared dependencies are
off the curated WASI-wheel set. The worker executes the bundle-shipped source as
a real OS subprocess in a `uv`-managed venv
(`julep/execution/native_venv_executor.py`) with the declared deps
installed. This is outside the wasm sandbox. `JULEP_PURE_NATIVE_DEPS` is therefore
the operator trust boundary: adding a pure name to that allowlist means trusting
that bundle's source to run as native code on the worker.

`JULEP_PURE_NATIVE_DEPS` is empty by default, per-pure, and required at both
publish/deploy and worker resolution. Without it, publish fails closed for
off-list deps and workers refuse to register native-tier manifest pures they
have not granted. A native-tier runtime ref carries no `envHash`; the worker
builds the venv from the declared deps. See [SPEC §6.5](/docs/internals/specification#65-pureruntimerefs--published-runtime-identity)
and [§6.6](/docs/internals/specification#66-bundle-manifest--detached-signature).

## Worker requirements

- Install the `wasm` extra so `wasmtime` is importable in the worker image:
  `pip install --pre 'julep[wasm]'` (wasmtime `>=45,<46`). Without it,
  resolving a bundle pure fails fast **at resolution** (worker init / fresh
  activation) with a `BundleResolutionError` carrying install guidance — before
  any work is accepted — not later with a raw `ModuleNotFoundError` at the first
  pure lookup inside workflow code.
- The vendored portable component ships at
  `julep/execution/_wasm/executor.wasm` (committed). A compiled
  module cache (`.cwasm`) is built lazily at runtime (~0.9s one-time) into
  `JULEP_WASM_CACHE_DIR` (default: the OS temp dir) and is **not** committed
  (it is wasmtime-version/platform specific). Mounting a writable, node-local
  cache dir avoids paying the one-time compile on every pod start.
- On the Temporal path the worker passes `wasmtime` through the workflow sandbox
  (`SandboxedWorkflowRunner.with_passthrough_modules("julep",
  "wasmtime")`) so the workflow-side wasm call shares the process-global engine
  and compiled component instead of re-importing wasmtime inside the sandbox.

### Tunables (env)

| Variable | Default | Effect |
| --- | --- | --- |
| `JULEP_WASM_FUEL` | `2_000_000_000` | Fuel ceiling per call; bounds runaway compute. **Deterministic, always-on primary bound.** |
| `JULEP_WASM_EPOCH_MS` | unset (off) | If set (>0), enables a best-effort epoch ticker + one-tick wall-clock deadline per call. **Opt-in, non-deterministic, coarse operational backstop only.** |
| `JULEP_WASM_CACHE_DIR` | OS temp dir | Where the compiled `.cwasm` cache is written. |

A pure that exceeds fuel (or the epoch deadline, if enabled) traps; the host
surfaces it as a `PureExecutionError` so flow error semantics match a native
raise. Clock/filesystem/network access inside the pure traps the same way.

#### Fuel vs epoch — the determinism contract (read before enabling epoch)

The wasm tier runs pures **synchronously inside the deterministic interpreter**
(on the Temporal path, inside replayed workflow code). The bound that stops a
pure MUST therefore be deterministic, or two workers (or a worker and its replay)
could disagree on whether a pure succeeded and desync history.

- **Fuel is the deterministic, always-on, primary bound.** Fuel is consumed per
  wasm instruction, independent of wall-clock time or host load, so a given pure
  on a given input consumes the same fuel everywhere and traps (or not)
  identically across workers and across replay. Fuel is enabled unconditionally.
- **Epoch is an opt-in, non-deterministic, coarse backstop — never the
  determinism mechanism.** Epoch interruption fires off a wall-clock ticker
  thread, so whether a pure exceeds the deadline depends on host speed and load
  and can differ across workers/replay. It exists only as an operational
  safety net for the pathological case (e.g. a pure that somehow burns
  wall-clock without burning fuel). It is **off by default**, and you should keep
  it off on durable/replayable paths; rely on fuel for the real bound and only
  enable epoch as a last-resort operational guard where occasional
  non-deterministic divergence is acceptable.

The process-global wasm executor (engine + compiled component, plus the epoch
ticker thread when enabled) is **eagerly initialized at bundle resolution time**
(worker init / fresh activation, in the worker thread before sandboxed workflow
code runs), not lazily on the first pure lookup inside workflow code. This keeps
the one-time component load / `.cwasm` cache IO — and any epoch thread spawn —
out of the Temporal workflow sandbox. A worker missing the `wasm` extra (or the
vendored `executor.wasm`) therefore fails **fast at resolution** with a
`BundleResolutionError` carrying install guidance, instead of a raw
`ModuleNotFoundError` at the first pure lookup mid-workflow.

### Failure taxonomy (operator-actionable)

A bundle pure failure surfaces as a `PureExecutionError` whose `error_type` is a
stable, greppable tag. The two classes are distinct on purpose:

| `error_type` | Cause | Operator action |
| --- | --- | --- |
| _the real Python type_ (e.g. `ValueError`, `KeyError`) | The pure raised in-sandbox (a normal application error). | Fix the pure / its input — same as a native pure raising. |
| `WasmSandboxTrap` | The pure reached for a host capability (clock, filesystem, network, entropy, env). The `--stub-wasi` build has no WASI, so the syscall traps. | The pure is not actually pure. Remove the capability use; bundle pures must be deterministic compute only. |
| `WasmFuelExhausted` | The pure burned through `JULEP_WASM_FUEL` (runaway compute). | Fix the runaway loop, or raise `JULEP_WASM_FUEL` if the budget is genuinely too low. |
| `WasmDeadlineExceeded` | The pure exceeded the `JULEP_WASM_EPOCH_MS` wall-clock deadline (only when epoch interruption is enabled). | As above: fix the long-running pure or raise the deadline. |
| `WasmHostError` | A host-boundary failure that is not a trap (e.g. malformed component response). | Usually a toolchain/version mismatch — check the `wasm` extra and the vendored component. |

The message names the offending pure and (for traps) points back at this runbook;
the `traceback_tail` carries the classification plus the raw `wasm trap: ...` line
for diagnosis, without dumping the full multi-line wasm backtrace. These are the
adversarial failures the local probe suite (`tests/test_wasm_sandbox.py`) pins as
failing closed with a structured diagnostic rather than a bare `WasmtimeError`.

## Trust model & signing

Bundle resolution is **fail-closed**. The former P2 dev-only
`JULEP_BUNDLE_NATIVE_EXEC` escape hatch is gone. Bundle pures default to the wasm
sandbox; the only native bundle path is the per-pure `JULEP_PURE_NATIVE_DEPS`
capability described above.

Signatures are ed25519 DETACHED signatures. `bundleHash` is sha256 over the
unsigned canonical manifest bytes, so bundle identity does not depend on who
signed it. The stored manifest's `signature` field is always `null`; the
detached signature object is stored and verified separately, consistent with
[SPEC §6.6](/docs/internals/specification#66-bundle-manifest--detached-signature).

Resolution verifies, in order, and refuses to register anything on any failure:

1. **Signer allowlist.** The bundle's detached ed25519 signature must carry a
   `publicKey` present in `JULEP_BUNDLE_ALLOWED_SIGNERS` (comma-separated hex keys).
2. **Signature.** The signature must verify against the manifest bytes, and its
   `bundleHash` must equal the requested bundle hash.
3. **Content addressing.** Every CAS read is integrity-checked against its hash
   (manifest, each source blob), and `artifactHash == sha256:artifactComponents`.
4. **Per-pure source hash.** Each pure's shipped source must hash to the
   `sourceHash` pinned in the manifest.
5. **No `std.*` shadowing.** A bundle must not ship a `std.*` pure (those stay
   baked); attempting to do so fails closed.
6. **No baked-vs-bundle drift.** If a pure is already baked in the worker with a
   different source hash, resolution refuses with operator guidance (stale image
   vs stale bundle).

Unsigned bundles and signatures from unknown public keys fail closed.

### Signing tiers (recommended)

- **Development**: a throwaway ed25519 seed kept out of the repo; the k3d demo
  uses a fixed `DEMO_SEED` purely for reproducibility — never a secret.
- **Staging/production**: an offline or HSM/KMS-held signing key. Publish bundles
  through a signing step that never exposes the private key to the worker. Workers
  only ever hold **public** keys (`JULEP_BUNDLE_ALLOWED_SIGNERS`).
- **Key rotation**: add the new public key to the allowlist, republish bundles
  signed with the new key, then remove the old key once no live workers pin
  bundles signed by it. The allowlist supports multiple keys for this overlap.

## CAS retention

Bundles are content-addressed and immutable. CAS exposes no public delete API:
a `bundleHash` plus optional signature digest is a stable, replay-safe pointer.
Garbage collection is the narrow private mark-sweep exception, implemented for
local stores in `julep/gc.py` (P5-S1, shipped commit `ed6ffb1`).

**Do not garbage-collect** a bundle while any worker may resolve it. On the
Temporal path a worker re-resolves the bundle from `FlowInput.bundle` on every
fresh activation, including replay on a new worker, so the blobs must outlive
every in-flight and replayable run. Retain at least all bundles referenced by
currently deployed artifacts, plus any bundle still reachable by an in-flight or
recently completed workflow that could replay. A safe default is to retain by
deployment lineage and expire only bundles no deployment references.

### Lease-backed GC

Leases encode the retention rule for local CAS stores. A `Lease` records
`bundle_hash`, optional `signature_digest`, and optional `name`, and persists
under `<cas_root>/leases/` outside the sharded blob tree. The reachable set is
the closure over each leased bundle manifest:

| Manifest field | Retained object |
| --- | --- |
| lease `bundle_hash` | manifest blob |
| lease `signature_digest` | detached signature object |
| `artifactComponents` | canonical artifact envelope |
| `flow` | canonical `flowJson` |
| each pure `source` | shipped pure source blob |
| each pure `envComponent` | pre-initialized wasm env component, when present |

`gc(store, lease_store, dry_run=...)` enumerates every CAS object, subtracts the
union of all lease closures, and reports the remainder as collectable.
`dry_run` defaults to `True`: it reports `reachable` and `collectable` and
deletes nothing. Pass `dry_run=False` to delete collectable objects.

GC fails closed. A single incomputable lease closure, such as an unreadable or
malformed manifest or a missing blob, raises `GCError` and aborts the whole
sweep before any deletion. A partial root set is never used to decide
deletions.

Only `LocalDirCAS` is enumerable and collectable today. `S3CAS` GC raises
`GCError`; paginated list/delete is deferred. On S3-backed CAS, keep applying
the retention rule manually: retain anything a live or replayable run may
resolve. Lease GC is the automated local-store optimization of that rule.

## Live EKS acceptance (manual)

The local gates exercise the full bundle→wasm path end to end (Temporal
time-skipping server, DBOS env, CMA env, and a real signed bundle). The **live
EKS acceptance run** — a real cluster, S3-backed CAS (`STORE_URL=s3://...`), KEDA
scale-from-zero, and a worker image built with the `wasm` extra — requires
cluster/S3/credentials not available in CI and remains a **manual ops step**:

1. Build and push the worker image with `julep[wasm]`.
2. Publish the signed bundle to the S3 CAS; record `JULEP_BUNDLES` and the signer
   public key.
3. Set `STORE_URL`, `JULEP_BUNDLES`, `JULEP_BUNDLE_ALLOWED_SIGNERS` on the worker
   Deployment (see `tooling/sandbox-k8s/worker.yaml`).
4. Drive the grade-scores flow and assert the wasm-tier result matches the local
   baked (native) dry-run value (parity).

<!-- ported-by julep-docs-site: deploy/wasm-tier -->
