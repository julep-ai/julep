"""Episode summaries with ``@flow`` record binding and frozen MCP tools.

Each episode is read through MCP, summarized by two reasoners, and written back
through MCP only when the source hash is unchanged. The keyless demo freezes a
checked-in MCP listing and injects deterministic fake MCP and reasoner callers.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any

from julep import Deployment, Reasoner, cond, deploy, each, flow, mcp_tool, pure, think
from julep.execution.effects import McpCaller, RunPrincipal

MODEL = "anthropic:claude-haiku-4-5-20251001"
MCP_SERVER = "episodes"
SUMMARIZER = "episode_summarizer"
ONE_LINER = "episode_one_liner"

EPISODE_BATCH = ["ep-1001", "ep-1002", "ep-1003", "ep-9999"]
MCP_LISTINGS_FIXTURE = (
    Path(__file__).resolve().parent / "fixtures" / "episode_mcp_listings.json"
)

_SEED: dict[str, str] = {
    "ep-1001": (
        "Diwank and the infra team spent the afternoon debugging why KEDA kept "
        "the Temporal worker scaled to zero. The scaler used the wrong task "
        "queue; fixing it drained the backlog. They added a queue-age alert."
    ),
    "ep-1002": (
        "The memory roadmap call prioritized episode summaries, then temporal "
        "rollups, then cluster labeling. Sarah asked for versioned prompts so "
        "stale summaries can be detected and regenerated."
    ),
    "ep-1003": (
        "A retry without an idempotency key double-charged 41 customers. Refunds "
        "were issued that day. The fix added a uniqueness constraint and a "
        "duplicate-webhook regression test."
    ),
}

_CONCURRENT_EDIT_ID = "ep-1003"
_store: dict[str, dict[str, Any]] = {}


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def reset_store() -> None:
    """Restore the deterministic in-process MCP-server state."""
    _store.clear()
    for episode_id, text in _SEED.items():
        _store[episode_id] = {
            "text": text,
            "contentHash": _content_hash(text),
            "summary": None,
            "oneLiner": None,
            "edited": False,
        }


reset_store()


def mcp_listings() -> dict[str, dict[str, Any]]:
    """Load the checked-in tools/list fixture used by freeze and the demo."""
    payload = json.loads(MCP_LISTINGS_FIXTURE.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("episode MCP listing fixture must be a JSON object")
    return payload


# These are references, not native Python tools. Their schemas and behavior
# contracts are resolved from the frozen MCP listing in build().
read_episode = mcp_tool(MCP_SERVER, "read_episode")
write_summary_surfaces = mcp_tool(MCP_SERVER, "write_summary_surfaces")


SUMMARIZER_R = Reasoner(
    name=SUMMARIZER,
    model=MODEL,
    system=(
        "Summarize the input episode's text in 2-4 plain sentences covering "
        'events, decisions, and follow-ups. Return {"summary": "..."}.'
    ),
    reply={
        "type": "object",
        "properties": {"summary": {"type": "string"}},
        "required": ["summary"],
    },
    max_tokens=1024,
)

ONE_LINER_R = Reasoner(
    name=ONE_LINER,
    model=MODEL,
    system=(
        "Compress the input summary into one sentence of at most 140 characters. "
        'Return {"oneLiner": "..."}.'
    ),
    reply={
        "type": "object",
        "properties": {"oneLiner": {"type": "string"}},
        "required": ["oneLiner"],
    },
    max_tokens=256,
)


@pure("episode_found")
def episode_found(source: dict[str, Any]) -> bool:
    return bool(source.get("found"))


@pure("not_found_status")
def not_found_status(source: dict[str, Any]) -> dict[str, Any]:
    return {"episodeId": source.get("episodeId"), "status": "not_found"}


@pure("tally_summary_statuses")
def tally_summary_statuses(results: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for result in results:
        status = str(result["status"])
        counts[status] = counts.get(status, 0) + 1
    return {"counts": counts, "results": results}


@flow
def summarize_found(source: dict[str, Any]) -> dict[str, Any]:
    summary = think(SUMMARIZER_R, source)
    one_liner = think(ONE_LINER_R, summary)
    return write_summary_surfaces(
        episode_id=source.episodeId,
        content_hash=source.contentHash,
        summary=summary.summary,
        one_liner=one_liner.oneLiner,
    )


@flow
def summarize_missing(source: dict[str, Any]) -> dict[str, Any]:
    return not_found_status(source)


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
        reducer=tally_summary_statuses,
    )


def build() -> Deployment:
    return deploy(
        batch,
        mcp_listings=mcp_listings(),
    )


def _read_episode(payload: dict[str, Any]) -> dict[str, Any]:
    episode_id = str(payload["episode_id"])
    row = _store.get(episode_id)
    if row is None:
        return {"episodeId": episode_id, "found": False}
    source = {
        "episodeId": episode_id,
        "found": True,
        "text": row["text"],
        "contentHash": row["contentHash"],
    }
    if episode_id == _CONCURRENT_EDIT_ID and not row["edited"]:
        row["text"] += " [edited after read: refund count corrected to 43]"
        row["contentHash"] = _content_hash(row["text"])
        row["edited"] = True
    return source


def _write_summary_surfaces(payload: dict[str, Any]) -> dict[str, Any]:
    episode_id = str(payload["episode_id"])
    row = _store.get(episode_id)
    if row is None:
        return {"episodeId": episode_id, "status": "not_found"}
    if row["contentHash"] != payload["content_hash"]:
        return {"episodeId": episode_id, "status": "stale_source"}
    row["summary"] = payload["summary"]
    row["oneLiner"] = payload["one_liner"]
    return {
        "episodeId": episode_id,
        "status": "success",
        "summary": payload["summary"],
        "oneLiner": payload["one_liner"],
    }


async def _fake_mcp_call(
    server: str,
    tool_name: str,
    value: Any,
    idempotency_key: str,
    principal: RunPrincipal | None,
) -> Any:
    """Deterministic stand-in for ``WorkerContext.mcp_call``."""
    del idempotency_key, principal
    if server != MCP_SERVER:
        raise KeyError(f"unknown fake MCP server {server!r}")
    if not isinstance(value, dict):
        raise TypeError("episode MCP tools require a record input")
    if tool_name == "read_episode":
        return _read_episode(value)
    if tool_name == "write_summary_surfaces":
        return _write_summary_surfaces(value)
    raise KeyError(f"unknown fake MCP tool {server}/{tool_name}")


def _fake_summarizer(value: dict[str, Any]) -> dict[str, Any]:
    return {"summary": f"[fake summary] {value['text'][:60]}..."}


def _fake_one_liner(value: dict[str, Any]) -> dict[str, Any]:
    return {"oneLiner": f"[fake one-liner] {value['summary'][:40]}..."}


async def run_demo(
    episode_ids: list[str] | None = None,
    *,
    mcp_call: McpCaller = _fake_mcp_call,
) -> Any:
    reset_store()
    return await build().adry_run(
        EPISODE_BATCH if episode_ids is None else episode_ids,
        mcp_call=mcp_call,
        reasoners={SUMMARIZER: _fake_summarizer, ONE_LINER: _fake_one_liner},
    )


def main() -> None:
    result = asyncio.run(run_demo())
    print("Episode summary rollup:")
    print(json.dumps(result.value, indent=2))


if __name__ == "__main__":
    main()
