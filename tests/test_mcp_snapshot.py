from __future__ import annotations

import asyncio
import builtins
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

import pytest

import julep.mcp_snapshot as mcp_snapshot


class _Dumpable:
    def __init__(self, value: dict[str, Any]) -> None:
        self.value = value

    def model_dump(self, **_kwargs: Any) -> dict[str, Any]:
        return dict(self.value)


@dataclass
class _State:
    pages: dict[str | None, Any]
    protocol: str = "2025-03-26"
    server_version: str = "2.4.0"
    initialize_delay: float = 0.0
    list_delay: float = 0.0
    transport_error: Exception | None = None
    wrap_body_errors: bool = False
    cursors: list[str | None] = field(default_factory=list)
    transport_calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    http_client_kwargs: dict[str, Any] | None = None


class _FakeSession:
    def __init__(self, read: _State, _write: object) -> None:
        self.state = read

    async def __aenter__(self) -> _FakeSession:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def initialize(self) -> Any:
        await asyncio.sleep(self.state.initialize_delay)
        return SimpleNamespace(
            protocolVersion=self.state.protocol,
            serverInfo=SimpleNamespace(version=self.state.server_version),
        )

    async def list_tools(self, *, cursor: str | None = None) -> Any:
        self.state.cursors.append(cursor)
        await asyncio.sleep(self.state.list_delay)
        return self.state.pages[cursor]


def _sdk(state: _State, *, modern: bool = False) -> mcp_snapshot._McpSdk:
    @asynccontextmanager
    async def stream(url: str, **kwargs: Any) -> Any:
        state.transport_calls.append((url, kwargs))
        if state.transport_error is not None:
            raise state.transport_error
        try:
            yield state, object(), lambda: None
        except Exception as exc:
            if state.wrap_body_errors:
                exception_group = vars(builtins)["ExceptionGroup"]
                raise exception_group("transport", [exc]) from None
            raise

    class FakeHttpx:
        class Timeout:
            def __init__(self, value: float) -> None:
                self.value = value

        class AsyncClient:
            def __init__(self, **kwargs: Any) -> None:
                state.http_client_kwargs = kwargs

            async def __aenter__(self) -> FakeHttpx.AsyncClient:
                return self

            async def __aexit__(self, *_args: object) -> None:
                return None

    if not modern:
        return mcp_snapshot._McpSdk(
            client_session=_FakeSession,
            stream_client=stream,
            modern_stream=False,
            httpx=FakeHttpx,
        )

    return mcp_snapshot._McpSdk(
        client_session=_FakeSession,
        stream_client=stream,
        modern_stream=True,
        httpx=FakeHttpx,
    )


def _tool(name: str) -> Any:
    return SimpleNamespace(
        name=name,
        inputSchema={"type": "object", "properties": {"query": {"type": "string"}}},
        annotations=_Dumpable({"readOnlyHint": True, "idempotentHint": True}),
        outputSchema={"type": "object"},
    )


def _page(*tools: Any, cursor: str | None = None) -> Any:
    return SimpleNamespace(tools=list(tools), nextCursor=cursor)


def test_fetch_listings_paginates_and_passes_legacy_auth_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _State(
        pages={
            None: _page(_tool("search"), cursor="page-2"),
            "page-2": _page(_tool("read")),
        }
    )
    monkeypatch.setattr(mcp_snapshot, "_load_sdk", lambda: _sdk(state))

    listings = mcp_snapshot.fetch_listings(
        {
            "memory": {
                "url": "https://mcp.example.test/mcp",
                "headers": {"X-Tenant": "acme"},
                "auth": "secret-token",
                "version": "2.4.0",
            }
        },
        allowlist={"https://MCP.EXAMPLE.test:443/mcp/"},
    )

    assert state.cursors == [None, "page-2"]
    assert list(listings["memory"]) == ["search", "read"]
    assert listings["memory"]["search"] == {
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
        },
        "annotations": {"readOnlyHint": True, "idempotentHint": True},
        "outputSchema": {"type": "object"},
    }
    assert state.transport_calls[0][0] == "https://mcp.example.test/mcp"
    transport_options = state.transport_calls[0][1]
    assert transport_options["headers"] == {
        "X-Tenant": "acme",
        "Authorization": "Bearer secret-token",
    }
    assert transport_options["timeout"] == 10.0
    assert transport_options["sse_read_timeout"] == 10.0
    factory = transport_options["httpx_client_factory"]
    client = factory(headers={}, timeout="timeout", auth=None)
    assert client is not None
    assert state.http_client_kwargs is not None
    assert state.http_client_kwargs["follow_redirects"] is False


