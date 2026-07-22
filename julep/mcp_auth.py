from __future__ import annotations

import asyncio
import base64
import inspect
import json
import os
import re
import time
import uuid
from collections.abc import Awaitable, Callable, Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import jwt

from .errors import ToolSurfaceDrift

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
    from mcp.server.auth.provider import AccessToken

    from .execution.effects import McpCaller, RunPrincipal


_SEED_HEX = re.compile(r"^[0-9a-fA-F]{64}$")
_SECRET_REF = re.compile(r"^secret://([a-z0-9][a-z0-9_-]{0,63})$")
_SCOPE_KEY = "julep.mcp_auth"


class McpAuthError(PermissionError):
    """An MCP bearer token could not be authenticated or authorized."""


def _signing_seed(value: str | None) -> bytes:
    raw = value if value is not None else os.environ.get("JULEP_MCP_SIGNING_KEY")
    if raw is None or raw.strip() == "":
        raise ValueError(
            "MCP auth signing requires a signing_key parameter or JULEP_MCP_SIGNING_KEY"
        )

    # Keep this decoding contract aligned with bundle.py:_signing_seed.
    text = raw.strip()
    if not _SEED_HEX.fullmatch(text):
        path = Path(text).expanduser()
        try:
            exists = path.exists()
        except OSError:
            exists = False
        if exists:
            text = path.read_text(encoding="utf-8").strip()

    if not _SEED_HEX.fullmatch(text):
        raise ValueError(
            "MCP auth signing key must be a 64-hex ed25519 seed or a path to a file "
            "containing that seed"
        )
    return bytes.fromhex(text)


@dataclass(frozen=True)
class McpAuthConfig:
    signing_key: str
    issuer: str
    kid: str
    ttl_s: int = 300

    def __post_init__(self) -> None:
        if not 0 < self.ttl_s <= 300:
            raise ValueError("MCP auth ttl_s must be greater than 0 and at most 300 seconds")

    def private_key(self) -> Ed25519PrivateKey:
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        except ModuleNotFoundError as error:
            raise RuntimeError(
                "MCP auth signing requires cryptography; install it with pip install 'julep[mcp]'"
            ) from error
        return Ed25519PrivateKey.from_private_bytes(_signing_seed(self.signing_key))

    @classmethod
    def from_env(cls) -> McpAuthConfig:
        signing_key = os.environ.get("JULEP_MCP_SIGNING_KEY")
        if signing_key is None or signing_key.strip() == "":
            raise ValueError(
                "MCP auth signing requires a signing_key parameter or JULEP_MCP_SIGNING_KEY"
            )
        issuer = os.environ.get("JULEP_MCP_ISSUER")
        if issuer is None or issuer.strip() == "":
            raise ValueError("MCP auth signing requires JULEP_MCP_ISSUER")
        kid = os.environ.get("JULEP_MCP_KID")
        if kid is None or kid.strip() == "":
            raise ValueError("MCP auth signing requires JULEP_MCP_KID")
        raw_ttl = os.environ.get("JULEP_MCP_TTL_S", "300")
        try:
            ttl_s = int(raw_ttl)
        except ValueError as error:
            raise ValueError("JULEP_MCP_TTL_S must be an integer") from error
        return cls(signing_key=signing_key, issuer=issuer, kid=kid, ttl_s=ttl_s)


@dataclass(frozen=True)
class VerifiedToken:
    aud: str
    sub: Optional[str]
    tenant: Optional[str]
    scopes: frozenset[str]
    tool: str
    idk: str
    jti: str


def mint_token(
    cfg: McpAuthConfig,
    *,
    server_id: str,
    tool: str,
    scopes: Iterable[str],
    idempotency_key: str,
    principal: Optional[RunPrincipal],
) -> str:
    now = int(time.time())
    claims: dict[str, Any] = {
        "iss": cfg.issuer,
        "aud": server_id,
        "tool": tool,
        "scope": " ".join(sorted(set(scopes))),
        "idk": idempotency_key,
        "iat": now,
        "exp": now + cfg.ttl_s,
        "jti": uuid.uuid4().hex,
    }
    if principal is not None:
        subject = principal.get("sub")
        if subject is None:
            subject = principal.get("viewer_id")
        tenant = principal.get("tenant")
        if tenant is None:
            tenant = principal.get("store_id")
        if subject is not None:
            claims["sub"] = str(subject)
        if tenant is not None:
            claims["tenant"] = str(tenant)
    return jwt.encode(claims, cfg.private_key(), algorithm="EdDSA", headers={"kid": cfg.kid})


