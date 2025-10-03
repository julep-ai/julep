#!/usr/bin/env python3
"""
A working MCP SSE server that properly implements the protocol.
Based on the FastMCP framework patterns.

To run:
    python tests/working_mcp_sse_server.py

Then connect at:
    http://localhost:8080/sse
"""

import asyncio
import logging
import os
from datetime import UTC, datetime
from typing import Any

from mcp import Tool
from mcp.server import Server
from mcp.server.sse import sse_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server instance
mcp_server = Server("working-mcp-sse")


@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="get_time",
            description="Get the current time",
            inputSchema={
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone (e.g., 'UTC', 'EST', 'PST')",
                        "default": "UTC",
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="echo",
            description="Echo back a message",
            inputSchema={
                "type": "object",
                "properties": {"message": {"type": "string", "description": "Message to echo"}},
                "required": ["message"],
            },
        ),
        Tool(
            name="calculate",
            description="Perform basic arithmetic",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                        "description": "Operation to perform",
                    },
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"},
                },
                "required": ["operation", "a", "b"],
            },
        ),
        Tool(
            name="list_files",
            description="List files in the current directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path (default: current)",
                        "default": ".",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "File pattern (e.g., '*.txt')",
                        "default": "*",
                    },
                },
                "required": [],
            },
        ),
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list:
    """Execute a tool"""
    logger.info(f"Tool called: {name} with args: {arguments}")

    if name == "get_time":
        tz_name = arguments.get("timezone", "UTC")
        current_time = datetime.now(tz=UTC).isoformat()
        return [{"type": "text", "text": f"Current time ({tz_name}): {current_time}"}]

    if name == "echo":
        message = arguments.get("message", "")
        return [{"type": "text", "text": f"Echo: {message}"}]

    if name == "calculate":
        operation = arguments.get("operation")
        a = arguments.get("a", 0)
        b = arguments.get("b", 0)

        result = 0
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b != 0:
                result = a / b
            else:
                return [{"type": "text", "text": "Error: Division by zero"}]

        return [{"type": "text", "text": f"Result of {a} {operation} {b} = {result}"}]

    if name == "list_files":
        import glob

        path = arguments.get("path", ".")
        pattern = arguments.get("pattern", "*")

        try:
            files = glob.glob(os.path.join(path, pattern))[:20]  # Limit to 20 files
            file_list = "\n".join(files) if files else "No files found"
            return [{"type": "text", "text": f"Files in {path}/{pattern}:\n{file_list}"}]
        except Exception as e:
            return [{"type": "text", "text": f"Error listing files: {e}"}]

    else:
        return [{"type": "text", "text": f"Unknown tool: {name}"}]


async def main():
    """Start the SSE server"""
    host = "0.0.0.0"
    port = 8080

    logger.info(f"Starting MCP SSE server on http://{host}:{port}/sse")
    logger.info("Tools available: get_time, echo, calculate, list_files")

    # Start SSE server using MCP SDK
    async with sse_server(mcp_server, host=host, port=port, endpoint="/sse"):
        logger.info(f"Server running. Connect at: http://localhost:{port}/sse")
        logger.info("Press Ctrl+C to stop")

        # Keep server running
        try:
            await asyncio.Future()  # Run forever until interrupted
        except KeyboardInterrupt:
            logger.info("Shutting down server...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped")
