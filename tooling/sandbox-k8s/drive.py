"""Start a burst of flows on the composable-agents queue, then await results."""

import asyncio
import sys

from temporalio.client import Client

from composable_agents import call, freeze, manifest_to_json, mcp
from composable_agents.contracts import McpAnnotations
from composable_agents.execution.harness import start_flow
from composable_agents.freeze import McpServerSnapshot, McpSnapshot, McpToolSpec

N = int(sys.argv[1]) if len(sys.argv) > 1 else 12

ann = McpAnnotations(read_only_hint=True, idempotent_hint=True)
SNAPSHOT = McpSnapshot(servers={"srv": McpServerSnapshot(server="srv", version="1", tools={
    "inc": McpToolSpec(input_schema={}, annotations=ann),
})})


async def main() -> None:
    fr = freeze(call(mcp("srv", "inc")), SNAPSHOT)
    flow_json, manifest_json = fr.flow.to_json(), manifest_to_json(fr.manifest)
    client = await Client.connect("localhost:7233")
    handles = []
    for i in range(N):
        handles.append(await start_flow(
            client, flow_json, manifest_json,
            session_id=f"k8s-demo-{i}", input=i, task_queue="composable-agents",
        ))
    print(f"started {N} workflows; awaiting results...", flush=True)
    results = await asyncio.gather(*(h.result() for h in handles))
    print("results:", results, flush=True)
    assert results == [i + 1 for i in range(N)], "wrong results"
    print("all workflows completed correctly", flush=True)


asyncio.run(main())