def _claim_string(claims: Mapping[str, Any], name: str, *, optional: bool = False) -> Optional[str]:
    value = claims.get(name)
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise McpAuthError(f"MCP token claim {name!r} must be a string")
    return value


def verify_token(
    token: str,
    *,
    verify_keys: Mapping[str, Ed25519PublicKey],
    audience: str,
    required_scopes: Iterable[str] = (),
    idempotency_key: str,
    issuer: str | None = None,
    leeway_s: int = 30,
) -> VerifiedToken:
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not isinstance(kid, str) or kid not in verify_keys:
            raise McpAuthError("MCP token uses an unknown signing key")
        claims = jwt.decode(
            token,
            verify_keys[kid],
            algorithms=["EdDSA"],
            audience=audience,
            issuer=issuer,
            leeway=leeway_s,
            options={"require": ["exp", "iat", "iss", "aud", "idk", "scope"]},
        )
        issued_at = claims["iat"]
        expires_at = claims["exp"]
        if not isinstance(issued_at, (int, float)) or isinstance(issued_at, bool):
            raise McpAuthError("MCP token claim 'iat' must be numeric")
        if not isinstance(expires_at, (int, float)) or isinstance(expires_at, bool):
            raise McpAuthError("MCP token claim 'exp' must be numeric")
        if expires_at - issued_at > 300:
            raise McpAuthError("MCP token lifetime exceeds 300 seconds")
        if issued_at > time.time() + leeway_s:
            raise McpAuthError("MCP token was issued in the future")

        actual_idk = _claim_string(claims, "idk")
        if actual_idk != idempotency_key:
            raise McpAuthError("MCP token idempotency key does not match the request header")
        scope_text = _claim_string(claims, "scope")
        assert scope_text is not None
        scopes = frozenset(scope_text.split())
        missing = frozenset(required_scopes) - scopes
        if missing:
            raise McpAuthError(f"MCP token is missing required scopes: {', '.join(sorted(missing))}")

        aud = _claim_string(claims, "aud")
        tool = _claim_string(claims, "tool")
        jti = _claim_string(claims, "jti")
        assert aud is not None and tool is not None and jti is not None and actual_idk is not None
        return VerifiedToken(
            aud=aud,
            sub=_claim_string(claims, "sub", optional=True),
            tenant=_claim_string(claims, "tenant", optional=True),
            scopes=scopes,
            tool=tool,
            idk=actual_idk,
            jti=jti,
        )
    except McpAuthError:
        raise
    except jwt.PyJWTError as error:
        raise McpAuthError(f"invalid MCP token: {error}") from error
    except (KeyError, TypeError, ValueError) as error:
        raise McpAuthError(f"invalid MCP token claims: {error}") from error


def verify_keys_from_env() -> dict[str, Ed25519PublicKey]:
    raw = os.environ.get("JULEP_MCP_VERIFY_KEYS")
    if raw is None or raw.strip() == "":
        raise McpAuthError("MCP auth verification requires JULEP_MCP_VERIFY_KEYS")
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "MCP auth verification requires cryptography; install it with pip install 'julep[mcp]'"
        ) from error

    keys: dict[str, Ed25519PublicKey] = {}
    try:
        for entry in raw.split(","):
            kid, separator, encoded = entry.strip().partition(":")
            if separator == "" or kid == "" or encoded == "" or kid in keys:
                raise ValueError("expected unique kid:base64pub entries")
            public_bytes = base64.b64decode(encoded, validate=True)
            keys[kid] = Ed25519PublicKey.from_public_bytes(public_bytes)
    except (ValueError, TypeError) as error:
        raise McpAuthError(f"invalid JULEP_MCP_VERIFY_KEYS: {error}") from error
    return keys


def _mcp_client_components() -> tuple[Any, Any]:
    try:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client
    except ModuleNotFoundError as error:
        raise RuntimeError("HTTP MCP calls require the 'mcp' extra; install 'julep[mcp]'") from error
    return ClientSession, streamablehttp_client


def _plain_tool_result(result: Any) -> Any:
    data = getattr(result, "data", None)
    if data is not None:
        return data
    structured = getattr(result, "structuredContent", None)
    if structured is None:
        structured = getattr(result, "structured_content", None)
    if structured is not None:
        return structured
    content = getattr(result, "content", result)
    if isinstance(content, list):
        return [item.model_dump(mode="json", by_alias=True) if hasattr(item, "model_dump") else item for item in content]
    return content


