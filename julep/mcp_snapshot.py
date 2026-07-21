"""Live MCP ``tools/list`` snapshots for deploy-time freezing.

The MCP SDK stays optional and is imported only when a live snapshot is requested.
Public helpers are synchronous because deployment and the CLI are synchronous authoring
surfaces; the transport itself uses the SDK's async client.
"""

from __future__ import annotations

import asyncio
import builtins
import json
import re
from collections.abc import AsyncIterator, Collection, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from importlib import import_module
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit, urlunsplit

if TYPE_CHECKING:
    from .freeze import McpSnapshot


DEFAULT_TIMEOUT_S = 10.0
DEFAULT_TOTAL_TIMEOUT_S = 60.0


class McpSnapshotError(ValueError):
    """A sanitized failure while collecting an MCP snapshot."""


@dataclass(frozen=True)
class _ServerConfig:
    server: str
    url: str
    headers: dict[str, str]
    version: str | None


@dataclass(frozen=True)
class _FetchedServer:
    tools: dict[str, dict[str, Any]]
    version: str


@dataclass(frozen=True)
class _McpSdk:
    client_session: Any
    stream_client: Any
    modern_stream: bool
    httpx: Any


def _load_sdk() -> _McpSdk:
    try:
        mcp = import_module("mcp")
        transport = import_module("mcp.client.streamable_http")
        httpx = import_module("httpx")
        modern_stream = getattr(transport, "streamable_http_client", None)
        if modern_stream is not None:
            stream_client = modern_stream
            is_modern = True
        else:
            stream_client = vars(transport)["streamablehttp_client"]
            is_modern = False
        client_session = vars(mcp)["ClientSession"]
    except (AttributeError, ImportError, KeyError):
        raise ImportError(
            "MCP snapshot support requires the 'mcp' extra; "
            "install it with `pip install 'julep[mcp]'`."
        ) from None
    return _McpSdk(
        client_session=client_session,
        stream_client=stream_client,
        modern_stream=is_modern,
        httpx=httpx,
    )


