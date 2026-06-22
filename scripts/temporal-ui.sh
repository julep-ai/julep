#!/usr/bin/env bash
# Open the Temporal web UI on the EKS demo cluster.
#
# Tunnels localhost -> internal ALB -> temporal-web through the SSM bastion.
# Requires AWS creds that can assume the temporal-team role (or that role's own
# creds). Set ASSUME_TEAM_ROLE=1 to assume it automatically.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT_DIR/infra/terraform/envs/demo"
LOCAL_PORT="${LOCAL_PORT:-8233}"

AWS_REGION="$(terraform -chdir="$TF_DIR" output -raw aws_region)"
CLUSTER_NAME="$(terraform -chdir="$TF_DIR" output -raw cluster_name)"
BASTION_ID="$(terraform -chdir="$TF_DIR" output -raw temporal_ui_bastion_instance_id)"
TEAM_ROLE_ARN="$(terraform -chdir="$TF_DIR" output -raw temporal_team_role_arn 2>/dev/null || true)"

if [[ -z "$BASTION_ID" || "$BASTION_ID" == "null" ]]; then
  echo "No bastion provisioned. Set team_principal_arns and re-run scripts/eks-demo-up.sh." >&2
  exit 1
fi

# Optionally assume the shared team role so the session uses its SSM permissions.
if [[ "${ASSUME_TEAM_ROLE:-0}" == "1" && -n "$TEAM_ROLE_ARN" && "$TEAM_ROLE_ARN" != "null" ]]; then
  CREDS_JSON="$(aws sts assume-role --role-arn "$TEAM_ROLE_ARN" \
    --role-session-name "temporal-ui-${USER:-team}")"
  AWS_ACCESS_KEY_ID="$(printf '%s' "$CREDS_JSON" | python3 -c 'import sys,json;print(json.load(sys.stdin)["Credentials"]["AccessKeyId"])')"
  AWS_SECRET_ACCESS_KEY="$(printf '%s' "$CREDS_JSON" | python3 -c 'import sys,json;print(json.load(sys.stdin)["Credentials"]["SecretAccessKey"])')"
  AWS_SESSION_TOKEN="$(printf '%s' "$CREDS_JSON" | python3 -c 'import sys,json;print(json.load(sys.stdin)["Credentials"]["SessionToken"])')"
  export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
fi

aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME" --alias "$CLUSTER_NAME" >/dev/null

ALB_HOST="$(kubectl -n temporal get ingress temporal-web \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || true)"
if [[ -z "$ALB_HOST" ]]; then
  echo "Temporal UI ingress has no ALB hostname yet (still provisioning?)." >&2
  echo "Check: kubectl -n temporal get ingress temporal-web" >&2
  exit 1
fi

echo "Tunneling localhost:${LOCAL_PORT} -> ${ALB_HOST}:80 via bastion ${BASTION_ID}"
echo "Once you see 'Waiting for connections...', open http://localhost:${LOCAL_PORT}"

exec aws ssm start-session \
  --region "$AWS_REGION" \
  --target "$BASTION_ID" \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters "host=${ALB_HOST},portNumber=80,localPortNumber=${LOCAL_PORT}"