def _remote_error_text(value: Any) -> str:
    """Extract enough remote error text to classify drift without returning it."""

    parts: list[str] = []
    seen: set[int] = set()

    def collect(current: Any) -> None:
        identity = id(current)
        if identity in seen:
            return
        seen.add(identity)

        error = (
            current.get("error")
            if isinstance(current, Mapping)
            else getattr(current, "error", None)
        )
        if error is not None:
            message = (
                error.get("message")
                if isinstance(error, Mapping)
                else getattr(error, "message", None)
            )
            data = (
                error.get("data")
                if isinstance(error, Mapping)
                else getattr(error, "data", None)
            )
            if isinstance(message, str):
                parts.append(message)
            if data is not None:
                parts.append(str(data))
            if isinstance(error, BaseException):
                collect(error)

        if isinstance(current, BaseException):
            parts.append(str(current))
            for nested in getattr(current, "exceptions", ()):
                if isinstance(nested, BaseException):
                    collect(nested)
            for nested in (
                getattr(current, "__cause__", None),
                getattr(current, "__context__", None),
            ):
                if isinstance(nested, BaseException):
                    collect(nested)

        content = (
            current.get("content")
            if isinstance(current, Mapping)
            else getattr(current, "content", None)
        )
        if isinstance(content, list):
            for item in content:
                text = (
                    item.get("text")
                    if isinstance(item, Mapping)
                    else getattr(item, "text", None)
                )
                if isinstance(text, str):
                    parts.append(text)

    collect(value)
    return " ".join(parts).casefold()


def classify_mcp_surface_drift(
    value: Any,
    *,
    input_schema_validated: bool = False,
) -> str | None:
    """Classify conservative MCP call-site drift signatures.

    Only an MCP error response/exception is eligible.  Ordinary successful
    tool output containing these words is never classified.
    """

    is_error = isinstance(value, BaseException)
    if isinstance(value, Mapping):
        is_error = is_error or value.get("isError", value.get("is_error")) is True
    else:
        is_error = is_error or getattr(value, "isError", getattr(value, "is_error", False)) is True
    if not is_error:
        return None
    text = _remote_error_text(value)
    if any(
        signature in text
        for signature in (
            "unknown tool",
            "unrecognized tool",
            "tool not found",
            "no such tool",
            "tool does not exist",
        )
    ) or re.search(r"tool\s+['\"`]?[^\s'\"`]+['\"`]?\s+(?:was\s+)?not found", text):
        return "tool_not_found"
    if input_schema_validated and any(
        signature in text
        for signature in (
            "input validation error",
            "input schema validation",
            "input schema mismatch",
            "invalid tool arguments",
            "invalid arguments for tool",
            "arguments do not match",
        )
    ):
        return "input_schema_rejected"
    return None


class McpTransportError(RuntimeError):
    """A sanitized configuration or network failure at the MCP boundary."""


@dataclass(frozen=True)
class McpToolListing:
    """One server's complete, paginated ``tools/list`` response."""

    tools: dict[str, dict[str, Any]]
    protocol_version: str
    server_version: str

    @property
    def version(self) -> str:
        """Legacy canonical combined version used by snapshot callers."""

        return json.dumps(
            {"protocol": self.protocol_version, "server": self.server_version},
            sort_keys=True,
            separators=(",", ":"),
        )


