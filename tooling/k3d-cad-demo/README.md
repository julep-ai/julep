# k3d code-as-data demo

Proves the P2 headline: **author a new flow, publish it, run it on k3d — with
zero docker in the per-flow loop.** The worker image is generic and built once;
a new flow ships as a signed artifact-store bundle the worker resolves at startup. No image
rebuild, no redeploy, no flow code on the worker.

The generic runtime image is defined once at `tooling/runtime-image/Dockerfile`;
`up.sh` builds from that canonical Dockerfile.

## What it shows

- `examples/grade_scores_flow.py` is a deterministic batch flow whose entire
  logic is three custom pures (`normalize_record`, `grade_one`, `tally_grades`)
  plus `each` — no reasoners, no tools, no API keys.
- `publish.py` builds the deployment and publishes a **signed** artifact-store bundle
  (manifest + `flowJson` + pure source + detached ed25519 signature) into an artifact-store
  dir the k3d node bind-mounts at `/artifacts`.
- The worker runs the stock `julep worker` with
  `WORKER_CONTEXT_FACTORY=julep.execution.bundle_worker:make_context`.
  At startup it resolves `JULEP_BUNDLES`, verifies the signature against
  `JULEP_BUNDLE_ALLOWED_SIGNERS` (fail-closed), and registers the bundle's pures —
  before accepting any task.
- `drive.py` submits the flow on Temporal. The pod runs it and returns the
  result, byte-identical to the local dry run.

The image holds only the installed framework — `find / -name grade_scores_flow*`
inside the pod returns nothing, and `import grade_scores_flow` fails. The pures
reach the worker's registry solely through the signed bundle.

## Run it

```bash
bash tooling/k3d-cad-demo/up.sh
TEMPORAL_ADDRESS=localhost:7233 uv run python tooling/k3d-cad-demo/drive.py
```

`up.sh` starts a Temporal dev server, creates a k3d cluster with the artifact-store dir
mounted, builds + imports the generic image, publishes the bundle, and rolls out
the worker. Re-running it is idempotent.

## Ship a *different* flow without touching docker

Point `publish.py` at another deployment, re-run publish, patch `JULEP_BUNDLES` +
`JULEP_BUNDLE_ALLOWED_SIGNERS` on the Deployment, and the same image runs the new
flow. The image never changes.

## Autoscaling (optional, KEDA)

`worker-keda.yaml` hands replica control to KEDA's temporal scaler so the generic
worker scales to zero when idle and back up on backlog — each cold start
re-resolves the signed bundle, so autoscaled replicas stay code-as-data. On k3d
the ScaledObject reaches Temporal (Ready) and scale-to-zero works; scale-from-zero
needs a Temporal frontend new enough to expose backlog stats (~1.24+), which the
local dev server (1.22.x) does not — see the header of `worker-keda.yaml`. The
core demo runs on the plain `replicas: 1` Deployment regardless.

## Security model

- Bundles are content-addressed and signed; workers verify every hash (manifest
  artifact-store address, source blobs, per-pure `sourceHash`) and the detached signature,
  and fail closed on unsigned/unknown-signer/tampered bundles.
- Bundle-sourced pures run in the **P3 wasmtime sandbox** (no clock, filesystem,
  or network; fresh instance per call), not natively in-process. Resolution is
  therefore ungated — the old P2 dev-only `JULEP_BUNDLE_NATIVE_EXEC=1` flag is gone.
  The fixed `DEMO_SEED` in `publish.py` is a throwaway demo key, not a secret.
- The wasm executor needs the `wasm` extra (`wasmtime`) installed in the worker
  image; without it, resolving a bundle pure fails fast at lookup time.
- The P4 native dependency tier is opt-in only: uncomment `JULEP_PURE_NATIVE_DEPS`
  in `worker.yaml` to grant named pures access to the uv-managed native venv
  tier for deps with no WASI wheel. Empty or unset remains wasm-only.

See `docs/ops/wasm-tier-runbook.md` for the signing/trust tiers and artifact-store retention
runbook.

## Clean up

```bash
K3D=$(ls -d "$HOME"/.local/share/mise/installs/k3d/*/k3d | sort -V | tail -1)
"$K3D" cluster delete julep-cad-demo
pkill -f "temporal server start-dev" || true
```
