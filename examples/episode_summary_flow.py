"""Episode summary pipeline — a mem-mcp workflow as a ``@flow`` definition.

A faithful port of mem-mcp's ``workflows/summary.py::process_summary`` (plus its
batch-dispatch shape): for each episode, read the source text, generate a
2-4 sentence summary and a one-liner abstract with two model calls, then write
both surfaces back **only if the content hash is unchanged** (the CAS guard the
product uses against concurrent edits). Episodes fan out with bounded
parallelism, mirroring the product's queue concurrency.

Structure notes:

* The flow uses define-by-construction authoring: ``@flow`` runs once at import
  time with data handles, so ordinary Python assignments name graph nodes while
  tools, reasoners, pures, ``cond``, and ``each`` append steps.
* Independent read/pure/reasoner work can be inferred as parallel by the DAG
  compiler when effect-safe; write and external-effect steps remain ordered
  barriers, so the CAS read -> model work -> guarded write shape stays intact.
* The "database" is an in-process store behind two native tools
  (``read_episode`` / ``write_summary_surfaces``); episode ``ep-1003`` simulates
  a concurrent edit between read and write, exercising the ``stale_source``
  branch end-to-end.
* ``run_demo()`` is the keyless dry run on ``InMemoryEnv`` (no API key, network,
  or Temporal). On Temporal, ``build().run(client, ...)`` drives the same frozen
  artifact with real model calls (see tooling/k3d-flow-demo/).
* The lower-level combinator kernel remains available for escape hatches; see
  the "Authoring DSL" section of the repo ``README.md``.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any

from composable_agents import (
    Reasoner,
    Deployment,
    cond,
    deploy,
    each,
    flow,
    pure,
    think,
    tool,
)

MODEL = "anthropic:claude-haiku-4-5-20251001"

SUMMARIZER = "episode_summarizer"
ONE_LINER = "episode_one_liner"

# The default batch: two clean episodes, one that gets edited mid-flight
# (stale_source), and one that does not exist (not_found).
EPISODE_BATCH = ["ep-1001", "ep-1002", "ep-1003", "ep-9999"]


# --------------------------------------------------------------------------- #
# The "episodes table": an in-process stand-in for the product DB.
# --------------------------------------------------------------------------- #
_SEED: dict[str, str] = {
    "ep-1001": (
        "Diwank and the infra team spent the afternoon debugging why KEDA kept "
        "the Temporal worker scaled to zero. The scaler was pointed at the "
        "wrong task queue name; after fixing the queue in the ScaledObject the "
        "deployment scaled 0 -> 1 within thirty seconds and drained the "
        "backlog. They agreed to alert on queue depth older than five minutes."
    ),
    "ep-1002": (
        "Planning call about the memory consolidation roadmap: ship episode "
        "summaries first, then temporal rollups, then cluster labeling. Sarah "
        "raised that summary prompts must be versioned so stale summaries can "
        "be detected and regenerated. Action item: add prompt_version to the "
        "summary ledger before the next release."
    ),
    "ep-1003": (
        "Incident retro for the duplicate-billing bug: a retry without an "
        "idempotency key double-charged 41 customers. Refunds were issued the "
        "same day. The fix adds a uniqueness constraint on (account, charge "
        "nonce) and a regression test that replays the duplicate webhook."
    ),
}

# ep-1003 simulates a user editing the episode while the summary is in flight:
# the read tool serves the original text, then bumps the stored content, so the
# CAS write later observes a different hash and reports stale_source.
_CONCURRENT_EDIT_ID = "ep-1003"

_store: dict[str, dict[str, Any]] = {}


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def reset_store() -> None:
    """Re-seed the episode store (call before each demo run)."""
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


# --------------------------------------------------------------------------- #
# Tools (the product's DB steps).
# --------------------------------------------------------------------------- #
@tool(effect="read", idempotent=True)
def read_episode(episode_id: str) -> dict[str, Any]:
    """Fetch an episode's text + content hash (mem-mcp read_summary_source_step)."""
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