class McpTransport:
    """The single configured transport for MCP discovery and invocation.

    Server URL/header configuration is resolved for every request, which lets
    ``secret://`` request-time credentials rotate without restarting a worker.
    A run-supplied value wins over the operator resolver for the same logical
    name and remains scoped to that call.
    """

    def __init__(
        self,
        servers: Mapping[str, Any],
        *,
        auth: McpAuthConfig | None = None,
        bearer_auth: str | Mapping[str, str] | None = None,
        secret_resolver: Any | None = None,
        timeout_s: float = 10.0,
        allowlist: Collection[str] | None = None,
    ) -> None:
        if timeout_s <= 0:
            raise ValueError("MCP transport timeout must be positive")
        # Keep endpoint validation and redirect policy identical to the live
        # snapshot path.  The import is local to avoid an import cycle.
        from . import mcp_snapshot

        allowed_urls = mcp_snapshot._allowlist(allowlist)
        self._configs = {
            server: mcp_snapshot._server_config(
                server,
                raw,
                auth=bearer_auth,
                allowed_urls=allowed_urls,
            )
            for server, raw in servers.items()
        }
        self._auth = auth
        self._secret_resolver = secret_resolver
        self._timeout_s = float(timeout_s)

    def _config(self, server: str) -> Any:
        try:
            return self._configs[server]
        except KeyError as error:
            raise McpTransportError(f"unknown MCP server {server!r}") from error

    async def _resolve_ref(
        self,
        value: str,
        run_secrets: Mapping[str, str] | None,
    ) -> str:
        match = _SECRET_REF.fullmatch(value)
        if match is None:
            if value.startswith("secret://"):
                raise McpTransportError("invalid MCP secret reference")
            return value
        name = match.group(1)
        if run_secrets is not None and name in run_secrets:
            resolved = run_secrets[name]
            if not isinstance(resolved, str):
                raise McpTransportError(f"run secret {name!r} must be a string")
            return resolved
        resolver = self._secret_resolver
        if resolver is None:
            try:
                from .secrets import SecretResolver
            except ImportError:
                raise McpTransportError(f"unresolved MCP secret reference {name!r}") from None
            resolver = SecretResolver.from_env()
            self._secret_resolver = resolver
        try:
            resolve_ref = resolver.resolve_ref
            if inspect.iscoroutinefunction(resolve_ref):
                resolved = await resolve_ref(value)
            else:
                # The built-in resolver performs a blocking control-plane HTTP
                # request on cache miss; keep it off the worker event loop.
                resolved = await asyncio.to_thread(resolve_ref, value)
            if inspect.isawaitable(resolved):
                resolved = await resolved
        except Exception as error:
            raise McpTransportError(f"failed to resolve MCP secret reference {name!r}") from error
        if not isinstance(resolved, str) or _SECRET_REF.fullmatch(resolved):
            raise McpTransportError(f"unresolved MCP secret reference {name!r}")
        return resolved

    async def _headers(
        self,
        config: Any,
        *,
        tool: str,
        scopes: Iterable[str],
        idempotency_key: str,
        principal: Optional[RunPrincipal],
        run_secrets: Mapping[str, str] | None,
    ) -> dict[str, str]:
        headers = {
            key: await self._resolve_ref(value, run_secrets)
            for key, value in config.headers.items()
        }
        headers["Idempotency-Key"] = idempotency_key
        if self._auth is not None and not any(
            key.lower() == "authorization" for key in headers
        ):
            token = mint_token(
                self._auth,
                server_id=config.server,
                tool=tool,
                scopes=scopes,
                idempotency_key=idempotency_key,
                principal=principal,
            )
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def list_tools(
        self,
        server: str,
        *,
        workflow_id: str,
        principal: Optional[RunPrincipal] = None,
        run_secrets: Mapping[str, str] | None = None,
    ) -> McpToolListing:
        """Discover one server with a scoped, deterministic preflight identity."""

        from . import mcp_snapshot

        config = self._config(server)
        idempotency_key = f"preflight:{workflow_id}:{server}"
        headers = await self._headers(
            config,
            tool="tools/list",
            scopes={"tools/list"},
            idempotency_key=idempotency_key,
            principal=principal,
            run_secrets=run_secrets,
        )
        request_config = type(config)(
            server=config.server,
            url=config.url,
            headers=headers,
            version=config.version,
        )
        stage = "connection"
        sdk = mcp_snapshot._load_sdk()
        try:
            async with mcp_snapshot._connect(
                sdk, request_config, timeout_s=self._timeout_s
            ) as (read, write, _session_id):
                async with sdk.client_session(read, write) as session:
                    stage = "initialize"
                    initialized = await asyncio.wait_for(
                        session.initialize(), timeout=self._timeout_s
                    )
                    protocol_raw = mcp_snapshot._field(
                        initialized, "protocolVersion", "protocol_version"
                    )
                    server_info = mcp_snapshot._field(
                        initialized, "serverInfo", "server_info"
                    )
                    server_version_raw = mcp_snapshot._field(server_info, "version")
                    if (
                        not isinstance(protocol_raw, (str, int))
                        or server_info is None
                        or not isinstance(server_version_raw, str)
                    ):
                        raise McpTransportError(
                            f"MCP server {server!r} returned invalid initialization metadata"
                        )
                    protocol_version = str(protocol_raw)
                    if config.version is not None and server_version_raw != config.version:
                        raise McpTransportError(
                            f"MCP server {server!r} did not match its configured version pin"
                        )

                    tools: dict[str, dict[str, Any]] = {}
                    cursor: str | None = None
                    seen_cursors: set[str] = set()
                    while True:
                        stage = "tools/list"
                        page = await asyncio.wait_for(
                            session.list_tools(cursor=cursor), timeout=self._timeout_s
                        )
                        page_tools = mcp_snapshot._field(page, "tools")
                        if not isinstance(page_tools, list):
                            raise McpTransportError(
                                f"MCP server {server!r} returned an invalid tools/list page"
                            )
                        for raw_tool in page_tools:
                            name, listing = mcp_snapshot._tool_listing(raw_tool, server=server)
                            if name in tools:
                                raise McpTransportError(
                                    f"MCP server {server!r} returned duplicate tool name {name!r}"
                                )
                            tools[name] = listing
                        next_cursor = mcp_snapshot._field(
                            page, "nextCursor", "next_cursor"
                        )
                        if next_cursor is None:
                            break
                        if not isinstance(next_cursor, str) or next_cursor in seen_cursors:
                            raise McpTransportError(
                                f"MCP server {server!r} returned an invalid pagination cursor"
                            )
                        seen_cursors.add(next_cursor)
                        cursor = next_cursor
                    return McpToolListing(
                        tools=tools,
                        protocol_version=protocol_version,
                        server_version=server_version_raw,
                    )
        except (asyncio.TimeoutError, TimeoutError):
            raise McpTransportError(
                f"MCP request timed out for server {server!r} during {stage}"
            ) from None
        except McpTransportError:
            raise
        except Exception as error:
            nested = mcp_snapshot._nested_exception(error, McpTransportError)
            if isinstance(nested, McpTransportError):
                raise nested from None
            if mcp_snapshot._nested_exception(error, TimeoutError) is not None:
                raise McpTransportError(
                    f"MCP request timed out for server {server!r} during {stage}"
                ) from None
            raise McpTransportError(
                f"MCP request failed for server {server!r} during {stage}"
            ) from None

    async def call_tool(
        self,
        server: str,
        tool: str,
        value: Any,
        idempotency_key: str,
        principal: Optional[RunPrincipal] = None,
        run_secrets: Mapping[str, str] | None = None,
        input_schema_validated: bool = False,
    ) -> Any:
        """Invoke one MCP tool through the same configured transport as discovery."""

        from . import mcp_snapshot

        config = self._config(server)
        headers = await self._headers(
            config,
            tool=tool,
            scopes={tool},
            idempotency_key=idempotency_key,
            principal=principal,
            run_secrets=run_secrets,
        )
        request_config = type(config)(
            server=config.server,
            url=config.url,
            headers=headers,
            version=config.version,
        )
        stage = "connection"
        sdk = mcp_snapshot._load_sdk()
        try:
            async with mcp_snapshot._connect(
                sdk, request_config, timeout_s=self._timeout_s
            ) as (read, write, _session_id):
                async with sdk.client_session(read, write) as session:
                    stage = "initialize"
                    await asyncio.wait_for(session.initialize(), timeout=self._timeout_s)
                    stage = "tools/call"
                    result = await asyncio.wait_for(
                        session.call_tool(tool, arguments=value), timeout=self._timeout_s
                    )
                    drift_reason = classify_mcp_surface_drift(
                        result,
                        input_schema_validated=input_schema_validated,
                    )
                    if drift_reason is not None:
                        raise ToolSurfaceDrift(server, tool, drift_reason)
                    return _plain_tool_result(result)
        except (asyncio.TimeoutError, TimeoutError):
            raise McpTransportError(
                f"MCP request timed out for server {server!r} during {stage}"
            ) from None
        except (McpTransportError, ToolSurfaceDrift):
            raise
        except Exception as error:
            nested_drift = mcp_snapshot._nested_exception(error, ToolSurfaceDrift)
            if isinstance(nested_drift, ToolSurfaceDrift):
                raise nested_drift from None
            nested_transport = mcp_snapshot._nested_exception(error, McpTransportError)
            if isinstance(nested_transport, McpTransportError):
                raise nested_transport from None
            if stage == "tools/call":
                drift_reason = classify_mcp_surface_drift(
                    error,
                    input_schema_validated=input_schema_validated,
                )
                if drift_reason is not None:
                    raise ToolSurfaceDrift(server, tool, drift_reason) from None
            if mcp_snapshot._nested_exception(error, TimeoutError) is not None:
                raise McpTransportError(
                    f"MCP request timed out for server {server!r} during {stage}"
                ) from None
            raise McpTransportError(
                f"MCP request failed for server {server!r} during {stage}"
            ) from None


