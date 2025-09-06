from types import SimpleNamespace

import pytest
from integrations.models import BaseProvider
from integrations.providers import available_providers
from integrations.utils.execute_integration import execute_integration


@pytest.mark.asyncio
async def test_mcp_provider_in_registry():
    assert "mcp" in available_providers
    provider = available_providers["mcp"]
    assert isinstance(provider, BaseProvider)
    methods = {m.method for m in provider.methods}
    assert {"list_tools", "call_tool"}.issubset(methods)


@pytest.mark.asyncio
async def test_mcp_list_tools_exec(monkeypatch):
    # Patch connector to avoid requiring real MCP server
    from integrations.utils.integrations import mcp as mcp_utils

    class FakeSession:
        async def initialize(self):  # pragma: no cover - not used
            pass

        async def list_tools(self):
            return [
                SimpleNamespace(
                    name="echo", description="Echo tool", inputSchema={"type": "object"}
                ),
                SimpleNamespace(name="ping", description="Ping tool", inputSchema=None),
            ]

        async def __aexit__(self, *_):  # pragma: no cover - not used
            return None

    async def fake_connect(_setup):
        async def aclose():
            return None

        return FakeSession(), aclose

    monkeypatch.setattr(mcp_utils, "_connect_session", fake_connect)

    # Build arguments via autogen classes at runtime
    from integrations.autogen.Tools import McpListToolsArguments, McpSetup

    setup = McpSetup(transport="stdio", command="fake-server")
    args = McpListToolsArguments()

    result = await execute_integration(
        provider="mcp",
        method="list_tools",
        setup=setup,
        arguments=args,
    )

    assert hasattr(result, "tools")
    assert len(result.tools) == 2
    assert {t.name for t in result.tools} == {"echo", "ping"}


@pytest.mark.asyncio
async def test_mcp_call_tool_exec(monkeypatch):
    # Patch connector and session.call_tool
    from integrations.utils.integrations import mcp as mcp_utils

    class FakeCallResult:
        def __init__(self):
            self.content = [SimpleNamespace(kind="text", text="hello"), {"json": True}]
            self.structuredContent = {"ok": True}
            self.isError = False

    class FakeSession:
        async def call_tool(self, tool_name: str, arguments):
            assert tool_name == "echo"
            return FakeCallResult()

    async def fake_connect(_setup):
        async def aclose():
            return None

        return FakeSession(), aclose

    monkeypatch.setattr(mcp_utils, "_connect_session", fake_connect)

    from integrations.autogen.Tools import McpCallToolArguments, McpSetup

    setup = McpSetup(transport="http", http_url="http://localhost:9999/mcp")
    args = McpCallToolArguments(tool_name="echo", arguments={"value": "hi"})

    result = await execute_integration(
        provider="mcp",
        method="call_tool",
        setup=setup,
        arguments=args,
    )

    # We expect normalized fields present
    assert result.is_error is False
    assert result.structured == {"ok": True}
    assert isinstance(result.content, list)
    assert len(result.content) >= 1
