#!/usr/bin/env python3
"""
Simple MCP SSE server for testing the SSE transport implementation.

This server implements the MCP protocol with SSE transport according to the
specification. It provides basic tools for testing purposes.

To run this server:
    python tests/test_mcp_sse_server.py

Then connect to it using:
    http://localhost:8001/sse
"""

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("MCP SSE test server starting on http://localhost:8001")
    yield
    logger.info("MCP SSE test server shutting down")


app = FastAPI(lifespan=lifespan)

# Add CORS middleware for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session storage for stateful operations
sessions = {}


async def sse_generator(request: Request) -> AsyncIterator[dict]:
    """Generate SSE events for the MCP protocol."""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {"initialized": False}

    # Send initial endpoint event to tell client where to POST messages
    yield {
        "event": "endpoint",
        "data": json.dumps({
            "url": f"http://localhost:8001/messages/{session_id}",
            "method": "POST",
        }),
    }

    # Keep connection alive with periodic pings
    try:
        while True:
            await asyncio.sleep(30)  # Send ping every 30 seconds
            if await request.is_disconnected():
                break
            yield {
                "event": "ping",
                "data": json.dumps({"timestamp": asyncio.get_event_loop().time()}),
            }
    finally:
        # Clean up session
        sessions.pop(session_id, None)
        logger.info(f"SSE connection closed for session {session_id}")


@app.get("/sse")
async def sse_endpoint(request: Request):
    """SSE endpoint for MCP protocol."""
    logger.info("New SSE connection established")
    return EventSourceResponse(sse_generator(request))


@app.post("/messages/{session_id}")
async def message_endpoint(session_id: str, request: Request):
    """Handle MCP JSON-RPC messages."""
    body = await request.json()
    logger.info(f"Received message for session {session_id}: {body}")

    method = body.get("method")
    id_ = body.get("id")

    # Handle MCP protocol methods
    if method == "initialize":
        sessions[session_id]["initialized"] = True
        return {
            "jsonrpc": "2.0",
            "id": id_,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "test-mcp-sse-server", "version": "1.0.0"},
            },
        }

    if method == "tools/list":
        if not sessions.get(session_id, {}).get("initialized"):
            return {
                "jsonrpc": "2.0",
                "id": id_,
                "error": {"code": -32002, "message": "Session not initialized"},
            }

        return {
            "jsonrpc": "2.0",
            "id": id_,
            "result": {
                "tools": [
                    {
                        "name": "test_echo",
                        "description": "Echo back the input message",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"message": {"type": "string"}},
                            "required": ["message"],
                        },
                    },
                    {
                        "name": "test_add",
                        "description": "Add two numbers",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
                            "required": ["a", "b"],
                        },
                    },
                ]
            },
        }

    if method == "tools/call":
        if not sessions.get(session_id, {}).get("initialized"):
            return {
                "jsonrpc": "2.0",
                "id": id_,
                "error": {"code": -32002, "message": "Session not initialized"},
            }

        params = body.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "test_echo":
            message = arguments.get("message", "")
            return {
                "jsonrpc": "2.0",
                "id": id_,
                "result": {"content": [{"type": "text", "text": f"Echo: {message}"}]},
            }

        if tool_name == "test_add":
            a = arguments.get("a", 0)
            b = arguments.get("b", 0)
            return {
                "jsonrpc": "2.0",
                "id": id_,
                "result": {"content": [{"type": "text", "text": f"Result: {a + b}"}]},
            }

        return {
            "jsonrpc": "2.0",
            "id": id_,
            "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
        }

    return {
        "jsonrpc": "2.0",
        "id": id_,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "server": "test-mcp-sse-server"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info",
    )
