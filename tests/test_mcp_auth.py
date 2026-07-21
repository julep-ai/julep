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
    VerifiedToken,
    asgi_auth_middleware,
    http_mcp_caller,
    mint_token,
    verify_keys_from_env,
    verify_token,
)


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
    import julep.mcp_auth as mcp_auth

    captured: dict[str, Any] = {}

    class Transport(AbstractAsyncContextManager[tuple[object, object, object]]):
        async def __aenter__(self) -> tuple[object, object, object]:
            return object(), object(), object()

        async def __aexit__(self, *args: Any) -> None:
            return None

    def transport(url: str, *, headers: dict[str, str]) -> Transport:
        captured.update(url=url, headers=headers)
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

    monkeypatch.setattr(mcp_auth, "_mcp_client_components", lambda: (Session, transport))
    caller = http_mcp_caller({"memory": "https://mcp.example.test"}, config())
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
