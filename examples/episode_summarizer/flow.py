"""Episode-summary flow using record binding and frozen MCP tools.

The live application reads episodes through MCP, asks two reasoners for the
summary surfaces, and writes each surface back independently.  The keyless demo
uses the same frozen listing with deterministic fake callers and no network.
"""

from __future__ import annotations

import asyncio
import json
import os
from copy import deepcopy
from typing import Any

from julep import (
    Application,
    Deployment,
    PipelineSpec,
    Reasoner,
    cond,
    deploy,
    each,
    flow,
    mcp_tool,
    pure,
    snapshot_from_listings,
    think,
)
from julep.execution.effects import McpCaller, RunPrincipal

from .tools_server import (
    EPISODE_IDS,
    MISSING_EPISODE_ID,
    TOOL_LISTINGS,
    read_episode as _read_episode,
    reset as _reset_store,
    write_one_liner as _write_one_liner,
    write_summary as _write_summary,
)

SUMMARIZER = os.environ.get("EPISODE_SUMMARIZER_MODEL", "anthropic:claude-sonnet-5")
ONE_LINER = os.environ.get("EPISODE_ONE_LINER_MODEL", "openai:gpt-4o-mini")

MCP_SERVER = "episodes"
PIPELINE_NAME = "episode_summary_batch"
LANE = "summary"


SUMMARIZER_R = Reasoner(
    name="episode_summarizer",
    model=SUMMARIZER,
    system=(
        "Summarize the episode text in 2-4 plain sentences covering the important "
        'events, decisions, and follow-ups. Return {"summary": "..."}.'
    ),
    reply={
        "type": "object",
        "properties": {"summary": {"type": "string"}},
        "required": ["summary"],
    },
    max_tokens=512,
)

ONE_LINER_R = Reasoner(
    name="episode_one_liner",
    model=ONE_LINER,
    system=(
        "Compress the summary into one sentence of at most 140 characters. "
        'Return {"oneLiner": "..."}.'
    ),
    reply={
        "type": "object",
        "properties": {"oneLiner": {"type": "string"}},
        "required": ["oneLiner"],
    },
    max_tokens=128,
)


# These references are frozen against TOOL_LISTINGS at deployment time.
read_episode = mcp_tool(MCP_SERVER, "read-episode")
write_summary = mcp_tool(MCP_SERVER, "write-summary")
write_one_liner = mcp_tool(MCP_SERVER, "write-one-liner")


@pure("episode_found")
def episode_found(source: dict[str, Any]) -> bool:
    return bool(source.get("found"))


@pure("episode_not_found")
def episode_not_found(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "episodeId": source.get("episodeId"),
        "summaryStatus": "not_found",
        "oneLinerStatus": "not_found",
    }


@pure("tally_statuses")
def tally_statuses(results: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for result in results:
        status = str(result["summaryStatus"])
        counts[status] = counts.get(status, 0) + 1
    return {"counts": counts, "results": results}


@flow
def summarize_found(source: dict[str, Any]) -> dict[str, Any]:
    summary = think(SUMMARIZER_R, source)
    context = summary | source
    one_liner = think(ONE_LINER_R, context)
    summary_write = write_summary(
        episode_id=source.episodeId,
        source_hash=source.sourceHash,
        summary=summary.summary,
    )
    one_liner_write = write_one_liner(
        episode_id=source.episodeId,
        source_hash=source.sourceHash,
        one_liner=one_liner.oneLiner,
    )
    return summary_write | one_liner_write


@flow
def summarize_missing(source: dict[str, Any]) -> dict[str, Any]:
    return episode_not_found(source)


@flow
def summarize_one(episode_id: str) -> dict[str, Any]:
    source = read_episode(episode_id=episode_id)
    return cond(episode_found, source, then=summarize_found, orelse=summarize_missing)


@flow
def batch(episode_ids: list[str]) -> dict[str, Any]:
    return each(
        summarize_one,
        episode_ids,
        max_parallel=2,
        reducer=tally_statuses,
    )


def mcp_listings() -> dict[str, dict[str, dict[str, Any]]]:
    """Return an isolated copy of the memory-tools listing used for freezing."""
    return deepcopy(TOOL_LISTINGS)


def build_deployment() -> Deployment:
    """Compile the flow against the checked-in-equivalent MCP listing."""
    return deploy(batch, mcp_listings=mcp_listings())


def build_application() -> Application:
    """Build the application declaration published by the live harness."""
    return Application(
        "episode-summarizer",
        [
            PipelineSpec(
                name=PIPELINE_NAME,
                flow=batch,
                reasoners=[SUMMARIZER_R, ONE_LINER_R],
                lane=LANE,
                snapshot=snapshot_from_listings(mcp_listings()),
            )
        ],
    )


async def _fake_mcp_call(
    server: str,
    tool_name: str,
    value: Any,
    idempotency_key: str,
    principal: RunPrincipal | None,
) -> Any:
    """Deterministic in-process replacement for the three MCP tools."""
    del idempotency_key, principal
    if server != MCP_SERVER:
        raise KeyError(f"unknown fake MCP server {server!r}")
    if not isinstance(value, dict):
        raise TypeError("episode MCP tools require a record input")

    episode_id = str(value["episode_id"])
    if tool_name == "read-episode":
        return _read_episode(episode_id)
    if tool_name == "write-summary":
        return _write_summary(
            episode_id,
            str(value["source_hash"]),
            str(value["summary"]),
        )
    if tool_name == "write-one-liner":
        return _write_one_liner(
            episode_id,
            str(value["source_hash"]),
            str(value["one_liner"]),
        )
    raise KeyError(f"unknown fake MCP tool {server}/{tool_name}")


def _fake_summarizer(value: dict[str, Any]) -> dict[str, Any]:
    return {"summary": f"[fake summary] {value['text'][:72]}..."}


def _fake_one_liner(value: dict[str, Any]) -> dict[str, Any]:
    return {"oneLiner": f"[fake one-liner] {value['summary'][:64]}..."}


async def run_demo(
    episode_ids: list[str] | None = None,
    *,
    mcp_call: McpCaller = _fake_mcp_call,
) -> Any:
    """Run the deployment locally with no credentials or network calls."""
    _reset_store()
    inputs = [*EPISODE_IDS, MISSING_EPISODE_ID] if episode_ids is None else episode_ids
    return await build_deployment().adry_run(
        inputs,
        mcp_call=mcp_call,
        reasoners={
            SUMMARIZER_R.name: _fake_summarizer,
            ONE_LINER_R.name: _fake_one_liner,
        },
    )


def main() -> None:
    result = asyncio.run(run_demo())
    print("Episode-summary rollup:")
    print(json.dumps(result.value, indent=2))


if __name__ == "__main__":
    main()
