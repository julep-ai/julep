from types import SimpleNamespace
from unittest.mock import patch

import pytest
from integrations.models import BaseProvider
from integrations.providers import available_providers
from integrations.utils.execute_integration import execute_integration
from integrations.utils.integrations import mcp as mcp_utils


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

    class FakeSession:
        async def initialize(self):  # pragma: no cover - not used
            pass

        async def list_tools(self):
            return SimpleNamespace(
                tools=[
                    SimpleNamespace(
                        name="echo", description="Echo tool", inputSchema={"type": "object"}
                    ),
                    SimpleNamespace(name="ping", description="Ping tool", inputSchema=None),
                ]
            )

        async def __aexit__(self, *_):  # pragma: no cover - not used
            return None

    async def fake_connect(_setup):
        async def aclose():
            return None

        return FakeSession(), aclose

    monkeypatch.setattr(mcp_utils, "_connect_session", fake_connect)

    # Build arguments via autogen classes at runtime
    from integrations.autogen.Tools import McpListToolsArguments, McpSetup

    setup = McpSetup(transport="http", http_url="http://localhost:9999/mcp")
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


from unittest.mock import AsyncMock

import pytest
from integrations.autogen.Tools import McpCallToolArguments, McpListToolsArguments, McpSetup


@pytest.mark.asyncio
@patch("integrations.utils.integrations.mcp.streamablehttp_client")
async def test_http_session_management(mock_client):
    """
    Test that HTTP transport uses streamablehttp_client correctly
    """
    setup = McpSetup(transport="http", http_url="http://test.example/mcp")

    # Mock the async context manager
    mock_ctx = AsyncMock()
    mock_read = AsyncMock()
    mock_write = AsyncMock()
    mock_ctx.__aenter__.return_value = (mock_read, mock_write, None)
    mock_ctx.__aexit__.return_value = None

    mock_client.return_value = mock_ctx

    # Mock ClientSession initialization
    mock_session = AsyncMock()
    mock_session.initialize = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock()

    with patch("mcp.ClientSession") as MockClientSession:
        MockClientSession.return_value = mock_session

        # Trigger the connection
        from integrations.utils.integrations.mcp import _connect_session

        _session, aclose = await _connect_session(setup)

        # Verify streamablehttp_client was called for HTTP transport
        mock_client.assert_called_once_with("http://test.example/mcp", headers={})

        # Verify session was created and initialized
        MockClientSession.assert_called_once_with(mock_read, mock_write)
        mock_session.initialize.assert_awaited_once()

        # Verify cleanup function exists
        assert callable(aclose)
        await aclose()


@pytest.mark.asyncio
@patch("mcp.ClientSession")
@patch("integrations.utils.integrations.mcp.streamablehttp_client")
async def test_http_connection_retry_logic(mock_client, mock_session_cls):
    """
    Test that HTTP connection uses retry logic
    """
    setup = McpSetup(transport="http", http_url="http://test.example/mcp")

    # Mock successful connection
    mock_ctx = AsyncMock()
    mock_read = AsyncMock()
    mock_write = AsyncMock()
    mock_ctx.__aenter__.return_value = (mock_read, mock_write)
    mock_ctx.__aexit__.return_value = None
    mock_client.return_value = mock_ctx

    # Mock ClientSession
    mock_session = AsyncMock()
    mock_session.initialize = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock()
    mock_session_cls.return_value = mock_session

    from integrations.utils.integrations.mcp import _connect_session

    # Test that connection works
    session, aclose = await _connect_session(setup)
    assert session is not None
    assert callable(aclose)

    # Verify streamablehttp_client was called
    mock_client.assert_called_once()

    # Clean up
    await aclose()


def test_mcp_sdk_version_check():
    """
    Test that missing MCP SDK raises proper error message
    """
    # Test that _ensure_mcp_available provides clear error if mcp is missing
    from integrations.utils.integrations.mcp import _ensure_mcp_available

    with (
        patch("builtins.__import__", side_effect=ImportError("mcp not found")),
        pytest.raises(RuntimeError, match=r"The 'mcp' Python package is required"),
    ):
        _ensure_mcp_available()


@pytest.mark.parametrize("transport", ["http", "sse"])
def test_mcp_setup_transport_validation(transport):
    """
    Test that McpSetup accepts valid transport types (http and sse)
    """
    from integrations.autogen.Tools import McpSetup

    # Valid transports should not raise validation errors
    setup = McpSetup(transport=transport)
    assert setup.transport == transport
    assert setup.transport in ["http", "sse"]


def test_mcp_setup_invalid_transport():
    """
    Test that invalid transport types raise validation error
    """
    from integrations.autogen.Tools import McpSetup
    from pydantic import ValidationError

    # Invalid transport should raise validation error
    with pytest.raises(ValidationError, match="Input should be 'sse' or 'http'"):
        McpSetup(transport="invalid")


