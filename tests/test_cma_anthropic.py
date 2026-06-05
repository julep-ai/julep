"""Anthropic CMA HTTP adapter tests."""

from __future__ import annotations

import json
import logging

import httpx
import pytest

from composable_agents.execution.cma import CMAEvent
from composable_agents.execution.cma_anthropic import (
    AnthropicCMAClient,
    _Normalizer,
    _parse_sse_data_line,
    build_agent_params,
)
from conftest import run


def test_build_agent_params_prefers_agent_model_and_system_and_never_adds_toolset() -> None:
    agent = {
        "name": "controller",
        "model": "agent-model",
        "system": "agent system",
        "tools": [
            {
                "type": "custom",
                "name": "search",
                "description": "Search",
                "input_schema": {"type": "object"},
            }
        ],
    }

    body = build_agent_params(agent, model="default-model", system="default system")

    assert body == {
        "name": "controller",
        "model": "agent-model",
        "system": "agent system",
        "tools": agent["tools"],
    }
    assert "agent_toolset_20260401" not in json.dumps(body)


def test_normalizer_buffers_tool_use_until_requires_action_then_emits_terminal() -> None:
    normalizer = _Normalizer()
    raw_events = [
        {
            "type": "agent.custom_tool_use",
            "id": "evt_tool",
            "name": "search",
            "input": {"q": "hello"},
            "usage": {"input_tokens": 3},
        },
        {
            "type": "session.status_idle",
            "stop_reason": {"type": "requires_action", "event_ids": ["evt_tool"]},
        },
        {"type": "agent.message", "content": [{"type": "text", "text": "done"}]},
        {
            "type": "session.status_idle",
            "stop_reason": {"type": "end_turn"},
            "usage": {"input_tokens": 3, "output_tokens": 2},
        },
    ]

    emitted = [event for raw in raw_events for event in normalizer.feed(raw)]

    assert emitted == [
        CMAEvent(
            "custom_tool_use",
            tool="search",
            input={"q": "hello"},
            call_id="evt_tool",
            usage={"input_tokens": 3},
        ),
        CMAEvent(
            "terminal",
            output="done",
            usage={"input_tokens": 3, "output_tokens": 2},
        ),
    ]


def test_normalizer_maps_session_error() -> None:
    emitted = _Normalizer().feed({"type": "session.error", "error": {"message": "bad"}})

    assert emitted == [CMAEvent("error", reason="bad")]


def test_normalizer_logs_unknown_requires_action_event_id(
    caplog: pytest.LogCaptureFixture,
) -> None:
    normalizer = _Normalizer()

    with caplog.at_level(logging.WARNING, logger="composable_agents.execution.cma_anthropic"):
        emitted = normalizer.feed(
            {
                "type": "session.status_idle",
                "stop_reason": {"type": "requires_action", "event_ids": ["evt_missing"]},
            }
        )

    assert emitted == []
    assert "unknown event_id 'evt_missing'" in caplog.text


def test_parse_sse_data_line_skips_malformed_json() -> None:
    assert _parse_sse_data_line('data: {"truncated":') is None


def test_anthropic_cma_client_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        AnthropicCMAClient(model="claude-sonnet")


