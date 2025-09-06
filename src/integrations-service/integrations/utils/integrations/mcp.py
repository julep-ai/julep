from __future__ import annotations

import asyncio
from typing import Any

from beartype import beartype
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import McpCallToolArguments, McpListToolsArguments, McpSetup
from ...models import McpListToolsOutput, McpToolCallOutput


def _ensure_mcp_available() -> None:
    try:
        import mcp  # noqa: F401
    except Exception as e:  # pragma: no cover - import path validation
        msg = (
            "The 'mcp' Python package is required for MCP integration. "
            "Add 'mcp' to integrations-service dependencies and install it."
        )
        raise RuntimeError(msg) from e


async def _connect_session(setup: McpSetup):
    """Create and initialize an MCP client session for the given setup.

    Returns a 2-tuple (session, aclose) where `aclose` is an async callable that
    will close underlying transports/session when awaited.
    """
    _ensure_mcp_available()

    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    # `streamablehttp_client` is available for Streamable HTTP transport
    try:
        from mcp.client.streamable_http import streamablehttp_client
    except Exception as e:  # pragma: no cover - guard older SDKs
        streamablehttp_client = None  # type: ignore[assignment]
        stream_err = e
    else:
        stream_err = None

    transport = setup.transport

    if transport == "stdio":
        if not setup.command:
            msg = "McpSetup.command is required for stdio transport"
            raise ValueError(msg)

        server_params = StdioServerParameters(
            command=setup.command,
            args=setup.args or [],
            env=setup.env or None,
            cwd=setup.cwd or None,
        )

        stdio_ctx = stdio_client(server_params)
        read, write = await stdio_ctx.__aenter__()

        session = ClientSession(read, write)
        await session.initialize()

        async def aclose() -> None:
            try:
                await session.__aexit__(None, None, None)  # type: ignore[attr-defined]
            finally:
                await stdio_ctx.__aexit__(None, None, None)

        return session, aclose

    if transport == "http":
        if streamablehttp_client is None:
            msg = (
                "Your installed 'mcp' SDK does not provide streamable HTTP client "
                f"support. Underlying import error: {stream_err}"
            )
            raise RuntimeError(msg)

        if not setup.http_url:
            msg = "McpSetup.http_url is required for http transport"
            raise ValueError(msg)

        headers = setup.http_headers or {}
        http_ctx = streamablehttp_client(str(setup.http_url), headers=headers)
        read, write, _ = await http_ctx.__aenter__()

        session = ClientSession(read, write)
        await session.initialize()

        async def aclose() -> None:
            try:
                await session.__aexit__(None, None, None)  # type: ignore[attr-defined]
            finally:
                await http_ctx.__aexit__(None, None, None)

        return session, aclose

    msg = f"Unknown MCP transport: {transport}"
    raise ValueError(msg)


def _serialize_content_item(item: Any) -> dict[str, Any]:
    """Best-effort conversion of MCP content item to JSON-serializable dict."""
    try:
        # Most MCP SDK objects support model_dump()
        return item.model_dump()  # type: ignore[attr-defined]
    except Exception:
        try:
            return dict(item)
        except Exception:
            return {"repr": repr(item)}


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
    stop=stop_after_attempt(3),
)
async def list_tools(setup: McpSetup, arguments: McpListToolsArguments) -> McpListToolsOutput:
    """List tools from an MCP server using the provided setup."""
    session, aclose = await _connect_session(setup)
    try:
        tools = await session.list_tools()
        out = [
            {
                "name": t.name,
                "description": getattr(t, "description", None),
                "input_schema": getattr(t, "inputSchema", None),
            }
            for t in tools
        ]
        return McpListToolsOutput(tools=out)  # type: ignore[arg-type]
    finally:
        await aclose()


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
    stop=stop_after_attempt(3),
)
async def call_tool(setup: McpSetup, arguments: McpCallToolArguments) -> McpToolCallOutput:
    """Call a named tool on an MCP server and normalize the response."""
    session, aclose = await _connect_session(setup)
    try:
        # Enforce timeout per call if provided
        async def _invoke():
            return await session.call_tool(
                arguments.tool_name, arguments=arguments.arguments or {}
            )

        if arguments.timeout_seconds and arguments.timeout_seconds > 0:
            result = await asyncio.wait_for(_invoke(), timeout=arguments.timeout_seconds)
        else:
            result = await _invoke()

        # Normalize result content
        text_parts: list[str] = []
        content_items: list[dict[str, Any]] = []
        structured = getattr(result, "structuredContent", None)
        is_error = getattr(result, "isError", False)

        try:
            from mcp import types as mcp_types  # type: ignore
        except Exception:
            mcp_types = None  # type: ignore

        for item in getattr(result, "content", []) or []:
            # Extract text content if type info is available
            if mcp_types is not None and isinstance(
                item, getattr(mcp_types, "TextContent", ())
            ):
                text = getattr(item, "text", None)
                if text:
                    text_parts.append(text)
            content_items.append(_serialize_content_item(item))

        return McpToolCallOutput(
            text="\n".join(text_parts) if text_parts else None,
            structured=structured,  # type: ignore[arg-type]
            content=content_items,
            is_error=bool(is_error),
        )
    finally:
        await aclose()
