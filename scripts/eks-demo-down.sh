#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT_DIR/infra/terraform/envs/demo"

terraform -chdir="$TF_DIR" init

# Delete the Temporal UI Ingress first so EKS Auto Mode deprovisions the ALB
# before Terraform tears down the VPC and security groups.
AWS_REGION="$(terraform -chdir="$TF_DIR" output -raw aws_region 2>/dev/null || true)"
CLUSTER_NAME="$(terraform -chdir="$TF_DIR" output -raw cluster_name 2>/dev/null || true)"
if [[ -n "$CLUSTER_NAME" ]]; then
  aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME" >/dev/null 2>&1 || true
  kubectl -n temporal delete ingress temporal-web --ignore-not-found --wait=true 2>/dev/null || true
fi

terraform -chdir="$TF_DIR" destroy -auto-approve "$@"
