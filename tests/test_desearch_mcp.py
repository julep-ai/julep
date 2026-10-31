from __future__ import annotations

import asyncio
from typing import Any

import pytest

from examples import desearch_mcp
from julep import deploy


def test_desearch_flow_calls_only_bounded_search() -> None:
    deployment = deploy(desearch_mcp.search, mcp_listings={
        "desearch": {"x-search": {
            "inputSchema": {
                "type": "object",
                "properties": {"query": {"type": "string"}, "count": {"type": "integer"}},
                "required": ["query"],
            },
        }},
    })
    calls = []

    async def fake(server, tool, value, key, principal, *args) -> Any:
        calls.append((server, tool, value))
        return {"data": [{"text": "A search result"}]}

    result = asyncio.run(deployment.adry_run("durable workflows", mcp_call=fake))
    assert calls == [("desearch", "x-search", {"query": "durable workflows", "count": 3})]
    assert result.value == {"data": [{"text": "A search result"}]}


def test_desearch_requires_key(monkeypatch) -> None:
    monkeypatch.delenv("DESEARCH_API_KEY", raising=False)
    with pytest.raises(ValueError, match="DESEARCH_API_KEY"):
        desearch_mcp.caller()


def test_desearch_binds_bearer_only_at_runtime(monkeypatch) -> None:
    monkeypatch.setenv("DESEARCH_API_KEY", "test-secret")
    captured = {}

    class FakeTransport:
        def __init__(self, servers, **kwargs):
            captured.update(servers=servers, **kwargs)

        async def call_tool(self, *args):
            return {}

    monkeypatch.setattr(desearch_mcp, "McpTransport", FakeTransport)
    desearch_mcp.caller()
    assert captured == {
        "servers": {"desearch": desearch_mcp.MCP_URL},
        "bearer_auth": "Bearer test-secret",
        "timeout_s": 60,
    }


def test_desearch_discovery_has_no_credentials(monkeypatch) -> None:
    monkeypatch.setenv("DESEARCH_API_KEY", "must-not-be-frozen")
    captured = {}
    sentinel = object()

    def fake_deploy(flow, **kwargs):
        captured.update(kwargs)
        assert flow is desearch_mcp.search
        return sentinel

    monkeypatch.setattr(desearch_mcp, "deploy", fake_deploy)
    assert desearch_mcp.build() is sentinel
    assert captured == {"mcp_servers": {"desearch": desearch_mcp.MCP_URL}}
