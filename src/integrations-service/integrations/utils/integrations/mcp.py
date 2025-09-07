"""
MCP (Model Context Protocol) Integration for Julep

This module provides a native MCP client integration that allows Julep agents to:
1. Connect to any MCP server (stdio or HTTP transport)
2. Dynamically discover available tools from the server
3. Execute tools with proper error handling and retry logic

The MCP integration enables Julep to interface with external tools and services
through a standardized protocol, making it extensible without hardcoding specific integrations.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any

from beartype import beartype
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

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


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=16),
    reraise=True,
    stop=stop_after_attempt(5),
)
async def _connect_session(setup: McpSetup):
    """
    Create and initialize an MCP client session for the given setup.
    
    This function handles the complexity of establishing connections to MCP servers
    which can use different transport mechanisms (stdio for local processes, HTTP for remote).
    
    The dual transport supports:
    - stdio: For running MCP servers as local subprocesses (e.g., npx tools)  
    - HTTP: For connecting to remote MCP servers over the network
    
    The session management pattern ensures proper cleanup of resources.

    Returns:
        tuple: (session, aclose) where session is the active MCP client and
               aclose is an async cleanup function that must be called when done
    """
    _ensure_mcp_available()

    from mcp import ClientSession

    # Dynamic import handling for optional HTTP transport
    # Not all MCP SDK versions include HTTP support, so we gracefully handle its absence
    try:
        from mcp.client.streamable_http import streamablehttp_client
    except Exception as e:  # pragma: no cover - guard older SDKs
        streamablehttp_client = None  # type: ignore[assignment]
        stream_err = e
    else:
        stream_err = None

    transport = setup.transport

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
        # Add session management header for MCP session tracking
        session_id = uuid.uuid4().hex
        headers["Mcp-Session-Id"] = session_id
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
    stop=stop_after_attempt(3),
)
async def list_tools(setup: McpSetup, arguments: McpListToolsArguments) -> McpListToolsOutput:
    """
    Discover available tools from an MCP server.

    This is the key innovation of MCP integration -
    Instead of hardcoding tools, we dynamically discover what's available from any MCP server.
    This makes Julep infinitely extensible - just point it at a new MCP server and all
    its tools become available to your agents automatically.

    The retry logic handles transient network issues, especially important for
    remote HTTP-based MCP servers.

    Returns:
        McpListToolsOutput: List of discovered tools with their names, descriptions, and schemas
    """
    start_time = time.time()
    logger.info(f"MCP list_tools call started for server: {getattr(setup, 'http_url', 'unknown')}")
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
            for t in tools
        ]

        duration = time.time() - start_time
        logger.info(f"MCP list_tools call completed in {duration:.3f}s, discovered {len(out)} tools")
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

    This is where Julep agents can call any tool
    exposed by an MCP server without knowing its implementation details. The tool
    could be running Python, Node.js, Rust, or any language - MCP abstracts that away.

    Key features:
    - Automatic retry on failure (network issues, timeouts)
    - Timeout support for long-running tools
    - Response normalization for consistent handling

    Args:
        setup: MCP connection configuration (transport type, credentials)
        arguments: Tool name and parameters to pass

    Returns:
        McpToolCallOutput: Normalized tool response with text, structured data, and error info
    """
    start_time = time.time()
    logger.info(f"MCP call_tool started for server: {getattr(setup, 'http_url')} tool: {arguments.tool_name}")
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

        duration = time.time() - start_time
        logger.info(f"MCP call_tool completed in {duration:.3f}s for tool: {arguments.tool_name}, error: {is_error}")
        return McpToolCallOutput(
            text="\n".join(text_parts) if text_parts else None,
            structured=structured,  # type: ignore[arg-type]
            content=content_items,
            is_error=bool(is_error),
        )
    finally:
        await aclose()
