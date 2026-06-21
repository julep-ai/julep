"""Provider-neutral Batch API adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import SimpleNamespace
from typing import Any

from .llm import _split_model


class BatchProvider(ABC):
    """Base interface for provider-specific batch adapters."""

    @abstractmethod
    def build_request(
        self,
        custom_id: str,
        reasoner: Any,
        value: Any,
        *,
        transcript: Any = None,
        dispatch: Any = None,
    ) -> dict[str, Any]:
        """Build one provider batch request entry keyed by global custom_id."""

    @abstractmethod
    async def submit(self, requests: list[dict[str, Any]]) -> str:
        """Submit a batch and return the provider batch id."""

    @abstractmethod
    async def poll_status(self, batch_id: str) -> str:
        """Return normalized status: pending, completed, or failed.

        Providers map their own status values here, e.g. Anthropic
        ``processing_status == "ended"`` or OpenAI ``status == "completed"``.
        """

    @abstractmethod
    async def results(self, batch_id: str) -> Any:
        """Stream raw provider result entries keyed by custom_id.

        Concrete providers yield ``(custom_id, raw)`` pairs.
        """

    def parse(self, raw: Any, reasoner: Any) -> Any:
        """Parse one any-llm-shaped completion into complete_reasoner's reply shape.

        The default assumes ``raw`` looks like an any-llm completion with
        ``choices[0].message`` and shared ``content`` / ``parsed`` semantics.
        """
        from .llm import _parse_reply

        return _parse_reply(raw, expect_json=reasoner.reply_schema is not None)


_PROVIDERS: dict[str, type[BatchProvider]] = {}


def register_batch_provider(provider: str, cls: type[BatchProvider]) -> None:
    _PROVIDERS[provider] = cls


def select_batch_provider(
    model: str,
    *,
    default_provider: str = "anthropic",
) -> BatchProvider:
    provider, _ = _split_model(model, default_provider)
    cls = _PROVIDERS.get(provider)
    if cls is None:
        raise NotImplementedError(f"no BatchProvider registered for provider {provider!r}")
    return cls()


def _llm_completion_from_message(content: Any, *, parsed: Any = None) -> Any:
    """Build the completion shape consumed by ``llm._parse_reply``."""

    message = SimpleNamespace(content=content, parsed=parsed)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def _llm_completion_from_openai_body(raw: Any) -> Any:
    """Coerce an OpenAI batch response body into any-llm's completion shape."""

    if hasattr(raw, "choices"):
        return raw
    if not isinstance(raw, dict):
        return raw
    choices = raw.get("choices")
    if not isinstance(choices, list):
        return raw
    converted = []
    for choice in choices:
        message = choice.get("message") if isinstance(choice, dict) else None
        if isinstance(message, dict):
            message = SimpleNamespace(
                content=message.get("content"),
                parsed=message.get("parsed"),
            )
        converted.append(SimpleNamespace(message=message))
    return SimpleNamespace(choices=converted)


__all__ = ["BatchProvider", "select_batch_provider", "register_batch_provider"]
