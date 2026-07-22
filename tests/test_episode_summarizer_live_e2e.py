"""Live full-stack coverage for the episode-summarizer example."""

from __future__ import annotations

import asyncio
import os
import shutil

import pytest

from examples.episode_summarizer.harness import (
    HarnessUnavailable,
    LIVE_ONE_LINER_MODEL,
    docker_usable,
    run_live_e2e,
)
from examples.episode_summarizer.tools_server import EPISODE_IDS, MISSING_EPISODE_ID


@pytest.mark.live
@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY is required",
)
@pytest.mark.skipif(shutil.which("temporal") is None, reason="temporal CLI is required")
def test_episode_summarizer_live_e2e(monkeypatch: pytest.MonkeyPatch) -> None:
    if not os.environ.get("EPISODE_E2E_PG_DSN") and not docker_usable():
        pytest.skip("set EPISODE_E2E_PG_DSN or start docker")

    # Keep the OpenAI model as the sample's code default, but use the working
    # Anthropic credential for this deliberately live test.
    monkeypatch.setenv("EPISODE_ONE_LINER_MODEL", LIVE_ONE_LINER_MODEL)
    try:
        result = asyncio.run(run_live_e2e(one_liner_model=LIVE_ONE_LINER_MODEL))
    except HarnessUnavailable as exc:
        pytest.skip(str(exc))

    assert result.sse_event_count >= 1
    assert result.terminal_seen is True
    assert set(result.summaries) == set(EPISODE_IDS)
    assert set(result.one_liners) == set(EPISODE_IDS)
    assert all(result.summaries.values())
    assert all(result.one_liners.values())
    assert result.result_value["counts"] == {
        "not_found": 1,
        "written": len(EPISODE_IDS),
    }
    missing = next(
        item for item in result.result_value["results"] if item["episodeId"] == MISSING_EPISODE_ID
    )
    assert missing["summaryStatus"] == "not_found"
    assert missing["oneLinerStatus"] == "not_found"


def test_episode_summarizer_hand_authored_snapshot_uses_names_preflight() -> None:
    # Keep this import inside the test: the live test above must set model
    # overrides before importing the flow module.
    from examples.episode_summarizer import flow
    from examples.episode_summarizer.tools_server import MCP_SERVER, _build_mcp
    from julep import compare_mcp_surface, snapshot_from_listings

    compiled = flow.build_compiled_application()
    advertised = asyncio.run(_build_mcp().list_tools())
    fresh = snapshot_from_listings(
        {
            MCP_SERVER: {
                tool.name: {
                    "inputSchema": tool.inputSchema,
                    "outputSchema": tool.outputSchema,
                    "annotations": (
                        tool.annotations.model_dump(exclude_none=True)
                        if tool.annotations is not None
                        else {}
                    ),
                }
                for tool in advertised
            }
        }
    )
    frozen = compiled.pipelines[0].deployment.manifest

    assert compiled.mcp_preflight_policy == "names"
    assert compiled.artifact_components["mcpPreflight"] == "names"
    assert compare_mcp_surface(frozen, fresh, policy="names") == ()
    assert compare_mcp_surface(frozen, fresh, policy="pin")
