#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT_DIR/infra/terraform/envs/demo"
LOCAL_PORT="${LOCAL_PORT:-17233}"

if [[ ! -f "$ROOT_DIR/.env" ]]; then
  echo "missing $ROOT_DIR/.env" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
. "$ROOT_DIR/.env"
set +a

if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "ANTHROPIC_API_KEY is missing from .env" >&2
  exit 1
fi

AWS_REGION="$(terraform -chdir="$TF_DIR" output -raw aws_region)"
CLUSTER_NAME="$(terraform -chdir="$TF_DIR" output -raw cluster_name)"
aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME" --alias "$CLUSTER_NAME" >/dev/null

kubectl -n julep-demo create secret generic llm-keys \
  --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -

export TEMPORAL_PAYLOAD_KEYS="$(kubectl -n julep-demo get secret temporal-payload-codec \
  -o jsonpath='{.data.keyring}' | base64 --decode)"
export TEMPORAL_PAYLOAD_KEY_ID="$(kubectl -n julep-demo get secret temporal-payload-codec \
  -o jsonpath='{.data.active-key-id}' | base64 --decode)"

kubectl -n temporal rollout status deploy/temporal-frontend --timeout=5m
kubectl -n temporal port-forward svc/temporal-frontend "$LOCAL_PORT:7233" >/tmp/julep-v2-temporal-port-forward.log 2>&1 &
PF_PID=$!
trap 'kill "$PF_PID" >/dev/null 2>&1 || true' EXIT

for _ in {1..30}; do
  if python3 - <<PY >/dev/null 2>&1
import socket
s = socket.create_connection(("127.0.0.1", $LOCAL_PORT), timeout=1)
s.close()
PY
  then
    break
  fi
  sleep 1
done

PYTHON="${PYTHON:-$ROOT_DIR/.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON=python3
fi

PYTHONPATH="$ROOT_DIR/tooling/k3d-llm-demo" "$PYTHON" - <<PY
from __future__ import annotations

import asyncio
import json
import time

from temporalio.client import Client
from julep.execution.codec import parse_aes_gcm_keyring
from julep.execution.worker import encrypted_payload_converter
from llm_weather_agent import AGENT, QUESTION
import os


async def main() -> None:
    converter = encrypted_payload_converter(
        parse_aes_gcm_keyring(os.environ["TEMPORAL_PAYLOAD_KEYS"]),
        active_key_id=os.environ["TEMPORAL_PAYLOAD_KEY_ID"],
    )
    client = await Client.connect("127.0.0.1:$LOCAL_PORT", data_converter=converter)
    session_id = f"eks-rds-llm-demo-{int(time.time())}"
    print(f"starting {session_id!r}: {QUESTION}", flush=True)
    result = await AGENT.deploy(client, session_id=session_id, input=QUESTION)
    print()
    print("=== durable run result (worker: EKS pod, reasoner: real Anthropic, Temporal: RDS PostgreSQL) ===")
    print("status:", result["status"], "| cost:", result.get("cost"))
    print("output:", json.dumps(result["output"]))
    print("trace:")
    for entry in result["trace"]:
        print(f"  - {entry['decision']} {entry.get('ref', '')} (\${entry['cost']})")


asyncio.run(main())
PY

echo
kubectl get scaledobject,hpa,deploy,pods -n julep-demo -o wide
