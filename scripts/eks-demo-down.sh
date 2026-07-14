#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT_DIR/infra/terraform/envs/demo"

# shellcheck source=eks-demo-network.sh
. "$ROOT_DIR/scripts/eks-demo-network.sh"

terraform -chdir="$TF_DIR" init
resolve_eks_demo_network "$TF_DIR"

# Delete the Temporal UI Ingress first so EKS Auto Mode deprovisions the ALB
# before Terraform tears down the VPC and security groups.
AWS_REGION="$(terraform -chdir="$TF_DIR" output -raw aws_region 2>/dev/null || true)"
CLUSTER_NAME="$(terraform -chdir="$TF_DIR" output -raw cluster_name 2>/dev/null || true)"
if [[ -n "$CLUSTER_NAME" ]]; then
  aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME" >/dev/null 2>&1 || true
  kubectl -n temporal delete ingress temporal-web --ignore-not-found --wait=true 2>/dev/null || true
fi

terraform -chdir="$TF_DIR" destroy -auto-approve \
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
