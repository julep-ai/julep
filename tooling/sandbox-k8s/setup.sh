#!/usr/bin/env bash
# Stand up k3s + KEDA + Temporal in a Claude Code sandbox VM and deploy the
# demo worker, end to end. See README.md for what each workaround is for.
#
# Tested sequence (2026-06): k3s 1.33 with --docker, KEDA 2.20 (temporal
# scaler, >= 2.17), Temporal CLI dev server. Sandbox-only: this edits
# /etc/docker/daemon.json and assumes a disposable root VM.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

[ "$(id -u)" = 0 ] || { echo "run as root (sandbox VM)"; exit 1; }

# --- 1. Docker daemon with the oom_score_adj-stripping runc wrapper -------- #
install -m 0755 "$HERE/runc-noadj" /usr/local/bin/runc-noadj
if ! grep -q runc-noadj /etc/docker/daemon.json 2>/dev/null; then
  mkdir -p /etc/docker
  [ -f /etc/docker/daemon.json ] && cp /etc/docker/daemon.json /etc/docker/daemon.json.bak
  cat > /etc/docker/daemon.json <<'EOF'
{
  "runtimes": {"runc-noadj": {"path": "/usr/local/bin/runc-noadj"}},
  "default-runtime": "runc-noadj"
}
EOF
  pkill dockerd 2>/dev/null || true; sleep 3
fi
if ! docker info >/dev/null 2>&1; then
  dockerd >/tmp/dockerd.log 2>&1 &
  sleep 5
fi
docker info 2>/dev/null | grep -q "Default Runtime: runc-noadj" \
  || { echo "dockerd is not using runc-noadj"; exit 1; }

# --- 2. Binaries (direct release downloads; no curl|bash) ------------------- #
[ -x /usr/local/bin/kubectl ] || { curl -fsSL -o /usr/local/bin/kubectl \
  "https://dl.k8s.io/release/v1.33.1/bin/linux/amd64/kubectl"; chmod +x /usr/local/bin/kubectl; }
[ -x /usr/local/bin/k3s ] || { curl -fsSL -o /usr/local/bin/k3s \
  "https://github.com/k3s-io/k3s/releases/download/v1.33.1%2Bk3s1/k3s"; chmod +x /usr/local/bin/k3s; }
[ -x /usr/local/bin/helm ] || { curl -fsSL \
  https://get.helm.sh/helm-v3.17.3-linux-amd64.tar.gz | tar xz -C /tmp \
  && mv /tmp/linux-amd64/helm /usr/local/bin/; }
[ -x /usr/local/bin/temporal ] || { curl -fsSL -o /tmp/temporal.tar.gz \
  "https://temporal.download/cli/archive/latest?platform=linux&arch=amd64" \
  && tar -C /usr/local/bin -xzf /tmp/temporal.tar.gz temporal; }

# --- 3. Temporal dev server on the host (pods reach it at 10.42.0.1) ------- #
if ! temporal operator namespace list --address localhost:7233 >/dev/null 2>&1; then
  temporal server start-dev --ip 0.0.0.0 --port 7233 --headless >/tmp/temporal-dev.log 2>&1 &
  sleep 6
fi

# --- 4. k3s with dockerd as the runtime (nested runc does not work here) --- #
if ! pgrep -f "k3s serve[r]" >/dev/null; then
  k3s server --docker --disable traefik --disable metrics-server \
    --write-kubeconfig-mode 644 >/tmp/k3s.log 2>&1 &
fi
until kubectl get nodes 2>/dev/null | grep -q " Ready"; do sleep 3; done
kubectl wait --for=condition=ready pod --all -n kube-system --timeout=300s

# --- 5. KEDA (temporal scaler needs >= 2.17) -------------------------------- #
if ! helm status keda -n keda >/dev/null 2>&1; then
  helm repo add kedacore https://kedacore.github.io/charts >/dev/null
  helm repo update >/dev/null
  helm install keda kedacore/keda --namespace keda --create-namespace --wait --timeout 6m
fi

# --- 6. Demo worker image from the local checkout --------------------------- #
BUILD=/tmp/ca-sandbox-k8s-build
rm -rf "$BUILD" && mkdir -p "$BUILD"
git -C "$REPO_ROOT" archive HEAD --prefix=julep-v2/ | tar -x -C "$BUILD"
cp "$HERE/Dockerfile" "$HERE/demo_worker.py" "$BUILD/"
cp /etc/ssl/certs/ca-certificates.crt "$BUILD/ca-bundle.crt"
docker build -t ca-worker:demo "$BUILD"

# --- 7. Deploy + scaler ------------------------------------------------------ #
kubectl apply -f "$HERE/worker.yaml"
kubectl get scaledobject ca-worker

cat <<'EOF'

Ready. Drive a burst and watch KEDA scale 0 -> N -> 0:

  export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
  kubectl get deploy ca-worker -w &
  python3 tooling/sandbox-k8s/drive.py 12
EOF
