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
