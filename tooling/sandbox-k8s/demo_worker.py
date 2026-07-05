"""Demo WorkerContext factory for the k3d/KEDA demo.

The MCP caller sleeps to simulate real tool latency so a burst of workflow
starts produces a visible task-queue backlog for KEDA to scale on.
"""

import asyncio

from julep.execution.effects import WorkerContext


async def _mcp(server, tool, value, idempotency_key):
    await asyncio.sleep(1.0)
    if tool == "inc":
        return value + 1
    raise ValueError(f"unknown tool: {tool}")


def make_context() -> WorkerContext:
    return WorkerContext(mcp_call=_mcp)
