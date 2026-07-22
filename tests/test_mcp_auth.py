from __future__ import annotations

import asyncio
import base64
import time
from contextlib import AbstractAsyncContextManager
from types import SimpleNamespace
from typing import Any

import pytest

pytest.importorskip("jwt")  # PyJWT ships in the `mcp` extra

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from julep.mcp_auth import (
    FastMCPTokenVerifier,
    McpAuthConfig,
    McpAuthError,
    McpTransport,
    VerifiedToken,
    asgi_auth_middleware,
    classify_mcp_surface_drift,
    http_mcp_caller,
    mint_token,
    transport_for_mcp_caller,
    verify_keys_from_env,
    verify_token,
)
from julep.errors import ToolSurfaceDrift


SEED = bytes(range(32))
SEED_HEX = SEED.hex()
PRIVATE_KEY = Ed25519PrivateKey.from_private_bytes(SEED)
PUBLIC_KEY = PRIVATE_KEY.public_key()


def config(**changes: Any) -> McpAuthConfig:
    values: dict[str, Any] = {
        "signing_key": SEED_HEX,
        "issuer": "julep-worker",
        "kid": "key-1",
        "ttl_s": 300,
    }
    values.update(changes)
    return McpAuthConfig(**values)


def minted(**changes: Any) -> str:
    values: dict[str, Any] = {
        "server_id": "memory",
        "tool": "search",
        "scopes": {"search", "read"},
        "idempotency_key": "cid-123",
        "principal": {"viewer_id": 42, "store_id": "tenant-a"},
    }
    values.update(changes)
    return mint_token(config(), **values)


def test_mint_verify_roundtrip() -> None:
    verified = verify_token(
        minted(),
        verify_keys={"key-1": PUBLIC_KEY},
        audience="memory",
        required_scopes={"search"},
        idempotency_key="cid-123",
        issuer="julep-worker",
    )

    assert verified == VerifiedToken(
        aud="memory",
        sub="42",
        tenant="tenant-a",
        scopes=frozenset({"read", "search"}),
        tool="search",
        idk="cid-123",
        jti=verified.jti,
    )
    assert len(verified.jti) == 32
    assert jwt.get_unverified_header(minted())["kid"] == "key-1"


@pytest.mark.parametrize("ttl_s", [0, -1, 301])
def test_config_enforces_ttl_cap(ttl_s: int) -> None:
    with pytest.raises(ValueError, match="at most 300"):
        config(ttl_s=ttl_s)


def test_forged_lifetime_over_cap_is_rejected() -> None:
    now = int(time.time())
    token = jwt.encode(
        {
            "iss": "julep-worker",
            "aud": "memory",
            "tool": "search",
            "scope": "search",
            "idk": "cid-123",
            "iat": now,
            "exp": now + 301,
            "jti": "forged",
        },
        PRIVATE_KEY,
        algorithm="EdDSA",
        headers={"kid": "key-1"},
    )

    with pytest.raises(McpAuthError, match="lifetime"):
        verify_token(
            token,
            verify_keys={"key-1": PUBLIC_KEY},
            audience="memory",
            idempotency_key="cid-123",
        )


@pytest.mark.parametrize(
    ("changes", "verify_changes", "match"),
    [
        ({}, {"audience": "other"}, "Audience"),
        ({}, {"issuer": "other"}, "issuer"),
        ({}, {"verify_keys": {"other": PUBLIC_KEY}}, "unknown signing key"),
        ({"scopes": {"read"}}, {"required_scopes": {"search"}}, "missing required scopes"),
    ],
)
def test_verification_rejects_wrong_authority_or_scope(
    changes: dict[str, Any], verify_changes: dict[str, Any], match: str
) -> None:
    kwargs: dict[str, Any] = {
        "verify_keys": {"key-1": PUBLIC_KEY},
        "audience": "memory",
        "required_scopes": (),
        "idempotency_key": "cid-123",
        "issuer": "julep-worker",
    }
    kwargs.update(verify_changes)
    with pytest.raises(McpAuthError, match=match):
        verify_token(minted(**changes), **kwargs)


def test_idempotency_key_is_bound_to_request_header() -> None:
    assert verify_token(
        minted(),
        verify_keys={"key-1": PUBLIC_KEY},
        audience="memory",
        idempotency_key="cid-123",
    ).idk == "cid-123"

    with pytest.raises(McpAuthError, match="does not match"):
        verify_token(
            minted(),
            verify_keys={"key-1": PUBLIC_KEY},
            audience="memory",
            idempotency_key="different-cid",
        )


