"""Start the weather agent on Temporal; the k3d pod worker runs the loop.

Run from the repo root with the demo dir on PYTHONPATH:

    PYTHONPATH=tooling/k3d-llm-demo .venv/bin/python tooling/k3d-llm-demo/drive_llm.py
"""

from __future__ import annotations

import asyncio
import json
import time

from temporalio.client import Client

from llm_weather_agent import AGENT, QUESTION


async def main() -> None:
    client = await Client.connect("localhost:7233")
    session_id = f"k3d-llm-demo-{int(time.time())}"
    print(f"starting {session_id!r}: {QUESTION}")
    result = await AGENT.deploy(client, session_id=session_id, input=QUESTION)
    print("\n=== durable run result (worker: k3d pod, reasoner: real Anthropic) ===")
    print("status:", result["status"], "| cost:", result.get("cost"))
    print("output:", json.dumps(result["output"]))
    print("trace:")
    for entry in result["trace"]:
        print(f"  - {entry['decision']} {entry.get('ref', '')} (${entry['cost']})")


if __name__ == "__main__":
    asyncio.run(main())
