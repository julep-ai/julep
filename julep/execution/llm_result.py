"""Typed result envelope for a single reasoner model call.

The ``LlmCaller`` seam returns the parsed reply *and* the metadata an
observability sink needs (served model, token usage, wall-clock window, and the
per-attempt ladder the resilience caller walked). ``meta.to_attrs()`` renders a
vendor-neutral dict that rides the existing ``Result.attrs`` ->
``ProjectionEvent.attrs`` seam; the Langfuse exporter maps it to gen_ai/langfuse
attributes downstream. Pure module: no IO, no engine imports.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class AttemptMeta:
    model: str
    provider: str
    outcome: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    ms: float | None = None

@dataclass(frozen=True)
class LlmCallMeta:
    served_model: str
    provider: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    started_at: float | None = None
    ended_at: float | None = None
    attempts: tuple[AttemptMeta, ...] = ()
    cost: float | None = None
    response_format_fallback: str | None = None
    output_retries_used: int = 0
    native_tool_calls: int = 0
    prompt_cache_requested: str | None = None
    prompt_cache_applied: bool | None = None
    prompt_cache_reason: str | None = None
    cache_read_tokens: int | None = None
    cache_creation_tokens: int | None = None

    def to_attrs(self) -> dict[str, Any]:
        out: dict[str, Any] = {"llm.model": self.served_model, "llm.provider": self.provider}
        if self.input_tokens is not None or self.output_tokens is not None:
            out["llm.usage"] = {
                "input": self.input_tokens,
                "output": self.output_tokens,
                "total": self.total_tokens,
            }
        if self.started_at is not None:
            out["llm.started_at"] = self.started_at
        if self.ended_at is not None:
            out["llm.ended_at"] = self.ended_at
        if self.cost is not None:
            out["llm.cost"] = self.cost
        if self.response_format_fallback is not None:
            out["llm.response_format_fallback"] = self.response_format_fallback
        if self.output_retries_used:
            out["llm.output_retries"] = self.output_retries_used
        if self.native_tool_calls:
            out["llm.tool_calls"] = self.native_tool_calls
        cache: dict[str, Any] = {}
        if self.prompt_cache_requested is not None:
            cache["requested"] = self.prompt_cache_requested
        if self.prompt_cache_applied is not None:
            cache["applied"] = self.prompt_cache_applied
        if self.prompt_cache_reason is not None:
            cache["reason"] = self.prompt_cache_reason
        if self.cache_read_tokens is not None:
            cache["read"] = self.cache_read_tokens
        if self.cache_creation_tokens is not None:
            cache["creation"] = self.cache_creation_tokens
        if cache:
            out["llm.cache"] = cache
        if self.attempts:
            out["llm.attempts"] = [
                {"model": a.model, "provider": a.provider, "outcome": a.outcome,
                 "input": a.input_tokens, "output": a.output_tokens, "ms": a.ms}
                for a in self.attempts
            ]
        return out

@dataclass(frozen=True)
class LlmResult:
    reply: Any
    meta: LlmCallMeta
