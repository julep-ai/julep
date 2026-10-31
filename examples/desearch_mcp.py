"""Search X with Desearch through a frozen Julep MCP flow.

Install ``pip install -e '.[mcp]'``, set ``DESEARCH_API_KEY``, then run
``python -m examples.desearch_mcp 'durable agent workflows'``.
Discovery is public; the API key is read only when creating the runtime caller
and is never included in the frozen deployment.
See https://desearch.ai/docs/guide/sdk/mcp for the hosted server contract.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any

from julep import Deployment, deploy, flow, mcp_tool
from julep.execution.effects import McpCaller
from julep.mcp_auth import McpTransport

MCP_URL = "https://mcp.desearch.ai/mcp"
search_posts = mcp_tool("desearch", "x-search")


@flow
def search(query: str) -> Any:
    return search_posts(query=query, count=3)


def build() -> Deployment:
    """Discover and freeze schemas without embedding credentials."""
    return deploy(search, mcp_servers={"desearch": MCP_URL})


def caller() -> McpCaller:
    """Bind Bearer auth to the runtime transport only."""
    key = os.environ.get("DESEARCH_API_KEY", "").strip()
    if not key:
        raise ValueError("Set DESEARCH_API_KEY before calling Desearch")
    transport = McpTransport(
        {"desearch": MCP_URL},
        bearer_auth=f"Bearer {key}",
        timeout_s=60,
    )
    return transport.call_tool


def main() -> None:
    mcp_call = caller()
    deployment = build()
    query = " ".join(sys.argv[1:]) or "durable agent workflows"
    result = asyncio.run(deployment.adry_run(query, mcp_call=mcp_call))
    print(json.dumps(result.value, indent=2))


if __name__ == "__main__":
    main()