def test_anthropic_cma_client_create_events_and_tool_posts() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.headers["x-api-key"] == "test-key"
        assert request.headers["anthropic-version"] == "2023-06-01"
        assert request.headers["anthropic-beta"] == "managed-agents-2026-04-01"
        assert request.headers["content-type"] == "application/json"

        if request.method == "POST" and request.url.path == "/v1/agents":
            assert json.loads(request.content) == {
                "name": "controller",
                "model": "claude-sonnet",
                "system": "system prompt",
                "tools": [
                    {
                        "type": "custom",
                        "name": "search",
                        "description": "",
                        "input_schema": {"type": "object"},
                    }
                ],
            }
            return httpx.Response(200, json={"id": "agnt_01"})
        if request.method == "POST" and request.url.path == "/v1/sessions":
            assert json.loads(request.content) == {
                "agent_id": "agnt_01",
                "environment": {"kind": "test"},
            }
            return httpx.Response(200, json={"id": "sesn_01", "usage": {"input_tokens": 1}})
        if request.method == "GET" and request.url.path == "/v1/sessions/sesn_01/events/stream":
            assert request.url.params["beta"] == "true"
            assert request.headers["accept"] == "text/event-stream"
            stream = "\n".join(
                [
                    'data: {"type":"agent.custom_tool_use","id":"evt_1","name":"search","input":{"q":"x"}}',
                    'data: {"type":"session.status_idle","stop_reason":{"type":"requires_action","event_ids":["evt_1"]}}',
                    'data: {"type":"agent.message","content":[{"type":"text","text":"ok"}]}',
                    'data: {"type":"session.status_idle","stop_reason":{"type":"end_turn"}}',
                    "",
                ]
            )
            return httpx.Response(200, content=stream.encode())
        if request.method == "POST" and request.url.path == "/v1/sessions/sesn_01/events":
            assert request.url.params["beta"] == "true"
            return httpx.Response(200, json={"ok": True})
        raise AssertionError(f"unexpected request {request.method} {request.url}")

    async def scenario() -> list[CMAEvent]:
        client = AnthropicCMAClient(
            api_key="test-key",
            model="claude-sonnet",
            system="system prompt",
            transport=httpx.MockTransport(handler),
        )
        session = await client.create_session(
            agent={
                "name": "controller",
                "tools": [
                    {
                        "type": "custom",
                        "name": "search",
                        "description": "",
                        "input_schema": {"type": "object"},
                    }
                ],
            },
            environment={"kind": "test"},
            session_cid="cid-1",
            input={"question": "hello"},
        )
        events: list[CMAEvent] = []
        async for event in session.events():
            events.append(event)
            if event.is_custom_tool_use:
                await session.tool_result(event.call_id or "", {"hit": True})
        await session.tool_error("evt_err", "failed")
        await session.cancel()
        await session.cancel()
        return events

    events = run(scenario())

    assert [(event.kind, event.tool, event.call_id, event.output) for event in events] == [
        ("custom_tool_use", "search", "evt_1", None),
        ("terminal", None, None, "ok"),
    ]
    kickoff_body = json.loads(requests[3].content)
    assert kickoff_body == {
        "events": [
            {
                "type": "user.message",
                "content": [{"type": "text", "text": '{"question": "hello"}'}],
            }
        ]
    }
    tool_result_body = json.loads(requests[4].content)
    assert tool_result_body["events"][0]["type"] == "user.custom_tool_result"
    assert tool_result_body["events"][0]["custom_tool_use_id"] == "evt_1"
    assert tool_result_body["events"][0]["content"][0]["text"] == '{"hit": true}'
    tool_error_body = json.loads(requests[5].content)
    assert tool_error_body["events"][0]["is_error"] is True
    assert tool_error_body["events"][0]["custom_tool_use_id"] == "evt_err"
    cancel_bodies = [
        json.loads(request.content)
        for request in requests
        if request.method == "POST"
        and request.url.path == "/v1/sessions/sesn_01/events"
        and json.loads(request.content)["events"][0]["type"] == "user.interrupt"
    ]
    assert cancel_bodies == [{"events": [{"type": "user.interrupt"}]}]


def test_anthropic_cma_session_events_yields_error_when_kickoff_post_fails() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path == "/v1/agents":
            return httpx.Response(200, json={"id": "agnt_01"})
        if request.method == "POST" and request.url.path == "/v1/sessions":
            return httpx.Response(200, json={"id": "sesn_01"})
        if request.method == "GET" and request.url.path == "/v1/sessions/sesn_01/events/stream":
            return httpx.Response(200, content=b"")
        if request.method == "POST" and request.url.path == "/v1/sessions/sesn_01/events":
            return httpx.Response(500, json={"error": {"message": "boom"}})
        raise AssertionError(f"unexpected request {request.method} {request.url}")

    async def scenario() -> list[CMAEvent]:
        client = AnthropicCMAClient(
            api_key="test-key",
            model="claude-sonnet",
            transport=httpx.MockTransport(handler),
        )
        session = await client.create_session(
            agent={"name": "controller", "tools": []},
            environment=None,
            session_cid="cid-1",
            input="hello",
        )
        return [event async for event in session.events()]

    events = run(scenario())

    assert len(events) == 1
    assert events[0].kind == "error"
    assert "kickoff failed" in (events[0].reason or "")
