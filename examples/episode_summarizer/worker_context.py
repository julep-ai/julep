"""Worker context for the live episode-summarizer example."""

from __future__ import annotations

import importlib
import os

from julep.execution.bundle_worker import make_context as base_make_context
from julep.execution.effects import WorkerContext
from julep.execution.llm import make_llm_caller
from julep.mcp_auth import McpAuthConfig, http_mcp_caller


def make_context() -> WorkerContext:
    """Load the published bundle and attach live MCP and LLM transports."""
    ctx = base_make_context()
    if not os.environ.get("JULEP_BUNDLES", "").strip():
        # A bundle preload already registered the pures, and the workflow's
        # runtime-declarations blob hydrates its reasoners from STORE_URL.
        importlib.import_module("examples.episode_summarizer.flow")
    url = os.environ["EPISODE_TOOLS_URL"]
    ctx.mcp_call = http_mcp_caller(
        servers={"episodes": url},
        auth=McpAuthConfig.from_env(),
    )
    ctx.llm = make_llm_caller()
    return ctx
