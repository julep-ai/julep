"""Experimental Anthropic Claude Managed Agents HTTP adapter.

This module targets the managed-agents beta HTTP surface directly. The protocol
shapes here were verified against live CMA (``managed-agents-2026-04-01``) on
2026-06-04: agent + environment + session creation, the SSE event stream, the
``agent.custom_tool_use`` / ``session.status_idle`` correlation, and the
``user.custom_tool_result`` reply. It remains experimental; request/stream
behavior is also covered with unit tests and ``httpx.MockTransport``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import AsyncIterator
from typing import Any, Optional

from .cma import CMAClient, CMAEvent, CMASession

logger = logging.getLogger(__name__)

ANTHROPIC_VERSION = "2023-06-01"
MANAGED_AGENTS_BETA = "managed-agents-2026-04-01"


def build_agent_params(
    agent: dict[str, Any],
    *,
    model: str,
    system: Optional[str],
) -> dict[str, Any]:
    """Build ``POST /v1/agents`` params without adding built-in toolsets."""
    body: dict[str, Any] = {
        "name": agent["name"],
        "model": agent.get("model") or model,
        "tools": list(agent.get("tools", [])),
    }
    selected_system = agent.get("system") if agent.get("system") is not None else system
    if selected_system is not None:
        body["system"] = selected_system
    return body


class _Normalizer:
    def __init__(self) -> None:
        self._pending: dict[str, tuple[str, Any]] = {}
        self._last_text: list[str] = []
        self._usage: Optional[dict[str, Any]] = None

    def feed(self, raw: dict[str, Any]) -> list[CMAEvent]:
        """Map one raw event dict to zero or more normalized CMA events."""
        self._track_usage(raw)
        event_type = raw.get("type")

        if event_type == "agent.custom_tool_use":
            event_id = raw.get("id")
            name = raw.get("name")
            if isinstance(event_id, str) and isinstance(name, str):
                self._pending[event_id] = (name, raw.get("input"))
            return []

        if event_type == "agent.message":
            self._last_text.extend(_content_text(raw.get("content")))
            return []

        if event_type == "session.status_idle":
            stop_reason = raw.get("stop_reason")
            if not isinstance(stop_reason, dict):
                return []
            reason_type = stop_reason.get("type")
            if reason_type == "requires_action":
                # A tool turn ends here; any narration so far belongs to this
                # intermediate turn, not the final answer. Reset so the terminal
                # output is only the model's post-last-tool-call text.
                self._last_text.clear()
                events: list[CMAEvent] = []
                event_ids = stop_reason.get("event_ids")
                if not isinstance(event_ids, list):
                    return []
                for event_id in event_ids:
                    if not isinstance(event_id, str):
                        continue
                    pending = self._pending.pop(event_id, None)
                    if pending is None:
                        logger.warning("requires_action references unknown event_id %r", event_id)
                        continue
                    name, inp = pending
                    events.append(
                        CMAEvent(
                            "custom_tool_use",
                            tool=name,
                            input=inp,
                            call_id=event_id,
                            usage=self._usage,
                        )
                    )
                return events
            if reason_type == "end_turn":
                output = "".join(self._last_text) or None
                return [CMAEvent("terminal", output=output, usage=self._usage)]
            return []

        if event_type == "session.error":
            error = raw.get("error")
            message = error.get("message") if isinstance(error, dict) else None
            return [CMAEvent("error", reason=message or "session error")]

        return []

    def _track_usage(self, raw: dict[str, Any]) -> None:
        usage = raw.get("usage")
        if isinstance(usage, dict):
            self._usage = usage
            return
        session = raw.get("session")
        if isinstance(session, dict) and isinstance(session.get("usage"), dict):
            self._usage = session["usage"]


def _content_text(content: Any) -> list[str]:
    if not isinstance(content, list):
        return []
    text: list[str] = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
            text.append(item["text"])
    return text


class AnthropicCMAClient(CMAClient):
    """Experimental Anthropic CMA HTTP client (live-verified protocol)."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        model: str,
        system: Optional[str] = None,
        base_url: str = "https://api.anthropic.com",
        transport: Any = None,
        timeout: float = 600.0,
        environment_id: Optional[str] = None,
        environment_name: str = "composable-agents",
    ) -> None:
        resolved_api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not resolved_api_key:
            raise ValueError("Anthropic CMA client requires api_key or ANTHROPIC_API_KEY")
        try:
            import httpx
        except ImportError as exc:
            raise ImportError(
                "AnthropicCMAClient requires httpx; install composable-agents[cma]."
            ) from exc

        self._httpx = httpx
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={
                "x-api-key": resolved_api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "anthropic-beta": MANAGED_AGENTS_BETA,
                "content-type": "application/json",
            },
            transport=transport,
            timeout=timeout,
        )
        self._model = model
        self._system = system
        self._environment_id = environment_id
        self._environment_name = environment_name
        self._env_lock = asyncio.Lock()

    async def create_session(
        self,
        *,
        agent: dict[str, Any],
        environment: Any,
        session_cid: str,
        input: Any = None,
    ) -> CMASession:
        del session_cid
        agent_response = await self._client.post(
            "/v1/agents",
            json=build_agent_params(agent, model=self._model, system=self._system),
        )
        agent_response.raise_for_status()
        agent_id = agent_response.json()["id"]

        environment_id = await self._resolve_environment_id(environment)

        session_response = await self._client.post(
            "/v1/sessions",
            json={
                "agent": {"type": "agent", "id": agent_id},
                "environment_id": environment_id,
            },
        )
        session_response.raise_for_status()
        session_id = session_response.json()["id"]
        return _AnthropicCMASession(self._client, session_id=session_id, input=input)

    async def _resolve_environment_id(self, environment: Any) -> str:
        """Resolve the ``environment_id`` the session API requires.

        ``str`` is an existing environment id; a ``dict`` is either a reference
        (``{"id": ...}``) or a create body (e.g. with ``packages``/``networking``);
        ``None`` lazily creates and reuses one shared environment for this client.
        """
        if isinstance(environment, str):
            return environment
        if isinstance(environment, dict):
            ref = environment.get("id")
            if isinstance(ref, str):
                return ref
            body = environment if environment.get("name") else {**environment, "name": self._environment_name}
            return await self._create_environment(body)
        async with self._env_lock:
            if self._environment_id is None:
                self._environment_id = await self._create_environment({"name": self._environment_name})
            return self._environment_id

    async def _create_environment(self, body: dict[str, Any]) -> str:
        response = await self._client.post("/v1/environments", json=body)
        response.raise_for_status()
        return str(response.json()["id"])