def http_mcp_caller(
    servers: Mapping[str, Any],
    auth: McpAuthConfig | None = None,
    *,
    secret_resolver: Any | None = None,
    timeout_s: float = 10.0,
    allowlist: Collection[str] | None = None,
) -> McpCaller:
    transport = McpTransport(
        servers,
        auth=auth,
        secret_resolver=secret_resolver,
        timeout_s=timeout_s,
        allowlist=allowlist,
    )

    async def call(
        server: str,
        tool: str,
        value: Any,
        key: str,
        principal: Optional[RunPrincipal],
        run_secrets: Mapping[str, str] | None = None,
        input_schema_validated: bool = False,
    ) -> Any:
        return await transport.call_tool(
            server,
            tool,
            value,
            key,
            principal,
            run_secrets,
            input_schema_validated,
        )

    # Worker preflight recovers the exact same configured transport rather than
    # rebuilding URL/header/auth policy through a second path.
    call.transport = transport  # type: ignore[attr-defined]
    return call


def transport_for_mcp_caller(caller: Any) -> McpTransport | None:
    """Return the shared transport attached by :func:`http_mcp_caller`."""

    transport = getattr(caller, "transport", None)
    return transport if isinstance(transport, McpTransport) else None


@dataclass(frozen=True)
class FastMCPTokenVerifier:
    verify_keys: Mapping[str, Ed25519PublicKey]
    audience: str
    required_scopes: Sequence[str] = ()
    issuer: str | None = None
    leeway_s: int = 30

    async def verify_token(self, token: str) -> AccessToken | None:
        # TokenVerifier does not receive request headers; asgi_auth_middleware enforces idk == header.
        try:
            unverified = jwt.decode(token, options={"verify_signature": False})
            idempotency_key = unverified.get("idk")
            if not isinstance(idempotency_key, str):
                return None
            verified = verify_token(
                token,
                verify_keys=self.verify_keys,
                audience=self.audience,
                required_scopes=self.required_scopes,
                idempotency_key=idempotency_key,
                issuer=self.issuer,
                leeway_s=self.leeway_s,
            )
            from mcp.server.auth.provider import AccessToken

            expires_at = unverified.get("exp")
            if not isinstance(expires_at, int) or isinstance(expires_at, bool):
                return None
            return AccessToken(
                token=token,
                client_id=verified.sub or verified.tenant or verified.aud,
                scopes=sorted(verified.scopes),
                expires_at=expires_at,
                resource=verified.aud,
            )
        except (McpAuthError, jwt.PyJWTError, ModuleNotFoundError, TypeError, ValueError):
            return None


