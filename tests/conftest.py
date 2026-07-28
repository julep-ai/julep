"""Shared fixtures/helpers for the test suite.

Async interpreter coroutines are driven with ``asyncio.run`` inside synchronous
tests, so the suite does not depend on a particular pytest-asyncio mode.
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine, Iterator
from typing import Any

import pytest

from julep.contracts import McpAnnotations
from julep.freeze import McpServerSnapshot, McpSnapshot, McpToolSpec
from julep.registry import DEFAULT_REGISTRY

# AIDEV-NOTE: DEFAULT_REGISTRY is process-global, so this autouse fixture makes
# the suite order-independent. Registrations performed during module import or
# collection survive because they happen before each snapshot; only intra-test
# registrations are rolled back. Each test must register the registry state it
# needs rather than relying on state left by another test.
_REGISTRY_STATE_ATTRS = (
    "reasoners",
    "pures",
    "renderers",
    "renderer_declarations",
    "tool_expectations",
    "scoped_tool_fallbacks",
    "agent_specs",
)


@pytest.fixture(autouse=True)
def isolate_default_registry() -> Iterator[None]:
    """Restore ``DEFAULT_REGISTRY`` around every test (global-state hygiene)."""
    saved = {attr: getattr(DEFAULT_REGISTRY, attr).copy() for attr in _REGISTRY_STATE_ATTRS}
    try:
        yield
    finally:
        for attr, value in saved.items():
            container = getattr(DEFAULT_REGISTRY, attr)
            container.clear()
            container.update(value)


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
