#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT_DIR/infra/terraform/envs/demo"

terraform -chdir="$TF_DIR" init
terraform -chdir="$TF_DIR" destroy -auto-approve "$@"
