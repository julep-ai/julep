"""Start the episode-summary flow on Temporal; a pod worker runs it.

Run from the repo root:

    PYTHONPATH=. .venv/bin/python tooling/k3d-flow-demo/drive_flow.py

TEMPORAL_ADDRESS targets another server (default localhost:7233, the local
dev server the k3d pod polls; point it at a port-forward of the EKS
temporal-frontend to drive the cluster worker instead).
"""

from __future__ import annotations

import asyncio
import json
import os
import time

from temporalio.client import Client

from examples.episode_summary_flow import EPISODE_BATCH, build


async def main() -> None:
    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    client = await Client.connect(address)
    deployment = build()
    session_id = f"flow-demo-{int(time.time())}"
    print(f"starting {session_id!r} on {address}: batch={EPISODE_BATCH}")
    result = await deployment.run(
        client,
        session_id=session_id,
        input=EPISODE_BATCH,
        task_queue="ca-flow-demo",
    )
    print("\n=== durable flow result (worker: pod, brains: real Anthropic) ===")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
