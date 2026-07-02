# AI-ANCHOR: eval: episode summary samples + scorer (trimmed vendored copy)
"""Eval for the canonical episode_summary prompt."""

from __future__ import annotations

import json
from typing import Any

from dotctx import extract_llm_content
from dotctx.eval_types import Sample

SAMPLES: list[dict[str, Any]] = [
    {
        "name": "meeting_with_context",
        "tags": ["smoke"],
        "input": {
            "content": "Alice met Bob at the London office to review the Atlas rollout.",
            "background": "The meeting confirmed the rollout would continue next week.",
        },
        "expected": {
            "must_contain": ["Alice", "Bob", "London", "Atlas", "rollout"],
            "must_not_contain": ["Summary:", "Here is", "one_liner"],
            "max_words": 150,
        },
    },
    {
        "name": "empty_background",
        "tags": ["edge"],
        "input": {
            "content": "Nina approved the Atlas launch in Berlin after the final review.",
            "background": None,
        },
        "expected": {
            "must_contain": ["Nina", "Atlas", "Berlin"],
            "must_not_contain": ["Summary:", "manager", "CEO", "one_liner"],
            "max_words": 60,
        },
    },
]


def sample(limit: int = -1) -> list[Sample]:
    """Return eval samples for episode_summary."""
    samples = [
        Sample(
            input=item["input"],
            expected=item["expected"],
            tags=item.get("tags", []),
            name=item["name"],
        )
        for item in SAMPLES
    ]
    if limit is not None and limit > 0:
        return samples[:limit]
    return samples


def _parse_output(output: Any) -> dict[str, Any] | None:
    text = (extract_llm_content(output) or "").strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def score(_input: dict[str, Any], output: Any, expected: Any) -> float:
    """Score summary output for JSON shape and grounding."""
    parsed = _parse_output(output)
    if parsed is None:
        return 0.0

    summary = parsed.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        return 0.0

    text = summary.strip()
    checks: list[bool] = [set(parsed.keys()) == {"summary"}]
    checks.append(len(text.split()) <= int(expected.get("max_words", 150)))

    lower = text.lower()
    for term in expected.get("must_contain", []):
        checks.append(term.lower() in lower)
    for term in expected.get("must_not_contain", []):
        checks.append(term.lower() not in lower)

    return sum(checks) / len(checks)