ASGIApp = Callable[[dict[str, Any], Callable[[], Awaitable[dict[str, Any]]], Callable[[dict[str, Any]], Awaitable[None]]], Awaitable[None]]


def asgi_auth_middleware(
    app: ASGIApp,
    *,
    verify_keys: Mapping[str, Ed25519PublicKey],
    audience: str,
    required_scopes: Iterable[str] = (),
    issuer: str | None = None,
    leeway_s: int = 30,
) -> ASGIApp:
    required = tuple(required_scopes)

    async def middleware(
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        if scope.get("type") != "http":
            await app(scope, receive, send)
            return
        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        authorization = headers.get("authorization", "")
        idempotency_key = headers.get("idempotency-key")
        if not authorization.startswith("Bearer ") or idempotency_key is None:
            await _send_auth_error(send, 401, "missing bearer token or Idempotency-Key header")
            return
        try:
            verified = verify_token(
                authorization.removeprefix("Bearer ").strip(),
                verify_keys=verify_keys,
                audience=audience,
                required_scopes=required,
                idempotency_key=idempotency_key,
                issuer=issuer,
                leeway_s=leeway_s,
            )
        except McpAuthError as error:
            status = 403 if "missing required scopes" in str(error) else 401
            await _send_auth_error(send, status, str(error))
            return
        scope[_SCOPE_KEY] = verified
        await app(scope, receive, send)

    return middleware


async def _send_auth_error(
    send: Callable[[dict[str, Any]], Awaitable[None]], status: int, detail: str
) -> None:
    body = json.dumps({"detail": detail}, separators=(",", ":")).encode()
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())],
        }
    )
    await send({"type": "http.response.body", "body": body})