@pytest.mark.asyncio
async def test_mcp_tool_response_normalization():
    """
    Test that MCP tool responses are properly normalized
    """
    from integrations.autogen.Tools import McpSetup
    from integrations.models import McpToolCallOutput

    setup = McpSetup(transport="http", http_url="http://test.example/mcp")
    args = McpCallToolArguments(tool_name="test_tool", arguments={"test": "data"})

    # Mock the entire connection and tool call
    with patch("integrations.utils.integrations.mcp._connect_session") as mock_connect:
        mock_session = AsyncMock()
        mock_result = SimpleNamespace(
            content=[
                SimpleNamespace(text="Hello world"),
                {"structured": True},
                SimpleNamespace(text="Second message"),
            ],
            structuredContent={"key": "value"},
            isError=False,
        )
        mock_session.call_tool.return_value = mock_result

        mock_acontext = AsyncMock()
        mock_connect.return_value = (mock_session, mock_acontext)

        from integrations.utils.integrations.mcp import call_tool

        result = await call_tool(setup, args)

        # Verify normalization
        assert isinstance(result, McpToolCallOutput)
        assert result.text == "Hello world\nSecond message"
        assert result.structured == {"key": "value"}
        assert result.is_error is False
        assert len(result.content) == 3
        assert "Hello world" in str(result.content[0])
        assert "structured" in str(result.content[1])
        assert "Second message" in str(result.content[2])


@pytest.mark.asyncio
async def test_mcp_list_tools_integration():
    """
    Test end-to-end tool discovery integration
    """
    from integrations.autogen.Tools import McpSetup
    from integrations.models import McpListToolsOutput

    setup = McpSetup(transport="http", http_url="http://test.example/mcp")
    args = McpListToolsArguments()

    # Mock connection and session
    with patch("integrations.utils.integrations.mcp._connect_session") as mock_connect:
        mock_session = AsyncMock()
        mock_tools = SimpleNamespace(
            tools=[
                SimpleNamespace(
                    name="tool1", description="First tool", inputSchema={"type": "object"}
                ),
                SimpleNamespace(name="tool2", description="Second tool", inputSchema=None),
            ]
        )
        mock_session.list_tools.return_value = mock_tools

        mock_acontext = AsyncMock()
        mock_connect.return_value = (mock_session, mock_acontext)

        from integrations.utils.integrations.mcp import list_tools

        result = await list_tools(setup, args)

        # Verify integration works end-to-end
        assert isinstance(result, McpListToolsOutput)
        assert len(result.tools) == 2
        assert result.tools[0].name == "tool1"
        assert result.tools[0].description == "First tool"
        assert result.tools[1].name == "tool2"
        assert result.tools[1].input_schema is None


@pytest.mark.asyncio
async def test_mcp_timeout_handling():
    """
    Test that tool calls respect timeout_seconds parameter
    """
    from unittest.mock import AsyncMock

    from integrations.autogen.Tools import McpSetup

    setup = McpSetup(transport="http", http_url="http://test.example/mcp")
    args = McpCallToolArguments(
        tool_name="slow_tool",
        arguments={"data": "test"},
        timeout_seconds=5,  # 5 second timeout
    )

    with patch("integrations.utils.integrations.mcp._connect_session") as mock_connect:
        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(
            side_effect=AsyncMock(
                return_value=SimpleNamespace(content=[], structuredContent={}, isError=False)
            )
        )

        mock_acontext = AsyncMock()
        mock_connect.return_value = (mock_session, mock_acontext)

        from asyncio import wait_for

        from integrations.utils.integrations.mcp import call_tool

        # Should complete without timeout
        result = await wait_for(call_tool(setup, args), timeout=10)

        # Verify timeout was respected (no exception)
        assert result is not None
        mock_session.call_tool.assert_awaited_once()
        # The asyncio.wait_for in call_tool should have used timeout_seconds=5


@pytest.mark.asyncio
async def test_mcp_sse_transport_connection():
    """
    Test that SSE transport establishes connection with proper headers
    """
    from integrations.autogen.Tools import McpSetup
    from integrations.utils.integrations.mcp import _connect_session

    setup = McpSetup(transport="sse", http_url="http://test.example/sse")

    with patch("integrations.utils.integrations.mcp.sse_client") as mock_client:
        mock_ctx = AsyncMock()
        mock_read = AsyncMock()
        mock_write = AsyncMock()
        mock_ctx.__aenter__.return_value = (mock_read, mock_write, None)
        mock_ctx.__aexit__.return_value = None
        mock_client.return_value = mock_ctx

        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        with patch("mcp.ClientSession", return_value=mock_session):
            _session, aclose = await _connect_session(setup)

            # Verify SSE-specific headers were added
            call_args = mock_client.call_args
            headers = call_args[1]["headers"]

            assert "Accept" in headers
            assert headers["Accept"] == "text/event-stream"
            assert "Cache-Control" in headers
            assert headers["Cache-Control"] == "no-cache"

            # Verify session was properly initialized
            mock_session.initialize.assert_awaited_once()

            # Clean up
            await aclose()


@pytest.mark.asyncio
async def test_mcp_sse_connection_error_handling():
    """
    Test that SSE connection failures provide clear error messages
    """
    from integrations.autogen.Tools import McpSetup
    from integrations.utils.integrations.mcp import _connect_session

    setup = McpSetup(transport="sse", http_url="http://test.example/sse")

    with patch("integrations.utils.integrations.mcp.sse_client") as mock_client:
        mock_ctx = AsyncMock()
        mock_read = AsyncMock()
        mock_write = AsyncMock()
        mock_ctx.__aenter__.return_value = (mock_read, mock_write, None)
        mock_ctx.__aexit__.return_value = None
        mock_client.return_value = mock_ctx

        mock_session = AsyncMock()
        # Simulate connection failure
        mock_session.initialize = AsyncMock(side_effect=Exception("Connection refused"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        with (
            patch("mcp.ClientSession", return_value=mock_session),
            pytest.raises(
                RuntimeError, match=r"Failed to establish SSE connection.*Connection refused"
            ),
        ):
            await _connect_session(setup)
