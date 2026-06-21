"""Provider-neutral Batch API adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .llm import _split_model


class BatchProvider(ABC):
    """Base interface for provider-specific batch adapters."""

    @abstractmethod
    def build_request(
        self,
        custom_id: str,
        brain: Any,
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

    def parse(self, raw: Any, brain: Any) -> Any:
        """Parse one any-llm-shaped completion into complete_brain's reply shape.

        The default assumes ``raw`` looks like an any-llm completion with
        ``choices[0].message`` and shared ``content`` / ``parsed`` semantics.
        """
        from .llm import _parse_reply

        return _parse_reply(raw, expect_json=brain.reply_schema is not None)


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


__all__ = ["BatchProvider", "select_batch_provider", "register_batch_provider"]