def test_principal_is_reduced_to_well_known_claims() -> None:
    token = minted(
        principal={
            "sub": "subject",
            "tenant": "tenant",
            "api_key": "do-not-serialize-this",
            "nested": {"secret": "also-secret"},
        }
    )
    claims = jwt.decode(token, options={"verify_signature": False})

    assert claims["sub"] == "subject"
    assert claims["tenant"] == "tenant"
    assert "api_key" not in claims
    assert "nested" not in claims
    assert "do-not-serialize-this" not in str(claims)


def test_verify_keys_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    raw_public = PUBLIC_KEY.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    monkeypatch.setenv(
        "JULEP_MCP_VERIFY_KEYS", f"key-1:{base64.b64encode(raw_public).decode()}"
    )

    keys = verify_keys_from_env()
    assert set(keys) == {"key-1"}
    assert verify_token(
        minted(),
        verify_keys=keys,
        audience="memory",
        idempotency_key="cid-123",
    ).aud == "memory"


def test_config_from_env_and_seed_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    key_file = tmp_path / "mcp.key"
    key_file.write_text(SEED_HEX)
    monkeypatch.setenv("JULEP_MCP_SIGNING_KEY", str(key_file))
    monkeypatch.setenv("JULEP_MCP_ISSUER", "issuer")
    monkeypatch.setenv("JULEP_MCP_KID", "kid")
    monkeypatch.setenv("JULEP_MCP_TTL_S", "60")

    cfg = McpAuthConfig.from_env()
    assert cfg == McpAuthConfig(str(key_file), "issuer", "kid", 60)
    assert cfg.private_key().public_key() == PUBLIC_KEY


def test_fastmcp_token_verifier_contract() -> None:
    pytest.importorskip("mcp")
    from mcp.server.auth.provider import AccessToken

    verifier = FastMCPTokenVerifier(
        verify_keys={"key-1": PUBLIC_KEY},
        audience="memory",
        required_scopes=("search",),
        issuer="julep-worker",
    )
    access = asyncio.run(verifier.verify_token(minted()))

    assert isinstance(access, AccessToken)
    assert access.client_id == "42"
    assert access.scopes == ["read", "search"]
    assert access.resource == "memory"
    assert asyncio.run(verifier.verify_token(minted(scopes={"read"}))) is None


def test_asgi_auth_middleware_valid_invalid_and_idk_mismatch() -> None:
    pytest.importorskip("starlette")
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from starlette.testclient import TestClient

    async def endpoint(request: Request) -> JSONResponse:
        verified = request.scope["julep.mcp_auth"]
        return JSONResponse({"sub": verified.sub, "idk": verified.idk})

    inner = Starlette(routes=[Route("/mcp", endpoint, methods=["POST"])])
    app = asgi_auth_middleware(
        inner,
        verify_keys={"key-1": PUBLIC_KEY},
        audience="memory",
        required_scopes={"search"},
        issuer="julep-worker",
    )
    with TestClient(app) as client:
        response = client.post(
            "/mcp",
            headers={"Authorization": f"Bearer {minted()}", "Idempotency-Key": "cid-123"},
        )
        invalid = client.post(
            "/mcp", headers={"Authorization": "Bearer invalid", "Idempotency-Key": "cid-123"}
        )
        mismatch = client.post(
            "/mcp",
            headers={"Authorization": f"Bearer {minted()}", "Idempotency-Key": "other"},
        )

    assert response.status_code == 200
    assert response.json() == {"sub": "42", "idk": "cid-123"}
    assert invalid.status_code == 401
    assert mismatch.status_code == 401


