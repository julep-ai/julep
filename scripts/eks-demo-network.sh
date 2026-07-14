#!/usr/bin/env bash

# Resolve the explicit Terraform network inputs used by the disposable demo.
# Production callers pass vpc_id/private_subnet_ids directly and never enable
# allow_public_subnets_for_demo. The wrappers intentionally preserve the old
# workstation demo by discovering the default VPC only when neither environment
# overrides nor existing Terraform outputs provide a network.
resolve_eks_demo_network() {
  local tf_dir="$1"
  local state_value=""

  DEMO_AWS_REGION="${DEMO_AWS_REGION:-${AWS_REGION:-}}"
  if [[ -z "$DEMO_AWS_REGION" ]]; then
    state_value="$(terraform -chdir="$tf_dir" output -raw aws_region 2>/dev/null || true)"
    DEMO_AWS_REGION="${state_value:-us-east-1}"
  fi

  if [[ -z "${DEMO_VPC_ID:-}" ]]; then
    state_value="$(terraform -chdir="$tf_dir" output -raw vpc_id 2>/dev/null || true)"
    DEMO_VPC_ID="$state_value"
  fi
  if [[ -z "$DEMO_VPC_ID" ]]; then
    DEMO_VPC_ID="$(
      aws ec2 describe-vpcs \
        --region "$DEMO_AWS_REGION" \
        --filters Name=is-default,Values=true \
        --query 'Vpcs[0].VpcId' \
        --output text
    )"
  fi
  if [[ -z "$DEMO_VPC_ID" || "$DEMO_VPC_ID" == "None" ]]; then
    echo "no default VPC found; set DEMO_VPC_ID and DEMO_SUBNET_IDS_JSON" >&2
    return 1
  fi

  if [[ -z "${DEMO_SUBNET_IDS_JSON:-}" ]]; then
    state_value="$(terraform -chdir="$tf_dir" output -json private_subnet_ids 2>/dev/null || true)"
    DEMO_SUBNET_IDS_JSON="$state_value"
  fi
  if [[ -z "$DEMO_SUBNET_IDS_JSON" ]]; then
    local subnet_inventory
    subnet_inventory="$(
      aws ec2 describe-subnets \
        --region "$DEMO_AWS_REGION" \
        --filters "Name=vpc-id,Values=$DEMO_VPC_ID" Name=state,Values=available \
        --query 'Subnets[].{id:SubnetId,az:AvailabilityZone}' \
        --output json
    )"
    DEMO_SUBNET_IDS_JSON="$(
      python3 - "$subnet_inventory" "${DEMO_EXCLUDED_AZS:-us-east-1e}" <<'PY'
import json
import sys

rows = json.loads(sys.argv[1])
excluded = {item.strip() for item in sys.argv[2].split(",") if item.strip()}
selected = sorted(
    (row for row in rows if row.get("az") not in excluded),
    key=lambda row: (row.get("az", ""), row.get("id", "")),
)
ids = [row["id"] for row in selected]
zones = {row["az"] for row in selected}
if len(ids) < 2 or len(zones) < 2:
    raise SystemExit(
        "the disposable demo needs at least two default-VPC subnets in distinct "
        "Availability Zones; set DEMO_SUBNET_IDS_JSON explicitly"
    )
print(json.dumps(ids, separators=(",", ":")))
PY
    )"
  fi

  DEMO_SUBNET_IDS_JSON="$(
    python3 - "$DEMO_SUBNET_IDS_JSON" <<'PY'
import json
import sys

value = json.loads(sys.argv[1])
if (
    not isinstance(value, list)
    or len(value) < 2
    or len(set(value)) != len(value)
    or not all(isinstance(item, str) and item.startswith("subnet-") for item in value)
):
    raise SystemExit("DEMO_SUBNET_IDS_JSON must be a JSON list of at least two distinct subnet IDs")
print(json.dumps(sorted(value), separators=(",", ":")))
PY
  )"
}
