"""Submit the grade-scores flow on Temporal; the generic k3d pod runs it.

Run from the repo root after up.sh reports the worker ready::

    uv run python tooling/k3d-cad-demo/drive.py

The driver holds the flow code (it is the author/operator); it ships flowJson +
pinned pure hashes as workflow input. The worker has never imported this flow —
it materialised the three custom pures from the signed CAS bundle at startup.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from temporalio.client import Client  # noqa: E402

from examples.grade_scores_flow import SCORES, build  # noqa: E402


async def main() -> None:
    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    client = await Client.connect(address)
    deployment = build()
    session_id = f"cad-demo-{int(time.time())}"
    print(f"submitting {session_id!r} on {address}: {len(SCORES)} records")

    result = await deployment.run(
        client,
        session_id=session_id,
        input=SCORES,
        task_queue="ca-cad-demo",
    )

    print("\n=== durable flow result (worker: generic k3d pod, pures: from bundle) ===")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
