# k3d code-as-data demo

Proves the P2 headline: **author a new flow, publish it, run it on k3d — with
zero docker in the per-flow loop.** The worker image is generic and built once;
a new flow ships as a signed CAS bundle the worker resolves at startup. No image
rebuild, no redeploy, no flow code on the worker.

## What it shows

- `examples/grade_scores_flow.py` is a deterministic batch flow whose entire
  logic is three custom pures (`normalize_record`, `grade_one`, `tally_grades`)
  plus `each` — no brains, no tools, no API keys.
- `publish.py` builds the deployment and publishes a **signed** CAS bundle
  (manifest + `flowJson` + pure source + detached ed25519 signature) into a CAS
  dir the k3d node bind-mounts at `/cas`.
- The worker runs the stock `composable-agents worker` with
  `WORKER_CONTEXT_FACTORY=composable_agents.execution.bundle_worker:make_context`.
  At startup it resolves `CA_BUNDLES`, verifies the signature against
  `CA_BUNDLE_ALLOWED_SIGNERS` (fail-closed), and registers the bundle's pures —
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

`up.sh` starts a Temporal dev server, creates a k3d cluster with the CAS dir
mounted, builds + imports the generic image, publishes the bundle, and rolls out
the worker. Re-running it is idempotent.

## Ship a *different* flow without touching docker

Point `publish.py` at another deployment, re-run publish, patch `CA_BUNDLES` +
`CA_BUNDLE_ALLOWED_SIGNERS` on the Deployment, and the same image runs the new
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
  CAS address, source blobs, per-pure `sourceHash`) and the detached signature,
  and fail closed on unsigned/unknown-signer/tampered bundles.
- `CA_BUNDLE_NATIVE_EXEC=1` is required: P2 executes bundle-sourced pures
  natively in-process, which is **dev-gated**. The production path is the P3 wasm
  executor tier. The fixed `DEMO_SEED` in `publish.py` is a throwaway demo key,
  not a secret.

## Clean up

```bash
K3D=$(ls -d "$HOME"/.local/share/mise/installs/k3d/*/k3d | sort -V | tail -1)
"$K3D" cluster delete ca-cad-demo
pkill -f "temporal server start-dev" || true
```
