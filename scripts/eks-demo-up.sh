#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT_DIR/infra/terraform/envs/demo"
BUILD_CTX="${TMPDIR:-/tmp}/julep-v2-eks-demo-build"

# shellcheck source=eks-demo-network.sh
. "$ROOT_DIR/scripts/eks-demo-network.sh"

terraform -chdir="$TF_DIR" init
resolve_eks_demo_network "$TF_DIR"
terraform -chdir="$TF_DIR" apply -auto-approve \
  -var=aws_region="$DEMO_AWS_REGION" \
  -var=vpc_id="$DEMO_VPC_ID" \
  -var=private_subnet_ids="$DEMO_SUBNET_IDS_JSON" \
  -var=allow_public_subnets_for_demo=true \
  -var=cluster_endpoint_public_access=true \
  -var=rds_deletion_protection=false \
  -var=rds_skip_final_snapshot=true \
  -var=release_bucket_force_destroy=true \
  -var=deploy_demo_worker=true \
  -var=secrets_recovery_window_days=0 \
  "$@"

AWS_REGION="$(terraform -chdir="$TF_DIR" output -raw aws_region)"
CLUSTER_NAME="$(terraform -chdir="$TF_DIR" output -raw cluster_name)"
IMAGE_URI="$(terraform -chdir="$TF_DIR" output -raw worker_image_uri)"
REGISTRY="${IMAGE_URI%%/*}"

aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME" --alias "$CLUSTER_NAME"

# Expose the Temporal UI via an internal ALB (EKS Auto Mode). Templated from
# terraform outputs because IngressClassParams has no typed Terraform resource.
if [[ "$(terraform -chdir="$TF_DIR" output -raw temporal_ui_enabled)" == "true" ]]; then
  SUBNET_IDS_CSV="$(terraform -chdir="$TF_DIR" output -json private_subnet_ids \
    | python3 -c 'import sys, json; print(", ".join(json.load(sys.stdin)))')"
  VPC_CIDR="$(terraform -chdir="$TF_DIR" output -raw vpc_cidr_block)"
  sed -e "s|__SUBNET_IDS__|${SUBNET_IDS_CSV}|" -e "s|__VPC_CIDR__|${VPC_CIDR}|" \
    "$ROOT_DIR/infra/k8s/temporal-ui-ingress.yaml" | kubectl apply -f -
fi

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$REGISTRY" >/dev/null

rm -rf "$BUILD_CTX"
mkdir -p "$BUILD_CTX/julep-v2"

rsync -a "$ROOT_DIR/pyproject.toml" "$BUILD_CTX/julep-v2/"
rsync -a "$ROOT_DIR/README.md" "$BUILD_CTX/julep-v2/"
rsync -a "$ROOT_DIR/LICENSE" "$BUILD_CTX/julep-v2/"
rsync -a --exclude='__pycache__' "$ROOT_DIR/julep" "$BUILD_CTX/julep-v2/"
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
