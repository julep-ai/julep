"""OpenAI Batch API adapter for cross-run brain batching."""

from __future__ import annotations

import inspect
import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from ..prompt import rendered_user_for
from .batch_provider import BatchProvider, register_batch_provider
from .llm import _messages, _response_format, _split_model, _strip_code_fence


@dataclass(frozen=True)
class _BatchEntryError:
    type: str


class OpenAIBatchProvider(BatchProvider):
    """BatchProvider implementation backed by the OpenAI Batch API."""

    def __init__(self, *, client: Any = None) -> None:
        self._client = client

    async def _get_client(self) -> Any:
        if self._client is None:
            try:
                import openai
            except ImportError as exc:  # pragma: no cover - only exercised without SDK
                raise ImportError(
                    "openai is required for OpenAI batch calls; install "
                    "composable-agents[providers] plus the OpenAI provider extra "
                    "(e.g. pip install 'any-llm-sdk[openai]')."
                ) from exc
            self._client = openai.AsyncOpenAI()
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
        _, model = _split_model(brain.model, "openai")
        schema = brain.reply_schema
        user_text = rendered_user_for(brain, value)
        body: dict[str, Any] = {
            "model": model,
            "messages": _messages(
                brain.system,
                value,
                schema_hint=None,
                user_text=user_text,
                transcript=transcript,
            ),
            "max_tokens": brain.max_tokens or 1024,
        }
        if brain.temperature is not None:
            body["temperature"] = brain.temperature
        if schema is not None:
            body["response_format"] = _response_format(schema)
        return {
            "custom_id": custom_id,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": body,
        }

    async def submit(self, requests: list[dict[str, Any]]) -> str:
        client = await self._get_client()
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for request in requests:
            grouped[str(request["body"]["model"])].append(request)

        batch_ids = []
        for model_requests in grouped.values():
            payload = "\n".join(json.dumps(request) for request in model_requests)
            data = (payload + "\n").encode()
            uploaded = await client.files.create(file=data, purpose="batch")
            batch = await client.batches.create(
                input_file_id=str(uploaded.id),
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )
            batch_ids.append(str(batch.id))
        return ",".join(batch_ids)

    async def poll_status(self, batch_id: str) -> str:
        client = await self._get_client()
        statuses = []
        for sub_batch_id in _split_composite_id(batch_id):
            batch = await client.batches.retrieve(sub_batch_id)
            statuses.append(str(getattr(batch, "status", "")))

        if any(status in {"failed", "cancelled", "expired"} for status in statuses):
            return "failed"
        if statuses and all(status == "completed" for status in statuses):
            return "completed"
        return "pending"

    async def results(self, batch_id: str) -> Any:
        client = await self._get_client()
        for sub_batch_id in _split_composite_id(batch_id):
            batch = await client.batches.retrieve(sub_batch_id)
            output_file_id = getattr(batch, "output_file_id", None)
            if not output_file_id:
                continue
            content = await client.files.content(output_file_id)
            text = await _content_text(content)
            for line in text.splitlines():
                if not line.strip():
                    continue
                entry = json.loads(line)
                custom_id = str(entry["custom_id"])
                # OpenAI batch output lines carry ``"error": null`` on success, so
                # a bare key check would misroute every successful reply as failed.
                error = entry.get("error")
                if error is not None:
                    yield (custom_id, _BatchEntryError(_error_type(error)))
                else:
                    yield (custom_id, entry["response"]["body"])

    def parse(self, raw: Any, brain: Any) -> Any:
        if isinstance(raw, _BatchEntryError):
            raise RuntimeError(f"batch entry {raw.type}")

        text = raw["choices"][0]["message"]["content"]
        if brain.reply_schema is None:
            return text
        try:
            return json.loads(_strip_code_fence(text))
        except (json.JSONDecodeError, ValueError):
            return text


def _split_composite_id(batch_id: str) -> list[str]:
    return [part for part in batch_id.split(",") if part]


async def _content_text(content: Any) -> str:
    text = getattr(content, "text", None)
    if text is None:
        read = getattr(content, "read", None)
        if callable(read):
            text = read()
            if inspect.isawaitable(text):
                text = await text
        else:
            text = content
    if isinstance(text, bytes):
        return text.decode()
    return text if isinstance(text, str) else str(text)


def _error_type(error: Any) -> str:
    if isinstance(error, dict):
        value = error.get("type") or error.get("code") or error.get("message")
        return str(value or "error")
    return str(error)


register_batch_provider("openai", OpenAIBatchProvider)


__all__ = ["OpenAIBatchProvider"]