def test_http_mcp_caller_sets_headers_and_normalizes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("mcp")
    captured: dict[str, Any] = {}

    class Transport(AbstractAsyncContextManager[tuple[object, object, object]]):
        async def __aenter__(self) -> tuple[object, object, object]:
            return object(), object(), object()

        async def __aexit__(self, *args: Any) -> None:
            return None

    def transport(url: str, **kwargs: Any) -> Transport:
        captured.update(url=url, headers=kwargs["headers"])
        return Transport()

    class Session(AbstractAsyncContextManager["Session"]):
        def __init__(self, read: object, write: object) -> None:
            captured.update(read=read, write=write)

        async def __aenter__(self) -> Session:
            return self

        async def __aexit__(self, *args: Any) -> None:
            return None

        async def initialize(self) -> None:
            captured["initialized"] = True

        async def call_tool(self, tool: str, *, arguments: Any) -> Any:
            captured.update(tool=tool, arguments=arguments)
            return SimpleNamespace(data=None, structuredContent={"result": 7})

    class FakeHttpx:
        class AsyncClient:
            def __init__(self, **_kwargs: Any) -> None:
                pass

    import julep.mcp_snapshot as mcp_snapshot

    monkeypatch.setattr(
        mcp_snapshot,
        "_load_sdk",
        lambda: mcp_snapshot._McpSdk(
            client_session=Session,
            stream_client=transport,
            modern_stream=False,
            httpx=FakeHttpx,
        ),
    )
    caller = http_mcp_caller({"memory": "https://mcp.example.test"}, config())
    assert transport_for_mcp_caller(caller) is not None
    result = asyncio.run(caller("memory", "search", {"q": "x"}, "cid-123", {"sub": "u"}))

    assert result == {"result": 7}
    assert captured["url"] == "https://mcp.example.test"
    assert captured["initialized"] is True
    assert captured["tool"] == "search"
    assert captured["arguments"] == {"q": "x"}
    headers = captured["headers"]
    assert headers["Idempotency-Key"] == "cid-123"
    token = headers["Authorization"].removeprefix("Bearer ")
    verified = verify_token(
        token,
        verify_keys={"key-1": PUBLIC_KEY},
        audience="memory",
        required_scopes={"search"},
        idempotency_key="cid-123",
    )
    assert verified.tool == "search"


def test_http_mcp_caller_rejects_unknown_server() -> None:
    caller = http_mcp_caller({"memory": "https://mcp.example.test"})
    with pytest.raises(RuntimeError, match="unknown MCP server"):
        asyncio.run(caller("other", "search", {}, "cid", None))


def test_transport_run_secret_shadows_operator_resolver() -> None:
    class Resolver:
        def __init__(self) -> None:
            self.values: list[str] = []

        def resolve_ref(self, value: str) -> str:
            self.values.append(value)
            return "operator-value"

    resolver = Resolver()
    transport = McpTransport(
        {
            "memory": {
                "url": "https://mcp.example.test",
                "headers": {"X-Token": "secret://tracker-token"},
            }
        },
        secret_resolver=resolver,
    )
    configured = transport._config("memory")

    run_headers = asyncio.run(
        transport._headers(
            configured,
            tool="search",
            scopes={"search"},
            idempotency_key="cid-run",
            principal=None,
            run_secrets={"tracker-token": "tenant-value"},
        )
    )
    operator_headers = asyncio.run(
        transport._headers(
            configured,
            tool="search",
            scopes={"search"},
            idempotency_key="cid-operator",
            principal=None,
            run_secrets=None,
        )
    )

    assert run_headers["X-Token"] == "tenant-value"
    assert operator_headers["X-Token"] == "operator-value"
    assert resolver.values == ["secret://tracker-token"]


def test_transport_rejects_malformed_whole_secret_reference() -> None:
    transport = McpTransport(
        {
            "memory": {
                "url": "https://mcp.example.test",
                "headers": {"X-Token": "secret://Bad_Name"},
            }
        }
    )

    with pytest.raises(RuntimeError, match="invalid MCP secret reference"):
        asyncio.run(transport._resolve_ref("secret://Bad_Name", None))
    assert (
        asyncio.run(transport._resolve_ref("Bearer secret://tracker-token", None))
        == "Bearer secret://tracker-token"
    )


def test_transport_discovery_token_has_dedicated_scope_and_deterministic_idk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import julep.mcp_snapshot as mcp_snapshot

    captured: dict[str, Any] = {}

    class Transport(AbstractAsyncContextManager[tuple[object, object, object]]):
        async def __aenter__(self) -> tuple[object, object, object]:
            return object(), object(), object()

        async def __aexit__(self, *args: Any) -> None:
            return None

    def stream(url: str, **kwargs: Any) -> Transport:
        captured.update(url=url, headers=kwargs["headers"])
        return Transport()

    class Session(AbstractAsyncContextManager["Session"]):
        def __init__(self, _read: object, _write: object) -> None:
            pass

        async def __aenter__(self) -> Session:
            return self

        async def __aexit__(self, *args: Any) -> None:
            return None

        async def initialize(self) -> Any:
            return SimpleNamespace(
                protocolVersion="2025-03-26",
                serverInfo=SimpleNamespace(version="2.4.0"),
            )

        async def list_tools(self, *, cursor: str | None = None) -> Any:
            assert cursor is None
            return SimpleNamespace(tools=[], nextCursor=None)

    class FakeHttpx:
        class AsyncClient:
            def __init__(self, **_kwargs: Any) -> None:
                pass

    monkeypatch.setattr(
        mcp_snapshot,
        "_load_sdk",
        lambda: mcp_snapshot._McpSdk(Session, stream, False, FakeHttpx),
    )
    transport = McpTransport(
        {"memory": "https://mcp.example.test"},
        auth=config(),
    )

    listing = asyncio.run(transport.list_tools("memory", workflow_id="wf-123"))

    assert listing.protocol_version == "2025-03-26"
    idempotency_key = captured["headers"]["Idempotency-Key"]
    assert idempotency_key == "preflight:wf-123:memory"
    token = captured["headers"]["Authorization"].removeprefix("Bearer ")
    verified = verify_token(
        token,
        verify_keys={"key-1": PUBLIC_KEY},
        audience="memory",
        required_scopes={"tools/list"},
        idempotency_key=idempotency_key,
    )
    assert verified.tool == "tools/list"


