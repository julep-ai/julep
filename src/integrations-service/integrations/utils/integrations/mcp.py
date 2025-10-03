"""
MCP (Model Context Protocol) Integration for Julep

This module provides a native MCP client integration that allows Julep agents to:
1. Connect to MCP servers using HTTP or SSE (Server-Sent Events) transports
2. Dynamically discover available tools from the server
3. Execute tools with proper error handling and retry logic

The MCP integration enables Julep to interface with external tools and services
through a standardized protocol, making it extensible without hardcoding specific integrations.

Transport Options:
- HTTP: Standard request-response pattern using streamablehttp_client
- SSE: Server-Sent Events for streaming responses using dedicated sse_client

Note: Both transports require mcp>=1.8.0. The HTTP transport uses streamablehttp_client
which supports both regular HTTP and streaming responses. The SSE transport uses a
dedicated sse_client for proper event stream handling. Stdio transport has been
removed for security reasons.
"""

from __future__ import annotations

import asyncio
import contextlib
import importlib.metadata
import sys
from contextlib import AsyncExitStack
from types import TracebackType
from typing import Any

from beartype import beartype
from packaging import version
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import McpCallToolArguments, McpListToolsArguments, McpSetup
from ...models import McpListToolsOutput, McpToolCallOutput


def _ensure_mcp_available() -> None:
    """
    Check if the MCP SDK is installed and available.

    This is a runtime check to provide clear error messages if the MCP
    dependency is missing, rather than cryptic import errors later.
    """
    try:
        import mcp  # noqa: F401
    except Exception as e:  # pragma: no cover - import path validation
        msg = (
            "The 'mcp' Python package is required for MCP integration. "
            "Add 'mcp' to integrations-service dependencies and install it."
        )
        raise RuntimeError(msg) from e


# Module-level dynamic import for MCP clients with version check
try:
    mcp_version = importlib.metadata.version("mcp")
    if version.parse(mcp_version) < version.parse("1.8.0"):
        msg = (
            f"Your installed 'mcp' SDK version {mcp_version} does not support required transports. "
            f"Required: mcp>=1.8.0. Please update with: pip install 'mcp>=1.8.0'."
        )
        raise RuntimeError(msg)
    from mcp.client.sse import sse_client
    from mcp.client.streamable_http import streamablehttp_client
except ImportError as e:
    msg = (
        f"MCP transports require mcp>=1.8.0. Underlying import error: {e}. "
        f"Please update with: pip install 'mcp>=1.8.0'."
    )
    raise RuntimeError(msg) from e


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=16),
    reraise=True,
    stop=stop_after_attempt(5),
)
async def _connect_session(setup: McpSetup):
    """
    Create and initialize an MCP client session for the given setup.

    This function establishes connections to MCP servers using either:
    - streamablehttp_client for HTTP transport (standard request/response)
    - sse_client for SSE transport (Server-Sent Events streaming)

    The session management pattern ensures proper cleanup of resources.

    Args:
        setup: MCP setup configuration with transport type and connection details

    Returns:
        tuple: (session, aclose) where session is the active MCP client and
               aclose is an async cleanup function that must be called when done

    Raises:
        ValueError: If required configuration is missing or transport type is unknown
        RuntimeError: If connection to the MCP server fails
    """
    _ensure_mcp_available()

    from mcp import ClientSession

    transport = setup.transport

    if transport in ("http", "sse"):
        if not setup.http_url:
            msg = f"McpSetup.http_url is required for {transport} transport"
            raise ValueError(msg)

        headers = setup.http_headers or {}

        if transport == "sse":
            # SSE transport uses the dedicated sse_client for proper event stream handling
            headers = {
                **headers,
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache",
            }
            client_ctx = sse_client(str(setup.http_url), headers=headers)
        else:
            # HTTP transport uses streamablehttp_client
            client_ctx = streamablehttp_client(str(setup.http_url), headers=headers)

        stack = AsyncExitStack()
        closed = False
        stage = "transport"

        # AsyncExitStack keeps MCP client cleanup on the same task to avoid cancel-scope errors.
        try:
            result = await stack.enter_async_context(client_ctx)
            stage = "session"

            if isinstance(result, tuple):
                read, write = result[:2]
            else:
                read = result
                write = result

            session = await stack.enter_async_context(ClientSession(read, write))
            stage = "initialize"
            await session.initialize()
        except Exception as e:
            with contextlib.suppress(Exception):
                await stack.__aexit__(type(e), e, e.__traceback__)

            error_msg: str
            if stage == "transport":
                error_msg = (
                    f"Failed to connect to {transport.upper()} endpoint {setup.http_url}: {e}"
                )
            else:
                error_msg = f"Failed to establish {transport.upper()} connection to {setup.http_url}: {e}"
            raise RuntimeError(error_msg) from e

        async def aclose(
            exc_type: type[BaseException] | None = None,
            exc: BaseException | None = None,
            tb: TracebackType | None = None,
        ) -> None:
            nonlocal closed
            if closed:
                return
            closed = True
            if exc_type is None and exc is None and tb is None:
                exc_type, exc, tb = sys.exc_info()
            with contextlib.suppress(Exception):
                await stack.__aexit__(exc_type, exc, tb)

        return session, aclose

    msg = f"Unknown MCP transport: {transport}"
    raise ValueError(msg)


