"""Anthropic Message Batches adapter for cross-run brain batching."""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from typing import Any

from ..prompt import rendered_user_for
from .batch_provider import BatchProvider, register_batch_provider
from .llm import _messages, _split_model, _strip_code_fence


@dataclass(frozen=True)
class _BatchEntryError:
    type: str


class AnthropicBatchProvider(BatchProvider):
    """BatchProvider implementation backed by Anthropic Message Batches."""

    def __init__(self, *, client: Any = None) -> None:
        self._client = client

    async def _get_client(self) -> Any:
        if self._client is None:
            try:
                import anthropic
            except ImportError as exc:  # pragma: no cover - only exercised without SDK
                raise ImportError(
                    "anthropic is required for Anthropic batch calls; install "
                    "composable-agents[providers] plus the Anthropic provider extra "
                    "(e.g. pip install 'any-llm-sdk[anthropic]')."
                ) from exc
            self._client = anthropic.AsyncAnthropic()
        return self._client

    def build_request(
        self,
        custom_id: str,
        brain: Any,
        value: Any,
        *,
        transcript: Any = None,
        dispatch: Any = None,
    ) -> dict[str, Any]:
        del dispatch
        _, model = _split_model(brain.model, "anthropic")
        schema = brain.reply_schema
        user_text = rendered_user_for(brain, value)
        messages = _messages(
            brain.system,
            value,
            schema_hint=schema,
            user_text=user_text,
            transcript=transcript,
        )
        system_text = None
        provider_messages: list[dict[str, Any]] = []
        for message in messages:
            if message.get("role") == "system" and system_text is None:
                content = message.get("content")
                system_text = content if isinstance(content, str) else json.dumps(content)
            else:
                provider_messages.append(message)

        params: dict[str, Any] = {
            "model": model,
            "max_tokens": brain.max_tokens or 1024,
            "system": system_text,
            "messages": provider_messages,
        }
        if brain.temperature is not None:
            params["temperature"] = brain.temperature
        return {"custom_id": custom_id, "params": params}

    async def submit(self, requests: list[dict[str, Any]]) -> str:
        client = await self._get_client()
        try:
            from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
            from anthropic.types.messages.batch_create_params import Request
        except ImportError as exc:  # pragma: no cover - only exercised without SDK
            raise ImportError(
                "anthropic is required for Anthropic batch calls; install "
                "composable-agents[providers] plus the Anthropic provider extra "
                "(e.g. pip install 'any-llm-sdk[anthropic]')."
            ) from exc

        sdk_requests = []
        for request in requests:
            params = dict(request["params"])
            if params.get("system") is None:
                params.pop("system", None)
            sdk_requests.append(
                Request(
                    custom_id=str(request["custom_id"]),
                    params=MessageCreateParamsNonStreaming(**params),
                )
            )
        batch = await client.messages.batches.create(requests=sdk_requests)
        return str(batch.id)

    async def poll_status(self, batch_id: str) -> str:
        client = await self._get_client()
        batch = await client.messages.batches.retrieve(batch_id)
        return "completed" if batch.processing_status == "ended" else "pending"

    async def results(self, batch_id: str) -> Any:
        client = await self._get_client()
        result_iter = client.messages.batches.results(batch_id)
        if inspect.isawaitable(result_iter):
            result_iter = await result_iter
        async for result in result_iter:
            result_type = result.result.type
            if result_type == "succeeded":
                yield (str(result.custom_id), result.result.message)
            else:
                yield (str(result.custom_id), _BatchEntryError(str(result_type)))

    def parse(self, raw: Any, brain: Any) -> Any:
        if isinstance(raw, _BatchEntryError):
            raise RuntimeError(f"batch entry {raw.type}")

        text = ""
        for block in getattr(raw, "content", []):
            if getattr(block, "type", None) == "text":
                value = getattr(block, "text", "")
                text = value if isinstance(value, str) else str(value)
                break
        if brain.reply_schema is None:
            return text
        try:
            return json.loads(_strip_code_fence(text))
        except (json.JSONDecodeError, ValueError):
            return text


register_batch_provider("anthropic", AnthropicBatchProvider)


__all__ = ["AnthropicBatchProvider"]