def _field(value: Any, *names: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        for name in names:
            if name in value:
                return value[name]
        return default
    for name in names:
        if hasattr(value, name):
            return getattr(value, name)
    return default


def _canonical_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("invalid endpoint") from exc
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise ValueError("invalid endpoint")
    scheme = parsed.scheme.lower()
    host = parsed.hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    if port is not None and not (
        (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    ):
        host = f"{host}:{port}"
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((scheme, host, path, parsed.query, ""))


def _authorization_value(token: str) -> str:
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*\s+\S", token):
        return token
    return f"Bearer {token}"


def _auth_token(auth: str | Mapping[str, str] | None, server: str) -> str | None:
    if auth is None or isinstance(auth, str):
        return auth
    token = auth.get(server)
    if token is not None and not isinstance(token, str):
        raise McpSnapshotError(f"invalid auth configuration for MCP server {server!r}")
    return token


def _server_config(
    server: str,
    raw: Any,
    *,
    auth: str | Mapping[str, str] | None,
    allowed_urls: frozenset[str] | None,
) -> _ServerConfig:
    if isinstance(raw, str):
        url_raw: Any = raw
        headers_raw: Any = {}
        server_auth: Any = None
        version_raw: Any = None
    else:
        url_raw = _field(raw, "url")
        headers_raw = _field(raw, "headers", default={})
        server_auth = _field(raw, "auth")
        version_raw = _field(raw, "version")

    if not isinstance(url_raw, str):
        raise McpSnapshotError(f"invalid URL configuration for MCP server {server!r}")
    try:
        canonical_url = _canonical_url(url_raw)
    except ValueError:
        raise McpSnapshotError(f"invalid URL configuration for MCP server {server!r}") from None
    if allowed_urls is not None and canonical_url not in allowed_urls:
        raise McpSnapshotError(f"MCP server {server!r} is not permitted by the URL allowlist")

    if not isinstance(headers_raw, Mapping):
        raise McpSnapshotError(f"invalid headers configuration for MCP server {server!r}")
    headers: dict[str, str] = {}
    for key, value in headers_raw.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise McpSnapshotError(f"invalid headers configuration for MCP server {server!r}")
        headers[key] = value

    if server_auth is not None and not isinstance(server_auth, str):
        raise McpSnapshotError(f"invalid auth configuration for MCP server {server!r}")
    token = server_auth or _auth_token(auth, server)
    if token and not any(key.lower() == "authorization" for key in headers):
        headers["Authorization"] = _authorization_value(token)

    if version_raw is not None and not isinstance(version_raw, str):
        raise McpSnapshotError(f"invalid version pin for MCP server {server!r}")
    return _ServerConfig(server=server, url=url_raw, headers=headers, version=version_raw)


def _allowlist(values: Collection[str] | None) -> frozenset[str] | None:
    if values is None:
        return None
    entries: Collection[str] = (values,) if isinstance(values, str) else values
    try:
        return frozenset(_canonical_url(value) for value in entries)
    except (TypeError, ValueError):
        raise McpSnapshotError("MCP URL allowlist contains an invalid endpoint") from None


def _plain_mapping(value: Any, *, server: str) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise McpSnapshotError(f"MCP server {server!r} returned an invalid tool listing")
        return dict(value)
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(by_alias=True, exclude_none=True)
        if isinstance(dumped, Mapping) and all(isinstance(key, str) for key in dumped):
            return dict(dumped)
    raise McpSnapshotError(f"MCP server {server!r} returned an invalid tool listing")


def _tool_listing(tool: Any, *, server: str) -> tuple[str, dict[str, Any]]:
    name = _field(tool, "name")
    if not isinstance(name, str) or not name:
        raise McpSnapshotError(f"MCP server {server!r} returned an invalid tool listing")
    input_schema = _plain_mapping(
        _field(tool, "inputSchema", "input_schema", default={}), server=server
    )
    annotations = _plain_mapping(_field(tool, "annotations"), server=server)
    output_raw = _field(tool, "outputSchema", "output_schema")
    output_schema = None if output_raw is None else _plain_mapping(output_raw, server=server)
    return name, {
        "inputSchema": input_schema,
        "annotations": annotations,
        "outputSchema": output_schema,
    }


def _nested_exception(
    error: BaseException, expected: type[BaseException]
) -> BaseException | None:
    if isinstance(error, expected):
        return error
    group_type = getattr(builtins, "BaseExceptionGroup", ())
    if isinstance(error, group_type):
        for nested in error.exceptions:
            match = _nested_exception(nested, expected)
            if match is not None:
                return match
    return None


@asynccontextmanager
async def _connect(
    sdk: _McpSdk,
    config: _ServerConfig,
    *,
    timeout_s: float,
) -> AsyncIterator[tuple[Any, Any, Any]]:
    if sdk.modern_stream:
        timeout = sdk.httpx.Timeout(timeout_s)
        client = sdk.httpx.AsyncClient(
            headers=config.headers, timeout=timeout, follow_redirects=False
        )
        async with client:
            async with sdk.stream_client(config.url, http_client=client) as streams:
                yield streams
        return

    def httpx_client_factory(**kwargs: Any) -> Any:
        # Redirects would escape an exact endpoint allowlist on older SDK releases.
        return sdk.httpx.AsyncClient(**kwargs, follow_redirects=False)

    async with sdk.stream_client(
        config.url,
        headers=config.headers,
        timeout=timeout_s,
        sse_read_timeout=timeout_s,
        httpx_client_factory=httpx_client_factory,
    ) as streams:
        yield streams


async def _fetch_server(
    sdk: _McpSdk,
    config: _ServerConfig,
    *,
    timeout_s: float,
) -> _FetchedServer:
    stage = "connection"
    try:
        async with _connect(sdk, config, timeout_s=timeout_s) as (read, write, _session_id):
            async with sdk.client_session(read, write) as session:
                stage = "initialize"
                initialized = await asyncio.wait_for(session.initialize(), timeout=timeout_s)
                protocol_raw = _field(initialized, "protocolVersion", "protocol_version")
                server_info = _field(initialized, "serverInfo", "server_info")
                server_version_raw = _field(server_info, "version")
                if (
                    not isinstance(protocol_raw, (str, int))
                    or server_info is None
                    or not isinstance(server_version_raw, str)
                ):
                    raise McpSnapshotError(
                        f"MCP server {config.server!r} returned invalid initialization metadata"
                    )
                protocol = str(protocol_raw)
                server_version = server_version_raw
                if config.version is not None and server_version != config.version:
                    raise McpSnapshotError(
                        f"MCP server {config.server!r} did not match its configured version pin"
                    )

                tools: dict[str, dict[str, Any]] = {}
                cursor: str | None = None
                seen_cursors: set[str] = set()
                while True:
                    stage = "tools/list"
                    page = await asyncio.wait_for(
                        session.list_tools(cursor=cursor), timeout=timeout_s
                    )
                    page_tools = _field(page, "tools")
                    if not isinstance(page_tools, list):
                        raise McpSnapshotError(
                            f"MCP server {config.server!r} returned an invalid tools/list page"
                        )
                    for tool in page_tools:
                        name, listing = _tool_listing(tool, server=config.server)
                        if name in tools:
                            raise McpSnapshotError(
                                f"MCP server {config.server!r} returned duplicate tool name {name!r}"
                            )
                        tools[name] = listing
                    next_cursor = _field(page, "nextCursor", "next_cursor")
                    if next_cursor is None:
                        break
                    if not isinstance(next_cursor, str) or next_cursor in seen_cursors:
                        raise McpSnapshotError(
                            f"MCP server {config.server!r} returned an invalid pagination cursor"
                        )
                    seen_cursors.add(next_cursor)
                    cursor = next_cursor

                version = json.dumps(
                    {"protocol": protocol, "server": server_version},
                    sort_keys=True,
                    separators=(",", ":"),
                )
                return _FetchedServer(tools=tools, version=version)
    except (asyncio.TimeoutError, TimeoutError):
        raise McpSnapshotError(
            f"MCP snapshot timed out for server {config.server!r} during {stage}"
        ) from None
    except McpSnapshotError:
        raise
    except Exception as exc:
        snapshot_error = _nested_exception(exc, McpSnapshotError)
        if isinstance(snapshot_error, McpSnapshotError):
            raise snapshot_error from None
        if _nested_exception(exc, TimeoutError) is not None:
            raise McpSnapshotError(
                f"MCP snapshot timed out for server {config.server!r} during {stage}"
            ) from None
        raise McpSnapshotError(
            f"MCP snapshot failed for server {config.server!r} during {stage}"
        ) from None


async def _fetch_all(
    servers: Mapping[str, Any],
    *,
    auth: str | Mapping[str, str] | None,
    timeout_s: float,
    allowlist: Collection[str] | None,
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    if not servers:
        return {}, {}
    allowed_urls = _allowlist(allowlist)
    configs = [
        _server_config(server, raw, auth=auth, allowed_urls=allowed_urls)
        for server, raw in servers.items()
    ]
    sdk = _load_sdk()
    fetched = await asyncio.gather(
        *(_fetch_server(sdk, config, timeout_s=timeout_s) for config in configs)
    )
    listings = {
        config.server: result.tools for config, result in zip(configs, fetched, strict=True)
    }
    versions = {
        config.server: result.version for config, result in zip(configs, fetched, strict=True)
    }
    return listings, versions


async def _fetch_with_total_timeout(
    servers: Mapping[str, Any],
    *,
    auth: str | Mapping[str, str] | None,
    timeout_s: float,
    total_timeout_s: float,
    allowlist: Collection[str] | None,
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    try:
        return await asyncio.wait_for(
            _fetch_all(servers, auth=auth, timeout_s=timeout_s, allowlist=allowlist),
            timeout=total_timeout_s,
        )
    except (asyncio.TimeoutError, TimeoutError):
        raise McpSnapshotError("MCP snapshot timed out before all servers completed") from None


def _fetch_listings_and_versions(
    servers: Mapping[str, Any],
    *,
    auth: str | Mapping[str, str] | None,
    timeout_s: float,
    total_timeout_s: float,
    allowlist: Collection[str] | None,
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    if timeout_s <= 0 or total_timeout_s <= 0:
        raise ValueError("MCP snapshot timeouts must be positive")
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        raise RuntimeError("live MCP snapshots cannot run inside an active asyncio event loop")
    return asyncio.run(
        _fetch_with_total_timeout(
            servers,
            auth=auth,
            timeout_s=timeout_s,
            total_timeout_s=total_timeout_s,
            allowlist=allowlist,
        )
    )


def fetch_listings(
    servers: Mapping[str, Any],
    *,
    auth: str | Mapping[str, str] | None = None,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    total_timeout_s: float = DEFAULT_TOTAL_TIMEOUT_S,
    allowlist: Collection[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Fetch plain ``tools/list`` data from configured Streamable HTTP servers.

    Each server value may be a URL string, a mapping, or a config object exposing
    ``url``, ``headers``, ``auth``, and ``version``. When provided, ``allowlist``
    contains the exact endpoint URLs permitted for network access.
    """

    listings, _versions = _fetch_listings_and_versions(
        servers,
        auth=auth,
        timeout_s=timeout_s,
        total_timeout_s=total_timeout_s,
        allowlist=allowlist,
    )
    return listings


def snapshot_servers(
    servers: Mapping[str, Any],
    *,
    auth: str | Mapping[str, str] | None = None,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    total_timeout_s: float = DEFAULT_TOTAL_TIMEOUT_S,
    allowlist: Collection[str] | None = None,
) -> McpSnapshot:
    """Fetch live MCP listings and build a version-pinned freeze snapshot."""

    listings, versions = _fetch_listings_and_versions(
        servers,
        auth=auth,
        timeout_s=timeout_s,
        total_timeout_s=total_timeout_s,
        allowlist=allowlist,
    )
    # Local import avoids a deploy -> snapshot module cycle when deploy wires this helper.
    from .deploy import snapshot_from_listings

    return snapshot_from_listings(listings, versions=versions)


__all__ = [
    "DEFAULT_TIMEOUT_S",
    "DEFAULT_TOTAL_TIMEOUT_S",
    "McpSnapshotError",
    "fetch_listings",
    "snapshot_servers",
]
