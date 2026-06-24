from __future__ import annotations

import os

from composable_agents.execution.langfuse import trace_id_for


def trace_url(run_id: str) -> str | None:
    """Build a Langfuse trace deep-link for a run when Langfuse is configured."""
    host = os.environ.get("LANGFUSE_HOST")
    if not host:
        return None

    host = host.rstrip("/")
    hexid = format(trace_id_for(run_id), "032x")
    project = os.environ.get("LANGFUSE_PROJECT_ID")

    if project:
        return f"{host}/project/{project}/traces/{hexid}"
    return f"{host}/api/public/traces/{hexid}"