def test_snapshot_servers_pins_protocol_and_server_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _State(pages={None: _page(_tool("search"))})
    monkeypatch.setattr(mcp_snapshot, "_load_sdk", lambda: _sdk(state, modern=True))

    snapshot = mcp_snapshot.snapshot_servers(
        {"memory": {"url": "https://mcp.example.test/mcp"}}
    )

    server = snapshot.servers["memory"]
    assert server.version == '{"protocol":"2025-03-26","server":"2.4.0"}'
    assert server.tools["search"].input_schema["type"] == "object"
    assert server.tools["search"].annotations.read_only_hint is True
    assert state.http_client_kwargs is not None
    assert state.http_client_kwargs["headers"] == {}
    assert state.http_client_kwargs["timeout"].value == 10.0
    assert state.http_client_kwargs["follow_redirects"] is False
    assert list(state.transport_calls[0][1]) == ["http_client"]


def test_duplicate_tool_names_across_pages_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _State(
        pages={
            None: _page(_tool("search"), cursor="again"),
            "again": _page(_tool("search")),
        },
        wrap_body_errors=True,
    )
    monkeypatch.setattr(mcp_snapshot, "_load_sdk", lambda: _sdk(state))

    with pytest.raises(mcp_snapshot.McpSnapshotError, match="duplicate tool name 'search'"):
        mcp_snapshot.fetch_listings({"memory": "https://mcp.example.test/mcp"})


def test_allowlist_is_enforced_before_loading_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    def should_not_load() -> mcp_snapshot._McpSdk:
        raise AssertionError("SDK should not load for a rejected URL")

    monkeypatch.setattr(mcp_snapshot, "_load_sdk", should_not_load)
    configured = "https://private.example.test/mcp?token=secret"

    with pytest.raises(mcp_snapshot.McpSnapshotError) as raised:
        mcp_snapshot.fetch_listings(
            {"private": configured}, allowlist={"https://allowed.example.test/mcp"}
        )

    assert "allowlist" in str(raised.value)
    assert configured not in str(raised.value)
    assert "token=secret" not in str(raised.value)


def test_version_pin_mismatch_fails_without_reporting_versions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _State(pages={None: _page()}, server_version="server-secret-version")
    monkeypatch.setattr(mcp_snapshot, "_load_sdk", lambda: _sdk(state))

    with pytest.raises(mcp_snapshot.McpSnapshotError) as raised:
        mcp_snapshot.fetch_listings(
            {
                "memory": {
                    "url": "https://mcp.example.test/mcp",
                    "version": "expected-secret-version",
                }
            }
        )

    message = str(raised.value)
    assert "version pin" in message
    assert "server-secret-version" not in message
    assert "expected-secret-version" not in message


def test_per_request_timeout_identifies_only_server_and_stage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _State(pages={None: _page()}, list_delay=0.05)
    monkeypatch.setattr(mcp_snapshot, "_load_sdk", lambda: _sdk(state))

    with pytest.raises(mcp_snapshot.McpSnapshotError) as raised:
        mcp_snapshot.fetch_listings(
            {"memory": "https://mcp.example.test/mcp"},
            timeout_s=0.005,
            total_timeout_s=1.0,
        )

    assert str(raised.value) == "MCP snapshot timed out for server 'memory' during tools/list"


def test_total_timeout_bounds_the_whole_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _State(pages={None: _page()}, initialize_delay=0.05)
    monkeypatch.setattr(mcp_snapshot, "_load_sdk", lambda: _sdk(state))

    with pytest.raises(mcp_snapshot.McpSnapshotError, match="before all servers completed"):
        mcp_snapshot.fetch_listings(
            {"memory": "https://mcp.example.test/mcp"},
            timeout_s=1.0,
            total_timeout_s=0.005,
        )


def test_transport_failure_is_sanitized(monkeypatch: pytest.MonkeyPatch) -> None:
    endpoint = "https://mcp.example.test/mcp?access_token=url-secret"
    token = "header-secret"
    state = _State(
        pages={None: _page()},
        transport_error=RuntimeError(f"failed at {endpoint} with Bearer {token}"),
    )
    monkeypatch.setattr(mcp_snapshot, "_load_sdk", lambda: _sdk(state))

    with pytest.raises(mcp_snapshot.McpSnapshotError) as raised:
        mcp_snapshot.fetch_listings(
            {"memory": {"url": endpoint, "auth": token}},
        )

    assert str(raised.value) == "MCP snapshot failed for server 'memory' during connection"
    assert endpoint not in str(raised.value)
    assert token not in str(raised.value)
    assert raised.value.__cause__ is None


def test_missing_sdk_has_clear_extra_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(_name: str) -> Any:
        raise ImportError("missing")

    monkeypatch.setattr(mcp_snapshot, "import_module", missing)

    with pytest.raises(ImportError, match=r"julep\[mcp\]"):
        mcp_snapshot.fetch_listings({"memory": "https://mcp.example.test/mcp"})


def test_empty_server_set_does_not_require_sdk() -> None:
    assert mcp_snapshot.fetch_listings({}) == {}
