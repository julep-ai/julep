"""Shared fixtures/helpers for the test suite.

Async interpreter coroutines are driven with ``asyncio.run`` inside synchronous
tests, so the suite does not depend on a particular pytest-asyncio mode.
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any

from composable_agents.contracts import McpAnnotations
from composable_agents.freeze import McpServerSnapshot, McpSnapshot, McpToolSpec


def run(coro: Coroutine[Any, Any, Any]) -> Any:
    """Synchronously run a coroutine (helper for non-async test bodies)."""
    return asyncio.run(coro)


def read_snapshot(*tools: str, server: str = "srv", version: str = "1") -> McpSnapshot:
    """An MCP snapshot whose every tool is a read-only, idempotent hint."""
    ann = McpAnnotations(read_only_hint=True, idempotent_hint=True)
    return McpSnapshot(servers={
        server: McpServerSnapshot(
            server=server, version=version,
            tools={t: McpToolSpec(input_schema={}, annotations=ann) for t in tools},
        )
    })


def mixed_snapshot(server: str = "srv") -> McpSnapshot:
    """A snapshot with one read tool and one (write, non-idempotent) tool."""
    read = McpAnnotations(read_only_hint=True, idempotent_hint=True)
    write = McpAnnotations(read_only_hint=False)
    return McpSnapshot(servers={
        server: McpServerSnapshot(server=server, version="1", tools={
            "read": McpToolSpec(input_schema={}, annotations=read),
            "writer": McpToolSpec(input_schema={}, annotations=write),
        })
    })
