"""Normalize mem-mcp-style model slugs into CA's canonical ``provider:model``.

Accepted inputs: ``provider:model``, ``provider/model``, bare model names, each
optionally suffixed ``@<effort>``. The effort suffix is only recognized when it
is a known level — ``model@vintage`` stays a model name. Pure module: no IO.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# mem-mcp's levels plus any-llm's "max". "auto" is any-llm's implicit default
# and deliberately not declarable.
EFFORT_LEVELS: frozenset[str] = frozenset(
    {"none", "minimal", "low", "medium", "high", "xhigh", "max"}
)

_PREFIX_MAP = {"vertex_ai": "vertexai", "google": "gemini", "gemini": "gemini"}


@dataclass(frozen=True)
class ModelSlug:
    model: str
    reasoning_effort: Optional[str]
    raw: str


def normalize_model_slug(raw: str) -> ModelSlug:
    trimmed = raw.strip()
    if not trimmed:
        raise ValueError("model slug is empty")

    effort: Optional[str] = None
    if "@" in trimmed:
        candidate, suffix = trimmed.rsplit("@", 1)
        if suffix.strip().lower() in EFFORT_LEVELS:
            trimmed, effort = candidate.strip(), suffix.strip().lower()

    colon, slash = trimmed.find(":"), trimmed.find("/")
    if colon == -1 and slash == -1:
        return ModelSlug(model=trimmed, reasoning_effort=effort, raw=raw)
    if colon != -1 and (slash == -1 or colon < slash):
        provider, rest = trimmed.split(":", 1)
    else:
        provider, rest = trimmed.split("/", 1)
    provider = _PREFIX_MAP.get(provider, provider)
    return ModelSlug(model=f"{provider}:{rest}", reasoning_effort=effort, raw=raw)


__all__ = ["EFFORT_LEVELS", "ModelSlug", "normalize_model_slug"]