@pytest.mark.parametrize(
    ("message", "validated", "reason"),
    [
        ("Unknown tool: search", False, "tool_not_found"),
        ("Input validation error: 'q' is required", True, "input_schema_rejected"),
    ],
)
def test_mcp_error_result_classifies_surface_drift(
    message: str, validated: bool, reason: str
) -> None:
    result = SimpleNamespace(
        isError=True,
        content=[SimpleNamespace(text=message)],
    )

    assert classify_mcp_surface_drift(
        result, input_schema_validated=validated
    ) == reason


def test_schema_rejection_is_not_drift_without_frozen_validation() -> None:
    result = SimpleNamespace(
        isError=True,
        content=[SimpleNamespace(text="Input validation error: 'q' is required")],
    )

    assert classify_mcp_surface_drift(result) is None


@pytest.mark.parametrize(
    ("message", "validated", "reason"),
    [
        ("tool 'search' not found", False, "tool_not_found"),
        ("invalid arguments for tool search", True, "input_schema_rejected"),
    ],
)
def test_nested_exception_group_classifies_surface_drift(
    message: str,
    validated: bool,
    reason: str,
) -> None:
    wrapper = RuntimeError("wrapper")
    wrapper.__cause__ = RuntimeError(message)
    exception_group = vars(__import__("builtins"))["ExceptionGroup"]
    error = exception_group("transport group", [wrapper])

    assert classify_mcp_surface_drift(
        error,
        input_schema_validated=validated,
    ) == reason


def test_drift_classifier_ignores_success_and_business_errors() -> None:
    successful = SimpleNamespace(
        isError=False,
        content=[SimpleNamespace(text="Unknown tool appears in documentation")],
    )
    business_error = SimpleNamespace(
        isError=True,
        content=[SimpleNamespace(text="customer record not found")],
    )

    assert classify_mcp_surface_drift(successful) is None
    assert classify_mcp_surface_drift(business_error) is None


def test_transport_raises_typed_drift_for_error_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import julep.mcp_snapshot as mcp_snapshot

    class Stream(AbstractAsyncContextManager[tuple[object, object, object]]):
        async def __aenter__(self) -> tuple[object, object, object]:
            return object(), object(), object()

        async def __aexit__(self, *args: Any) -> None:
            return None

    class Session(AbstractAsyncContextManager["Session"]):
        def __init__(self, _read: object, _write: object) -> None:
            pass

        async def __aenter__(self) -> Session:
            return self

        async def __aexit__(self, *args: Any) -> None:
            return None

        async def initialize(self) -> None:
            return None

        async def call_tool(self, _tool: str, *, arguments: Any) -> Any:
            del arguments
            return SimpleNamespace(
                isError=True,
                content=[SimpleNamespace(text="Unknown tool: removed")],
            )

    class FakeHttpx:
        class AsyncClient:
            def __init__(self, **_kwargs: Any) -> None:
                pass

    monkeypatch.setattr(
        mcp_snapshot,
        "_load_sdk",
        lambda: mcp_snapshot._McpSdk(
            Session,
            lambda _url, **_kwargs: Stream(),
            False,
            FakeHttpx,
        ),
    )
    transport = McpTransport({"memory": "https://mcp.example.test"})

    with pytest.raises(ToolSurfaceDrift) as raised:
        asyncio.run(transport.call_tool("memory", "removed", {}, "cid", None))

    assert raised.value.to_json() == {
        "server": "memory",
        "tool": "removed",
        "reason": "tool_not_found",
    }
