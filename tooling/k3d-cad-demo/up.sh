#!/usr/bin/env bash
# Bring up the code-as-data demo on k3d, end to end:
#   1. Temporal dev server on the host (pods reach it at host.k3d.internal:7233)
#   2. k3d cluster with the host CAS dir bind-mounted at /cas
#   3. a GENERIC worker image (no flow code) built once and imported
#   4. publish the grade-scores bundle into the shared CAS dir
#   5. deploy the generic worker pointed at that bundle; wait until ready
# Then run drive.py to submit the flow. Zero docker in the per-flow loop: the
# image is never rebuilt to ship the flow — the flow arrives as a signed bundle.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"

CLUSTER="${CLUSTER:-julep-cad-demo}"
CAS_DIR="${CAS_DIR:-/tmp/julep-cad-cas}"
IMAGE="${IMAGE:-julep-worker:cad-demo}"
ENV_OUT="${ENV_OUT:-/tmp/julep-cad-env.json}"

K3D="${K3D:-$(command -v k3d 2>/dev/null || true)}"
if [ -z "$K3D" ] || ! "$K3D" version >/dev/null 2>&1; then
  K3D="$(ls -d "$HOME"/.local/share/mise/installs/k3d/*/k3d 2>/dev/null | sort -V | tail -1)"
fi
[ -n "$K3D" ] && "$K3D" version >/dev/null 2>&1 || { echo "k3d not found"; exit 1; }
echo "k3d: $K3D"

# --- 1. Temporal dev server on the host ------------------------------------ #
if ! temporal operator namespace list --address localhost:7233 >/dev/null 2>&1; then
  echo "starting temporal dev server (0.0.0.0:7233) ..."
  nohup temporal server start-dev --ip 0.0.0.0 --port 7233 --headless \
    >/tmp/julep-cad-temporal.log 2>&1 &
  for _ in $(seq 1 30); do
    temporal operator namespace list --address localhost:7233 >/dev/null 2>&1 && break
    sleep 1
  done
fi
temporal operator namespace list --address localhost:7233 >/dev/null 2>&1 \
  && echo "temporal: reachable on localhost:7233" || { echo "temporal not reachable"; exit 1; }

# --- 2. k3d cluster with the CAS dir bind-mounted at /cas ------------------- #
mkdir -p "$CAS_DIR"
if ! "$K3D" cluster list "$CLUSTER" >/dev/null 2>&1; then
  echo "creating k3d cluster $CLUSTER (volume $CAS_DIR -> /cas) ..."
  "$K3D" cluster create "$CLUSTER" --volume "$CAS_DIR:/cas@all" --wait
fi
export KUBECONFIG="$("$K3D" kubeconfig write "$CLUSTER")"
kubectl config use-context "k3d-$CLUSTER" >/dev/null
kubectl wait --for=condition=ready node --all --timeout=120s

# --- 3. Generic worker image (built once; never rebuilt per flow) ---------- #
BUILD=/tmp/julep-cad-build
rm -rf "$BUILD" && mkdir -p "$BUILD"
git -C "$REPO_ROOT" archive HEAD --prefix=julep-v2/ | tar -x -C "$BUILD"
cp "$REPO_ROOT/tooling/runtime-image/Dockerfile" "$BUILD/"
echo "building $IMAGE ..."
docker build -t "$IMAGE" "$BUILD" >/tmp/julep-cad-build.log 2>&1 \
  || { echo "image build failed; see /tmp/julep-cad-build.log"; tail -20 /tmp/julep-cad-build.log; exit 1; }
"$K3D" image import "$IMAGE" -c "$CLUSTER"

# --- 4. Publish the bundle into the shared CAS dir ------------------------- #
echo "publishing grade-scores bundle into $CAS_DIR ..."
CAS_DIR="$CAS_DIR" ENV_OUT="$ENV_OUT" uv --project "$REPO_ROOT" run python "$HERE/publish.py"
JULEP_BUNDLES="$(python3 -c "import json;print(json.load(open('$ENV_OUT'))['JULEP_BUNDLES'])")"
SIGNER="$(python3 -c "import json;print(json.load(open('$ENV_OUT'))['JULEP_BUNDLE_ALLOWED_SIGNERS'])")"

# --- 5. Deploy the generic worker pointed at the bundle -------------------- #
RENDERED=/tmp/julep-cad-worker.yaml
sed -e "s|__JULEP_BUNDLES__|$JULEP_BUNDLES|" -e "s|__SIGNER__|$SIGNER|" "$HERE/worker.yaml" > "$RENDERED"
kubectl apply -f "$RENDERED"
echo "waiting for worker rollout ..."
kubectl rollout status deploy/julep-cad-worker --timeout=120s

cat <<EOF

Ready. The generic worker resolved the bundle at startup. Now submit the flow:

  TEMPORAL_ADDRESS=localhost:7233 uv run python $HERE/drive.py

Worker logs:   KUBECONFIG=$KUBECONFIG kubectl logs deploy/julep-cad-worker
Bundle env:    $ENV_OUT
EOF
