"""Run the issue-dedup dotctx as a bounded AgentWorkflow-compatible loop.

The example is deliberately keyless: a deterministic controller fake emits the
same native-tool protocol a provider would, and a bare-name tool fake stands in
for the configured tracker MCP server. Replacing those two fakes with a real LLM
caller and ``tracker:search-similar-posts`` transport does not change the dotctx
package.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from julep.deploy import Deployment, deploy
from julep.dotctx import reasoner_to_flow
from julep.dotctx_rich import RichDotctx, load_rich_dotctx
from julep.freeze import McpServerSnapshot, McpSnapshot, McpToolSpec

HERE = os.path.dirname(os.path.abspath(__file__))
DOTCTX_DIR = os.path.join(HERE, "dotctx", "issue_dedup")
ALIAS = "search_similar_posts"
WIRE_TOOL = "tracker/search-similar-posts"


def build() -> tuple[RichDotctx, Deployment]:
    """Freeze the package against the same schema its tools.pyi declares."""
    rich = load_rich_dotctx(DOTCTX_DIR)
    schema = rich.expected_tool_schemas[ALIAS]
    flow = reasoner_to_flow(
        rich.reasoner,
        tool_aliases={ALIAS: WIRE_TOOL},
    )
    snapshot = McpSnapshot(
        servers={
            "tracker": McpServerSnapshot(
                server="tracker",
                tools={"search-similar-posts": McpToolSpec(input_schema=schema)},
            )
        }
    )
    return rich, deploy(flow, snapshot=snapshot, reasoners=[rich.reasoner])


def _controller(payload: dict[str, Any]) -> dict[str, Any]:
    """A two-round provider fake: search first, then emit a valid decision."""
    if not payload["trace"]:
        issue = payload["input"]["issue"]
        return {
            "tool_calls": [
                {
                    "id": "search-1",
                    "tool": ALIAS,
                    "input": {"query": issue},
                }
            ]
        }
    return {
        "output": {
            "action": "create",
            "title": "Login retries fail after token refresh",
            "reason": "The fake tracker returned no similar posts.",
        }
    }


def _search_similar_posts(_args: dict[str, Any]) -> list[dict[str, Any]]:
    return []


async def main() -> dict[str, Any]:
    rich, deployment = build()
    result = await deployment.adry_run(
        {
            "issue": "Login retries fail after token refresh",
            "category": "authentication",
            "thread_id": "demo-1",
        },
        reasoners={rich.reasoner.name: _controller},
        tools={ALIAS: _search_similar_posts},
    )
    terminal = result.value
    print(f"artifact: {deployment.artifact_hash}")
    print(f"status: {terminal['status']}")
    print(f"decision: {terminal['output']}")
    print(f"transcript: {terminal['trace']}")
    return terminal


if __name__ == "__main__":
    asyncio.run(main())