@tool(effect="write", idempotent=True)
def write_summary_surfaces(payload: dict[str, Any]) -> dict[str, Any]:
    """Persist summary + one-liner iff content is unchanged (CAS on hash)."""
    episode_id = payload["episodeId"]
    row = _store.get(episode_id)
    if row is None:
        return {"episodeId": episode_id, "status": "not_found"}
    if row["contentHash"] != payload["contentHash"]:
        return {"episodeId": episode_id, "status": "stale_source"}
    row["summary"] = payload["summary"]
    row["oneLiner"] = payload["oneLiner"]
    return {
        "episodeId": episode_id,
        "status": "success",
        "summary": payload["summary"],
        "oneLiner": payload["oneLiner"],
    }


TOOLS = [read_episode, write_summary_surfaces]


# --------------------------------------------------------------------------- #
# Reasoners (the product's two LLM passes), declared as deployable objects.
# --------------------------------------------------------------------------- #
SUMMARIZER_R = Reasoner(
    name=SUMMARIZER,
    model=MODEL,
    system=(
        "You summarize episodic memory records for a memory store. The user "
        "message is a JSON object; summarize its 'text' field in 2-4 plain "
        "sentences covering what happened, decisions made, and follow-ups. "
        'Reply with exactly one JSON object: {"summary": "..."}.'
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
        "You write one-line abstracts. The user message is a JSON object "
        "with a 'summary' field; compress it into a single sentence of at "
        'most 140 characters. Reply with exactly one JSON object: '
        '{"oneLiner": "..."}.'
    ),
    reply={
        "type": "object",
        "properties": {"oneLiner": {"type": "string"}},
        "required": ["oneLiner"],
    },
    max_tokens=256,
)


# --------------------------------------------------------------------------- #
# Pures (branching/status and the batch rollup) — pinned by source hash.
# --------------------------------------------------------------------------- #
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
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    return {"counts": counts, "results": results}


# --------------------------------------------------------------------------- #
# The flow.
# --------------------------------------------------------------------------- #
@flow
def happy_path(source: dict[str, Any]) -> dict[str, Any]:
    summary = think(SUMMARIZER_R, source)
    merged = source | summary
    liner = think(ONE_LINER_R, merged)
    return write_summary_surfaces(merged | liner)


@flow
def not_found(source: dict[str, Any]) -> dict[str, Any]:
    status = not_found_status(source)
    return status


@flow
def summarize_one(episode_id: str) -> dict[str, Any]:
    source = read_episode(episode_id)
    return cond(episode_found, source, then=happy_path, orelse=not_found)


@flow
def batch(episode_ids: list[str]) -> dict[str, Any]:
    return each(
        summarize_one,
        episode_ids,
        max_parallel=2,
        reducer=tally_summary_statuses,
    )


def build() -> Deployment:
    return deploy(batch, tools=TOOLS, reasoners=[SUMMARIZER_R, ONE_LINER_R])


# --------------------------------------------------------------------------- #
# Keyless dry run: deterministic fake reasoners on InMemoryEnv.
# --------------------------------------------------------------------------- #
def _fake_summarizer(value: dict[str, Any]) -> dict[str, Any]:
    return {"summary": f"[fake summary] {value['text'][:60]}..."}


def _fake_one_liner(value: dict[str, Any]) -> dict[str, Any]:
    return {"oneLiner": f"[fake one-liner] {value['summary'][:40]}..."}


async def run_demo(batch: list[str] | None = None) -> Any:
    reset_store()
    deployment = build()
    return await deployment.adry_run(
        batch or EPISODE_BATCH,
        reasoners={SUMMARIZER: _fake_summarizer, ONE_LINER: _fake_one_liner},
    )


def main() -> None:
    result = asyncio.run(run_demo())
    print("Episode summary rollup:")
    print(json.dumps(result.value, indent=2))


if __name__ == "__main__":
    main()
