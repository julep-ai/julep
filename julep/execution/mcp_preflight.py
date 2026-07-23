"""Backend-neutral run-start validation for frozen MCP tool surfaces."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections.abc import Mapping, MutableMapping
from typing import Any

from ..contracts import manifest_from_json
from ..deploy import snapshot_from_listings
from ..ir import McpTool, Node, Op, SubStep, canonical_json
from ..mcp_auth import _SECRET_REF, transport_for_mcp_caller
from ..mcp_surface import (
    McpSurfaceMismatchError,
    McpSurfacePolicy,
    assert_mcp_surface,
    canonical_surface_digest,
)
from ..secrets import REDACTED, operator_secret_redactor, scrubber_for_values
from . import effects


McpPreflightCache = MutableMapping[str, tuple[float, dict[str, Any]]]

_MCP_PREFLIGHT_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_MCP_PREFLIGHT_CACHE_TTL_S = 30.0
_MCP_PREFLIGHT_CACHE_MAX_ENTRIES = 256


class McpPreflightError(RuntimeError):
    """A typed preflight refusal independent of any execution backend."""

    def __init__(
        self,
        detail: str,
        *,
        error_type: str,
        non_retryable: bool = True,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.type = error_type
        self.non_retryable = non_retryable


def scrub_mcp_preflight_failure(
    error: BaseException,
    run_secrets: Mapping[str, str] | None,
) -> McpPreflightError:
    """Preserve failure type while removing operator and per-run secret values."""

    redactor = operator_secret_redactor()
    if run_secrets:
        redactor = scrubber_for_values(run_secrets.values(), base=redactor)
    try:
        redacted = redactor(str(error))
    except Exception:
        redacted = REDACTED
    detail = redacted if isinstance(redacted, str) else REDACTED
    return McpPreflightError(
        detail,
        error_type=(
            error.type if isinstance(error, McpPreflightError) else type(error).__name__
        ),
        non_retryable=(
            error.non_retryable if isinstance(error, McpPreflightError) else False
        ),
    )


def _prune_mcp_preflight_cache(
    now: float,
    *,
    cache: McpPreflightCache = _MCP_PREFLIGHT_CACHE,
    ttl_s: float = _MCP_PREFLIGHT_CACHE_TTL_S,
    max_entries: int = _MCP_PREFLIGHT_CACHE_MAX_ENTRIES,
) -> None:
    """Drop stale entries and bound per-process preflight cache growth."""

    expired = [
        key
        for key, (cached_at, _result) in cache.items()
        if now - cached_at > ttl_s
    ]
    for key in expired:
        cache.pop(key, None)
    overflow = len(cache) - max_entries
    if overflow <= 0:
        return
    oldest = sorted(cache, key=lambda key: (cache[key][0], key))
    for key in oldest[:overflow]:
        cache.pop(key, None)


def _refusal(error_type: str, payload: Mapping[str, Any]) -> McpPreflightError:
    return McpPreflightError(
        json.dumps(dict(payload), sort_keys=True),
        error_type=error_type,
    )


async def preflight_mcp(
    inp: Mapping[str, Any],
    *,
    cache: McpPreflightCache = _MCP_PREFLIGHT_CACHE,
    cache_ttl_s: float = _MCP_PREFLIGHT_CACHE_TTL_S,
    cache_max_entries: int = _MCP_PREFLIGHT_CACHE_MAX_ENTRIES,
) -> dict[str, Any]:
    """Validate run bindings and the frozen MCP surface on an effect context."""

    policy = McpSurfacePolicy.coerce(str(inp.get("policy", "off")))
    now = time.monotonic()
    _prune_mcp_preflight_cache(
        now,
        cache=cache,
        ttl_s=cache_ttl_s,
        max_entries=cache_max_entries,
    )
    # Preflight the entire statically reachable release surface, not only the
    # root manifest. Ref children are frozen independently and resolved from
    # the release-scoped worker registry at runtime.
    manifest_jsons: list[Mapping[str, Any]] = [dict(inp.get("manifestJson") or {})]
    pending_flows: list[Mapping[str, Any]] = []
    root_flow = inp.get("flowJson")
    if isinstance(root_flow, Mapping):
        pending_flows.append(root_flow)
    seen_refs: set[str] = set()
    while pending_flows:
        flow = Node.from_json(dict(pending_flows.pop()))
        refs: set[str] = set()
        for node in flow.walk():
            if isinstance(node.step, SubStep):
                refs.add(node.step.ref)
            if node.op is Op.APP and isinstance(node.subflows, (list, tuple)):
                refs.update(str(ref) for ref in node.subflows)
        for ref in sorted(refs):
            if ref in seen_refs:
                continue
            seen_refs.add(ref)
            spec = effects._CTX.subflows.get(ref)
            if spec is None:
                # Preserve lazy failure for an unregistered branch. Preflight
                # expands only children the release worker can resolve.
                continue
            child_manifest = spec.get("manifestJson")
            if isinstance(child_manifest, Mapping):
                manifest_jsons.append(child_manifest)
            child_flow = spec.get("flowJson")
            if isinstance(child_flow, Mapping):
                pending_flows.append(child_flow)

    frozen = [
        tool
        for manifest_json in manifest_jsons
        for tool in manifest_from_json(dict(manifest_json)).values()
        if isinstance(tool.ref, McpTool)
    ]
    if not frozen:
        unused = sorted(dict(inp.get("secrets") or {}))
        if unused:
            raise _refusal(
                "invalid_run_secret_binding",
                {
                    "error": "invalid_run_secret_binding",
                    "names": unused,
                    "allowed": [],
                },
            )
        return {"policy": policy.value, "completed": True, "surfaceDigest": None}

    frozen_digest = canonical_surface_digest(frozen)
    run_secrets = dict(inp.get("secrets") or {})
    if policy is McpSurfacePolicy.OFF and not run_secrets:
        return {
            "policy": policy.value,
            "completed": True,
            "surfaceDigest": frozen_digest,
        }

    transport = effects._CTX.mcp_transport
    if transport is None:
        transport = transport_for_mcp_caller(effects._CTX.mcp_call)
    if transport is None:
        raise RuntimeError("worker has no MCP transport configured for preflight")

    servers = sorted({tool.ref.server for tool in frozen})

    # Only whole-string references in the request-time config for referenced
    # servers are valid run bindings. Values never enter this diagnostic.
    allowed_names: set[str] = set()
    configs: dict[str, Any] = {}
    for server in servers:
        config = transport._config(server)
        configs[server] = config
        for value in config.headers.values():
            match = _SECRET_REF.fullmatch(value)
            if match is not None:
                allowed_names.add(match.group(1))
    unused = sorted(set(run_secrets) - allowed_names)
    if unused:
        raise _refusal(
            "invalid_run_secret_binding",
            {
                "error": "invalid_run_secret_binding",
                "names": unused,
                "allowed": sorted(allowed_names),
            },
        )

    if policy is McpSurfacePolicy.OFF:
        return {
            "policy": policy.value,
            "completed": True,
            "surfaceDigest": frozen_digest,
        }

    sinks: list[tuple[str, str]] = []
    for server in servers:
        config = configs[server]
        sinks.append(
            (
                f"{server}:url",
                hashlib.sha256(str(config.url).encode("utf-8")).hexdigest(),
            )
        )
        if config.version is not None:
            sinks.append(
                (
                    f"{server}:version",
                    hashlib.sha256(str(config.version).encode("utf-8")).hexdigest(),
                )
            )
        for header, raw_value in sorted(
            config.headers.items(), key=lambda item: item[0].lower()
        ):
            resolved = await transport._resolve_ref(raw_value, run_secrets)
            sinks.append(
                (
                    f"{server}:header:{header.lower()}",
                    hashlib.sha256(resolved.encode("utf-8")).hexdigest(),
                )
            )
    cache_payload = {
        "frozen": frozen_digest,
        # Keep per-manifest duplicates in the cache identity. The public
        # surface digest collapses by wire ref, but two reachable flows can pin
        # different definitions for that ref and must not share an entry.
        "frozenDefinitions": sorted(
            (tool.ref.server, tool.ref.tool, tool.definition_hash) for tool in frozen
        ),
        "policy": policy.value,
        "sinks": sinks,
        "principalHash": hashlib.sha256(
            canonical_json(inp.get("principal")).encode("utf-8")
        ).hexdigest(),
        "auth": (
            None
            if transport._auth is None
            else {"issuer": transport._auth.issuer, "kid": transport._auth.kid}
        ),
    }
    cache_key = hashlib.sha256(
        canonical_json(cache_payload).encode("utf-8")
    ).hexdigest()
    cached = cache.get(cache_key)
    if cached is not None and now - cached[0] <= cache_ttl_s:
        return dict(cached[1])

    listings = await asyncio.gather(
        *(
            transport.list_tools(
                server,
                workflow_id=str(inp["workflowId"]),
                principal=inp.get("principal"),
                run_secrets=run_secrets,
            )
            for server in servers
        )
    )
    fresh = snapshot_from_listings(
        {
            server: listing.tools
            for server, listing in zip(servers, listings, strict=True)
        },
        versions={
            server: listing.version
            for server, listing in zip(servers, listings, strict=True)
        },
        protocol_versions={
            server: listing.protocol_version
            for server, listing in zip(servers, listings, strict=True)
        },
        server_versions={
            server: listing.server_version
            for server, listing in zip(servers, listings, strict=True)
        },
    )
    try:
        assert_mcp_surface(frozen, fresh, policy=policy)
    except McpSurfaceMismatchError as exc:
        raise _refusal(
            "tool_surface_mismatch",
            {"error": "tool_surface_mismatch", "details": exc.details},
        ) from None

    result = {
        "policy": policy.value,
        "completed": True,
        "surfaceDigest": frozen_digest,
    }
    cache[cache_key] = (time.monotonic(), result)
    _prune_mcp_preflight_cache(
        time.monotonic(),
        cache=cache,
        ttl_s=cache_ttl_s,
        max_entries=cache_max_entries,
    )
    return dict(result)


__all__ = [
    "McpPreflightError",
    "preflight_mcp",
    "scrub_mcp_preflight_failure",
]
