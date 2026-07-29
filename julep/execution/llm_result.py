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
from typing import Any, Literal


LlmCostStatus = Literal["reported", "derived", "unknown"]


@dataclass(frozen=True)
class LlmUsage:
    """Provider-neutral token usage for one or more model calls."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    cache_read_tokens: int | None = None
    cache_creation_tokens: int | None = None


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
    skill_loads: tuple[str, ...] = ()
    prompt_cache_requested: str | None = None
    prompt_cache_applied: bool | None = None
    prompt_cache_reason: str | None = None
    cache_read_tokens: int | None = None
    cache_creation_tokens: int | None = None
    # Additive typed view. The scalar fields above remain for source and
    # constructor compatibility with callers built against rc5/early rc6.
    usage: LlmUsage | None = None
    cost_status: LlmCostStatus | None = None

    def resolved_usage(self) -> LlmUsage:
        """Return the typed usage, including legacy scalar metadata."""

        if self.usage is not None:
            return self.usage
        return LlmUsage(
            prompt_tokens=self.input_tokens,
            completion_tokens=self.output_tokens,
            total_tokens=self.total_tokens,
            cache_read_tokens=self.cache_read_tokens,
            cache_creation_tokens=self.cache_creation_tokens,
        )

    def resolved_cost_status(self) -> LlmCostStatus:
        """Infer the pre-status contract for backwards-compatible callers."""

        if self.cost_status is not None:
            return self.cost_status
        return "reported" if self.cost is not None else "unknown"

    def to_attrs(self) -> dict[str, Any]:
        out: dict[str, Any] = {"llm.model": self.served_model, "llm.provider": self.provider}
        usage = self.resolved_usage()
        if usage.prompt_tokens is not None or usage.completion_tokens is not None:
            out["llm.usage"] = {
                "input": usage.prompt_tokens,
                "output": usage.completion_tokens,
                "total": usage.total_tokens,
            }
        if self.started_at is not None:
            out["llm.started_at"] = self.started_at
        if self.ended_at is not None:
            out["llm.ended_at"] = self.ended_at
        if self.cost is not None:
            out["llm.cost"] = self.cost
        out["llm.cost.status"] = self.resolved_cost_status()
        if self.response_format_fallback is not None:
            out["llm.response_format_fallback"] = self.response_format_fallback
        if self.output_retries_used:
            out["llm.output_retries"] = self.output_retries_used
        if self.native_tool_calls:
            out["llm.tool_calls"] = self.native_tool_calls
        if self.skill_loads:
            out["llm.skill_loads"] = list(self.skill_loads)
        cache: dict[str, Any] = {}
        if self.prompt_cache_requested is not None:
            cache["requested"] = self.prompt_cache_requested
        if self.prompt_cache_applied is not None:
            cache["applied"] = self.prompt_cache_applied
        if self.prompt_cache_reason is not None:
            cache["reason"] = self.prompt_cache_reason
        if usage.cache_read_tokens is not None:
            cache["read"] = usage.cache_read_tokens
        if usage.cache_creation_tokens is not None:
            cache["creation"] = usage.cache_creation_tokens
        if cache:
            out["llm.cache"] = cache
        if self.attempts:
            out["llm.attempts"] = [
                {
                    "model": a.model,
                    "provider": a.provider,
                    "outcome": a.outcome,
                    "input": a.input_tokens,
                    "output": a.output_tokens,
                    "ms": a.ms,
                }
                for a in self.attempts
            ]
        return out


@dataclass(frozen=True)
class LlmResult:
    reply: Any
    meta: LlmCallMeta