class _AnthropicCMASession(CMASession):
    """One experimental Anthropic CMA HTTP session."""

    def __init__(self, client: Any, *, session_id: str, input: Any = None) -> None:
        self._client = client
        self._session_id = session_id
        self._input = input
        self._started = False
        self._cancelled = False
        self.cancel_errors: list[Exception] = []

    async def events(self) -> AsyncIterator[CMAEvent]:
        normalizer = _Normalizer()
        async with self._client.stream(
            "GET",
            f"/v1/sessions/{self._session_id}/events/stream",
            params={"beta": "true"},
            headers={"accept": "text/event-stream"},
        ) as response:
            response.raise_for_status()
            try:
                await self._kickoff_once()
            except Exception as exc:
                logger.warning("Anthropic CMA kickoff failed", exc_info=True)
                yield CMAEvent("error", reason=f"kickoff failed: {exc}")
                return
            async for line in response.aiter_lines():
                raw = _parse_sse_data_line(line)
                if raw is None:
                    continue
                for event in normalizer.feed(raw):
                    yield event
                    if event.is_terminal or event.is_error:
                        return

    async def tool_result(self, call_id: str, result: Any) -> None:
        await self._post_event(
            {
                "type": "user.custom_tool_result",
                "custom_tool_use_id": call_id,
                "content": [{"type": "text", "text": _text_payload(result)}],
            }
        )

    async def tool_error(self, call_id: str, reason: str) -> None:
        await self._post_event(
            {
                "type": "user.custom_tool_result",
                "custom_tool_use_id": call_id,
                "content": [{"type": "text", "text": reason}],
                "is_error": True,
            }
        )

    async def cancel(self) -> None:
        if self._cancelled:
            return
        self._cancelled = True
        try:
            await self._post_event({"type": "user.interrupt"})
        except Exception as exc:  # best-effort teardown, but keep evidence
            self.cancel_errors.append(exc)
            logger.debug("Anthropic CMA cancel failed", exc_info=True)

    async def _kickoff_once(self) -> None:
        if self._started:
            return
        self._started = True
        if self._input is None:
            return
        await self._post_event(
            {
                "type": "user.message",
                "content": [{"type": "text", "text": _text_payload(self._input)}],
            }
        )

    async def _post_event(self, event: dict[str, Any]) -> None:
        response = await self._client.post(
            f"/v1/sessions/{self._session_id}/events",
            params={"beta": "true"},
            json={"events": [event]},
        )
        response.raise_for_status()


def _text_payload(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value)


def _parse_sse_data_line(line: str) -> Optional[dict[str, Any]]:
    stripped = line.strip()
    if not stripped.startswith("data:"):
        return None
    payload = stripped.removeprefix("data:").strip()
    if not payload or payload == "[DONE]":
        return None
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        logger.debug("skipping malformed CMA SSE data line", exc_info=True)
        return None
    return parsed if isinstance(parsed, dict) else None


__all__ = ["AnthropicCMAClient", "build_agent_params"]
