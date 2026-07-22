"""Authenticated MCP tools for the episode-summarizer example.

The backing store deliberately lives in this module so the live harness can run
the ASGI app in-process and inspect the writes after the workflow completes.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from julep.mcp_auth import ASGIApp, asgi_auth_middleware, verify_keys_from_env

MCP_SERVER = "episodes"
MCP_AUDIENCE = MCP_SERVER
MCP_PATH = "/mcp"
MISSING_EPISODE_ID = "ep-missing"

_EPISODE_TEXTS: dict[str, str] = {
    "ep-orchard": (
        "Mara noticed the community orchard's irrigation timer was running at noon. "
        "She moved it to dawn and asked the volunteers to check the soil again Friday."
    ),
    "ep-library": (
        "The library team tested a quiet-hour pilot for the upstairs study room. "
        "Visitors liked it, so Priya scheduled a two-week trial and a feedback survey."
    ),
    "ep-bakery": (
        "Jon's bakery sold out of rye bread before lunch three days in a row. "
        "He increased Thursday's batch and left a note to review waste at closing."
    ),
}

# These are the found episodes. Callers append MISSING_EPISODE_ID when they want
# to exercise the flow's not-found branch.
EPISODE_IDS: tuple[str, ...] = tuple(_EPISODE_TEXTS)

_READ_ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}
_WRITE_ANNOTATIONS = {
    "readOnlyHint": False,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}

_STRING_PROPERTY = {"type": "string"}
_READ_INPUT_SCHEMA = {
    "type": "object",
    "properties": {"episode_id": _STRING_PROPERTY},
    "required": ["episode_id"],
    "additionalProperties": False,
}
_WRITE_SUMMARY_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "episode_id": _STRING_PROPERTY,
        "source_hash": _STRING_PROPERTY,
        "summary": _STRING_PROPERTY,
    },
    "required": ["episode_id", "source_hash", "summary"],
    "additionalProperties": False,
}
_WRITE_ONE_LINER_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "episode_id": _STRING_PROPERTY,
        "source_hash": _STRING_PROPERTY,
        "one_liner": _STRING_PROPERTY,
    },
    "required": ["episode_id", "source_hash", "one_liner"],
    "additionalProperties": False,
}

TOOL_LISTINGS: dict[str, dict[str, dict[str, Any]]] = {
    MCP_SERVER: {
        "read-episode": {
            "inputSchema": _READ_INPUT_SCHEMA,
            "annotations": _READ_ANNOTATIONS,
            "outputSchema": {
                "type": "object",
                "properties": {
                    "episodeId": _STRING_PROPERTY,
                    "found": {"type": "boolean"},
                    "text": _STRING_PROPERTY,
                    "sourceHash": _STRING_PROPERTY,
                },
                "required": ["episodeId", "found"],
                "additionalProperties": False,
            },
        },
        "write-summary": {
            "inputSchema": _WRITE_SUMMARY_INPUT_SCHEMA,
            "annotations": _WRITE_ANNOTATIONS,
            "outputSchema": {
                "type": "object",
                "properties": {
                    "episodeId": _STRING_PROPERTY,
                    "summaryStatus": _STRING_PROPERTY,
                    "summary": _STRING_PROPERTY,
                },
                "required": ["episodeId", "summaryStatus"],
                "additionalProperties": False,
            },
        },
        "write-one-liner": {
            "inputSchema": _WRITE_ONE_LINER_INPUT_SCHEMA,
            "annotations": _WRITE_ANNOTATIONS,
            "outputSchema": {
                "type": "object",
                "properties": {
                    "episodeId": _STRING_PROPERTY,
                    "oneLinerStatus": _STRING_PROPERTY,
                    "oneLiner": _STRING_PROPERTY,
                },
                "required": ["episodeId", "oneLinerStatus"],
                "additionalProperties": False,
            },
        },
    }
}

_store: dict[str, dict[str, Any]] = {}


def _source_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def seed(episodes: Mapping[str, str] | None = None) -> None:
    """Add the default episodes, or a caller-provided set, to the store."""
    source = _EPISODE_TEXTS if episodes is None else episodes
    for episode_id, text in source.items():
        _store[episode_id] = {
            "text": text,
            "sourceHash": _source_hash(text),
            "summary": None,
            "oneLiner": None,
        }


def reset() -> None:
    """Restore the small deterministic episode fixture."""
    _store.clear()
    seed()


def store_snapshot() -> dict[str, dict[str, Any]]:
    """Return an isolated copy suitable for live-harness assertions."""
    return deepcopy(_store)


def read_episode(episode_id: str) -> dict[str, Any]:
    """Read an episode transcript and the hash guarding subsequent writes."""
    row = _store.get(episode_id)
    if row is None:
        return {"episodeId": episode_id, "found": False}
    return {
        "episodeId": episode_id,
        "found": True,
        "text": row["text"],
        "sourceHash": row["sourceHash"],
    }


def write_summary(episode_id: str, source_hash: str, summary: str) -> dict[str, Any]:
    """Store a summary when the caller read the current episode revision."""
    row = _store.get(episode_id)
    if row is None:
        return {"episodeId": episode_id, "summaryStatus": "unknown"}
    if source_hash != row["sourceHash"]:
        return {"episodeId": episode_id, "summaryStatus": "stale_source"}
    row["summary"] = summary
    return {
        "episodeId": episode_id,
        "summaryStatus": "written",
        "summary": summary,
    }


def write_one_liner(episode_id: str, source_hash: str, one_liner: str) -> dict[str, Any]:
    """Store a one-liner when the caller read the current episode revision."""
    row = _store.get(episode_id)
    if row is None:
        return {"episodeId": episode_id, "oneLinerStatus": "unknown"}
    if source_hash != row["sourceHash"]:
        return {"episodeId": episode_id, "oneLinerStatus": "stale_source"}
    row["oneLiner"] = one_liner
    return {
        "episodeId": episode_id,
        "oneLinerStatus": "written",
        "oneLiner": one_liner,
    }


def _annotations(values: Mapping[str, bool]) -> ToolAnnotations:
    return ToolAnnotations(**dict(values))


def _build_mcp() -> FastMCP:
    mcp = FastMCP(
        "memory-tools",
        streamable_http_path=MCP_PATH,
        stateless_http=True,
    )
    mcp.tool(
        name="read-episode",
        annotations=_annotations(_READ_ANNOTATIONS),
        structured_output=True,
    )(read_episode)
    mcp.tool(
        name="write-summary",
        annotations=_annotations(_WRITE_ANNOTATIONS),
        structured_output=True,
    )(write_summary)
    mcp.tool(
        name="write-one-liner",
        annotations=_annotations(_WRITE_ANNOTATIONS),
        structured_output=True,
    )(write_one_liner)
    return mcp


def build_app() -> ASGIApp:
    """Build the streamable-HTTP MCP app with Julep's JWT guard in front."""
    app = _build_mcp().streamable_http_app()
    return asgi_auth_middleware(
        app,
        verify_keys=verify_keys_from_env(),
        audience=MCP_AUDIENCE,
        required_scopes=(),
        issuer=os.environ.get("JULEP_MCP_ISSUER") or None,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--host",
        default=os.environ.get("EPISODE_TOOLS_HOST", "127.0.0.1"),
        help="interface to bind (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("EPISODE_TOOLS_PORT", "8000")),
        help="port to bind (default: 8000)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    import uvicorn

    uvicorn.run(build_app(), host=args.host, port=args.port)


reset()


if __name__ == "__main__":
    main()
