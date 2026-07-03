# AI-ANCHOR: eval: record/execute acceptance fixture samples + trace-derived scorer
"""Eval suite for the record/execute acceptance fixture.

Three samples, one per mock tool. The scorer reads the agent-loop terminal
dict: 0 if any tool errored, else the fraction of the expected ``must_call``
tools actually called (mem-mcp record/execute semantics: success = the tool
side-effects happened).
"""

from __future__ import annotations

from typing import Any

from dotctx.eval_types import Sample, stop_after_turns


def sample(limit: int = -1) -> list[Sample]:
    samples = [
        Sample(
            name="records_ok",
            input={"task": "record a memory"},
            expected={"must_call": ["record_memory"]},
            mock_tools={"record_memory": {"ok": True}},
            stop_on=stop_after_turns(6),
        ),
        Sample(
            name="searches_ok",
            input={"task": "search memories"},
            expected={"must_call": ["search"]},
            mock_tools={"search": ["alice", "bob"]},
            stop_on=stop_after_turns(6),
        ),
        Sample(
            name="recalls_ok",
            input={"task": "recall a memory"},
            expected={"must_call": ["recall"]},
            mock_tools={"recall": {"value": "remembered"}},
            stop_on=stop_after_turns(6),
        ),
    ]
    return samples if limit is None or limit < 0 else samples[:limit]


def score(_input: dict[str, Any], output: Any, expected: Any) -> float:
    trace = output.get("trace", []) if isinstance(output, dict) else []
    if any(entry.get("error") for entry in trace):
        return 0.0
    called = [entry.get("ref") for entry in trace if entry.get("decision") == "call"]
    want = expected.get("must_call", []) if isinstance(expected, dict) else []
    if not want:
        return 1.0 if called else 0.0
    hits = sum(1 for w in want if w in called)
    return hits / len(want)
