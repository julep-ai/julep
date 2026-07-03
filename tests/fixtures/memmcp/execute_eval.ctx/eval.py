# AI-ANCHOR: eval: tool-loop eval fixture samples + trace-derived scorer
"""Eval for the tool-loop fixture: scores the agent-loop terminal dict."""

from __future__ import annotations

from typing import Any

from dotctx.eval_types import MockToolConfig, Sample, stop_after_turns


def sample(limit: int = -1) -> list[Sample]:
    samples = [
        Sample(
            name="records_ok",
            input={"task": "store a memory"},
            expected={"must_call": ["record_memory"]},
            mock_tools={"record_memory": {"ok": True}},
            stop_on=stop_after_turns(4),
        ),
        Sample(
            name="search_mockcfg",
            input={"task": "search memories"},
            expected={"must_call": ["search"]},
            mock_tools={
                "search": MockToolConfig(
                    match=[({"query": "hits"}, ["a", "b"])],
                    default=[],
                )
            },
            stop_on=stop_after_turns(4),
        ),
        Sample(
            name="unmocked_fails",
            input={"task": "store without a mock"},
            expected={"must_call": ["record_memory"]},
            mock_tools={},
            stop_on=stop_after_turns(4),
        ),
    ]
    return samples if limit is None or limit < 0 else samples[:limit]


def score(_input: dict[str, Any], output: Any, expected: Any) -> float:
    """Score the agent-loop terminal dict: 0 if any tool errored, else the
    fraction of `must_call` tools that were actually called."""
    trace = output.get("trace", []) if isinstance(output, dict) else []
    if any(entry.get("error") for entry in trace):
        return 0.0
    called = [entry.get("ref") for entry in trace if entry.get("decision") == "call"]
    want = expected.get("must_call", []) if isinstance(expected, dict) else []
    if not want:
        return 1.0 if called else 0.0
    hits = sum(1 for w in want if w in called)
    return hits / len(want)
