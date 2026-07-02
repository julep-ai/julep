"""Anthropic Message Batches adapter for cross-run reasoner batching."""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from typing import Any

from ..prompt import rendered_user_for
from .batch_provider import (
    BatchProvider,
    BatchReply,
    _llm_completion_from_message,
    register_batch_provider,
)
from .llm import _messages, _split_model


@dataclass(frozen=True)
class _BatchEntryError:
    type: str


# any-llm's anthropic translation of CA effort levels (adaptive thinking +
# output_config effort); the batch path must match the sync path per reasoner.
_EFFORT_TO_ANTHROPIC = {
    "minimal": "low",
    "low": "low",
    "medium": "medium",
    "high": "high",
    "xhigh": "xhigh",
    "max": "max",
}


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
        reasoner: Any,
        value: Any,
        *,
        transcript: Any = None,
        dispatch: Any = None,
    ) -> dict[str, Any]:
        del dispatch
        _, model = _split_model(reasoner.model, "anthropic")
        schema = reasoner.reply_schema
        user_text = rendered_user_for(reasoner, value)
        messages = _messages(
            reasoner.system,
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
            "max_tokens": reasoner.max_tokens or 1024,
            "system": system_text,
            "messages": provider_messages,
        }
        # Mirror the sync path (execution/llm.py → any-llm): enable adaptive
        # thinking at the mapped effort and omit temperature while reasoning
        # is actually enabled.
        effort = reasoner.reasoning_effort
        if effort is not None and effort != "none":
            params["thinking"] = {"type": "adaptive"}
            params["output_config"] = {"effort": _EFFORT_TO_ANTHROPIC[effort]}
        if reasoner.temperature is not None and (effort is None or effort == "none"):
            params["temperature"] = reasoner.temperature
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

    def parse(self, raw: Any, reasoner: Any) -> Any:
        if isinstance(raw, _BatchEntryError):
            raise RuntimeError(f"batch entry {raw.type}")

        text = ""
        for block in getattr(raw, "content", []):
            if getattr(block, "type", None) == "text":
                value = getattr(block, "text", "")
                text = value if isinstance(value, str) else str(value)
                break
        completion = _llm_completion_from_message(
            text,
            parsed=getattr(raw, "parsed", None),
        )
        return super().parse(completion, reasoner)

    def parse_with_usage(self, raw: Any, reasoner: Any) -> BatchReply:
        u = getattr(raw, "usage", None)
        input_tokens = getattr(u, "input_tokens", None)
        output_tokens = getattr(u, "output_tokens", None)
        return BatchReply(
            reply=self.parse(raw, reasoner),
            input_tokens=input_tokens if isinstance(input_tokens, int) else None,
            output_tokens=output_tokens if isinstance(output_tokens, int) else None,
        )


register_batch_provider("anthropic", AnthropicBatchProvider)


__all__ = ["AnthropicBatchProvider"]
