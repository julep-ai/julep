#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT_DIR/infra/terraform/envs/demo"
BUILD_CTX="${TMPDIR:-/tmp}/julep-v2-eks-demo-build"

terraform -chdir="$TF_DIR" init
terraform -chdir="$TF_DIR" apply -auto-approve "$@"

AWS_REGION="$(terraform -chdir="$TF_DIR" output -raw aws_region)"
CLUSTER_NAME="$(terraform -chdir="$TF_DIR" output -raw cluster_name)"
IMAGE_URI="$(terraform -chdir="$TF_DIR" output -raw worker_image_uri)"
REGISTRY="${IMAGE_URI%%/*}"

aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME" --alias "$CLUSTER_NAME"
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$REGISTRY" >/dev/null

rm -rf "$BUILD_CTX"
mkdir -p "$BUILD_CTX/julep-v2"

rsync -a "$ROOT_DIR/pyproject.toml" "$BUILD_CTX/julep-v2/"
rsync -a "$ROOT_DIR/README.md" "$BUILD_CTX/julep-v2/"
rsync -a "$ROOT_DIR/LICENSE" "$BUILD_CTX/julep-v2/"
rsync -a --exclude='__pycache__' "$ROOT_DIR/composable_agents" "$BUILD_CTX/julep-v2/"
mkdir -p "$BUILD_CTX/julep-v2/tooling/k3d-llm-demo"
rsync -a "$ROOT_DIR/tooling/k3d-llm-demo/Dockerfile" "$BUILD_CTX/julep-v2/tooling/k3d-llm-demo/"

cp "$ROOT_DIR/tooling/k3d-llm-demo/llm_weather_agent.py" "$BUILD_CTX/llm_weather_agent.py"

if find "$BUILD_CTX" \( -name .env -o -name '*.tfstate' -o -name '.terraform' \) -print -quit | grep -q .; then
  echo "refusing to build: secret-bearing files leaked into Docker build context" >&2
  exit 1
fi

docker build \
  -f "$BUILD_CTX/julep-v2/tooling/k3d-llm-demo/Dockerfile" \
  -t "$IMAGE_URI" \
  "$BUILD_CTX"
docker push "$IMAGE_URI"

kubectl get pods -n temporal
kubectl get scaledobject,hpa,deploy -n julep-demo

echo "EKS demo stack is ready."
echo "Worker image: $IMAGE_URI"