def _serialize_content_item(item: Any) -> dict[str, Any]:
    """
    Best-effort conversion of MCP content item to JSON-serializable dict.

    MCP servers can return various content types (text, images, structured data).
    This function normalizes them into a consistent format that can be serialized to JSON
    and passed back through our API. The fallback chain ensures we never lose data,
    even if it's in an unexpected format.
    """
    try:
        # Most MCP SDK objects support model_dump() for Pydantic-style serialization
        return item.model_dump()  # type: ignore[attr-defined]
    except Exception:
        try:
            # Fallback to dict conversion for simpler objects
            return dict(item)
        except Exception:
            # Last resort: string representation to preserve some information
            return {"repr": repr(item)}


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
    stop=stop_after_attempt(1),
)
async def list_tools(setup: McpSetup, arguments: McpListToolsArguments) -> McpListToolsOutput:
    """
    Discover available tools from an MCP server.

    This is the key innovation of MCP integration - instead of hardcoding tools,
    we dynamically discover what's available from any MCP server. This makes Julep
    infinitely extensible - just point it at a new MCP server and all its tools
    become available to your agents automatically.

    The retry logic handles transient network issues, especially important for
    remote HTTP-based MCP servers.

    Args:
        setup: MCP connection configuration (transport type, URL, headers)
        arguments: Arguments for listing tools (currently unused, reserved for future filtering)

    Returns:
        McpListToolsOutput: List of discovered tools with their names, descriptions, and schemas

    Raises:
        RuntimeError: If connection to the MCP server fails
        ValueError: If configuration is invalid
    """
    # AIDEV-NOTE: Debug logging for MCP tool discovery - remove in production
    session, aclose = await _connect_session(setup)
    try:
        # Query the MCP server for its tool catalog
        tools = await session.list_tools()
        # Transform MCP tool format to Julep's internal format
        # Extract the essential fields that Julep needs to present tools to agents
        out = [
            {
                "name": t.name,
                "description": getattr(t, "description", None),
                "input_schema": getattr(t, "inputSchema", None),  # JSON Schema for validation
            }
            for t in tools.tools
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
    """
    Execute a specific tool on an MCP server with the provided arguments.

    This allows Julep agents to call any tool exposed by an MCP server without
    knowing its implementation details. The tool could be running Python, Node.js,
    Rust, or any language - MCP abstracts that away.

    Key features:
    - Automatic retry on failure (network issues, timeouts)
    - Timeout support for long-running tools
    - Response normalization for consistent handling

    Args:
        setup: MCP connection configuration (transport type, URL, headers)
        arguments: Contains tool_name, arguments dict, and optional timeout_seconds

    Returns:
        McpToolCallOutput: Normalized tool response with:
            - text: Concatenated text content from the response
            - structured: Any structured data returned by the tool
            - content: Raw content items as JSON-serializable dicts
            - is_error: Whether the tool execution resulted in an error

    Raises:
        asyncio.TimeoutError: If the tool execution exceeds the specified timeout
        RuntimeError: If connection to the MCP server fails
        ValueError: If configuration is invalid
    """
    # AIDEV-NOTE: Debug logging for MCP tool execution - remove in production
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
            elif hasattr(item, "text") and item.text:
                text_parts.append(item.text)
            content_items.append(_serialize_content_item(item))

        return McpToolCallOutput(
            text="\n".join(text_parts) if text_parts else None,
            structured=structured,  # type: ignore[arg-type]
            content=content_items,
            is_error=bool(is_error),
        )
    finally:
        await aclose()
