"""Backend-neutral effect implementations (the Hands + Brains boundary).

These are the bodies of the Temporal activities, factored out so any durable
backend (Temporal, DBOS) can wrap them in its own retry/checkpoint unit.
This module must never import an engine: no temporalio, no dbos.
Configuration is process-global via :func:`configure` (one WorkerContext per
worker process), exactly as before.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

from .. import agent_loop as al
from ..capabilities import CapabilityManifest, ToolGrant
from ..contracts import CONSERVATIVE_DEFAULT, ToolContract
from ..dotctx import Brain
from ..errors import CapabilityDenied, PureDriftError
from ..ir import Node, toolref_from_json, toolref_key
from ..kinds import Effect, Idempotency
from ..registry import DEFAULT_REGISTRY, Registry
from ..prompt import rendered_brain_for
from ..staged import admit_plan
from .blobstore import BlobStore
from .session_store import SessionStore

logger = logging.getLogger("composable_agents.execution.effects")

# Caller signatures the worker supplies.
McpCaller = Callable[[str, str, Any, str], Awaitable[Any]]  # (server, tool, args, key) -> result
LlmCaller = Callable[[Brain, Any], Awaitable[Any]]         # (brain, value) -> result


@dataclass
class WorkerContext:
    """Process-global configuration read by the activities.

    ``mcp_call`` receives ``(server, tool, value, idempotency_key)``. The key is
    the deterministic activation ``cid`` from :class:`CallHandInput`; Temporal
    retries re-invoke the activity with the same input, so MCP retry keys are
    stable by construction. MCP now carries the key, so MCP tools that require
    transport-level idempotency are admissible.
    """

    hand_urls: dict[str, str] = field(default_factory=dict)   # native name -> URL
    mcp_call: Optional[McpCaller] = None
    llm: Optional[LlmCaller] = None
    blob_store: Optional[BlobStore] = None
    session_store: Optional[SessionStore] = None
    capabilities: Optional[CapabilityManifest] = None
    registry: Optional[Registry] = None
    http_timeout_s: float = 30.0
    # Deploy-time registries. A sub-flow is a separately frozen flow addressable
    # by ref; an agent spec is the controller's loop policy. Both are fixed at
    # worker startup, so the resolve* activities below read them deterministically.
    # ref -> {flowJson, manifestJson, pureSourceHashes?}
    subflows: dict[str, dict[str, Any]] = field(default_factory=dict)
    # controller -> {config, grantedTools, grantedContracts, grantedSubflows}
    agents: dict[str, dict[str, Any]] = field(default_factory=dict)


_CTX = WorkerContext()


def configure(ctx: WorkerContext) -> None:
    """Install the worker-wide context the activities read."""
    global _CTX
    _CTX = ctx


def _registry() -> Registry:
    return _CTX.registry or DEFAULT_REGISTRY


def _domain_of(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).hostname or ""


# --------------------------------------------------------------------------- #
# Payloads (Temporal serializes these to/from the data converter).
# --------------------------------------------------------------------------- #
@dataclass
class CallHandInput:
    tool_ref: dict[str, Any]      # ToolRef JSON (native or mcp)
    value: Any
    cid: str                      # deterministic activation id -> Idempotency-Key
    # Advisory CacheHint JSON. The hand/transport may honor it; the framework
    # does not provide a cache backend or change replay behavior from this hint.
    cache: Optional[dict[str, Any]] = None


@dataclass
class InvokeBrainInput:
    brain: str
    value: Any
    cid: str


@dataclass
class CompilePlanInput:
    planner: str
    value: Any
    cid: str
    manifest: Optional[dict[str, Any]] = None  # parent frozen manifest (for schema checks)


@dataclass
class LoadStateInput:
    session_id: str
    cursor: int


@dataclass
class CommitStateInput:
    session_id: str
    base: int
    state: dict[str, Any]
    state_hash: str


@dataclass
class PutBlobInput:
    tenant: str
    value: Any


# --------------------------------------------------------------------------- #
# Activities.
# --------------------------------------------------------------------------- #
async def loadState(inp: LoadStateInput) -> dict[str, Any]:
    if _CTX.session_store is None:
        raise RuntimeError("worker has no session store configured")
    return (await _CTX.session_store.load(inp.session_id, inp.cursor)).to_json()


async def commitState(inp: CommitStateInput) -> int:
    if _CTX.session_store is None:
        raise RuntimeError("worker has no session store configured")
    state = al.AgentState.from_json(inp.state)
    return await _CTX.session_store.commit(
        inp.session_id, inp.base, state, inp.state_hash
    )


async def putBlob(inp: PutBlobInput) -> str:
    """JSON-canonical claim check for trace/context refs (``trace_content_refs``).

    Refs address the canonical JSON encoding (``json.dumps(sort_keys=True)``) —
    a deliberately distinct ref-space from the wire codec's raw-payload refs
    (``codec.py``); non-JSON values are rejected loudly (``TypeError``).
    """
    if _CTX.blob_store is None:
        raise RuntimeError("worker has no blob store configured")
    import json

    return await _CTX.blob_store.put(
        inp.tenant, json.dumps(inp.value, sort_keys=True).encode()
    )


async def callHand(inp: CallHandInput) -> Any:
    ref = toolref_from_json(inp.tool_ref)
    key = toolref_key(ref)

    if inp.tool_ref.get("kind") == "mcp":
        if _CTX.mcp_call is None:
            raise RuntimeError("worker has no MCP caller configured")
        server = inp.tool_ref["server"]
        tool = inp.tool_ref["tool"]
        return await _CTX.mcp_call(server, tool, inp.value, inp.cid)

    # Native hand: HTTP POST with an idempotency key derived from the cid.
    url = _CTX.hand_urls.get(key)
    if url is None:
        raise RuntimeError(f"no URL registered for native hand {key!r}")
    if _CTX.capabilities is not None and not _CTX.capabilities.network_allows(_domain_of(url)):
        raise CapabilityDenied(f"network egress to {_domain_of(url)!r} is not granted")

    import httpx  # imported in-activity so the module loads without httpx

    logger.debug("callHand %s -> %s", key, url)
    async with httpx.AsyncClient(timeout=_CTX.http_timeout_s) as client:
        body = {"input": inp.value}
        if inp.cache is not None:
            body["cache"] = inp.cache
        resp = await client.post(
            url,
            json=body,
            headers={"Idempotency-Key": inp.cid},
        )
        resp.raise_for_status()
        return resp.json()


async def invokeBrain(inp: InvokeBrainInput) -> Any:
    if _CTX.llm is None:
        raise RuntimeError("worker has no LLM caller configured")
    brain = rendered_brain_for(_registry().get_brain(inp.brain), inp.value)
    return await _CTX.llm(brain, inp.value)


async def compilePlan(inp: CompilePlanInput) -> dict[str, Any]:
    """Run the planner brain, parse its Plan, admit it (§8), return plan JSON.

    Admission happens here, in an activity, so a rejected plan fails the activity
    (and surfaces as a clean ``PlanRejected``) instead of corrupting the
    deterministic workflow.
    """
    if _CTX.llm is None:
        raise RuntimeError("worker has no LLM caller configured")
    planner = _registry().get_brain(inp.planner)
    raw = await _CTX.llm(planner, inp.value)

    plan_json = raw["plan"] if isinstance(raw, dict) and "plan" in raw else raw
    plan = Node.from_json(plan_json)

    if _CTX.capabilities is not None:
        from ..contracts import manifest_from_json  # local import keeps hot path light

        manifest = manifest_from_json(inp.manifest) if inp.manifest else None
        plan = admit_plan(plan, _CTX.capabilities, manifest)

    return plan.to_json()


async def verifyPures(pinned: dict[str, str]) -> None:
    """Verify deploy-pinned pure source hashes against this worker's registry."""
    registered: dict[str, str] = {}
    registry = _registry()
    for name in pinned:
        try:
            registered[name] = registry.source_hash_of(name)
        except KeyError:
            pass

    drift = registry.diff_pure_hashes(pinned, registered)
    if drift:
        details = "; ".join(
            (
                f"{item['name']}: pinned={item['pinned']} "
                f"actual={item['actual'] if item['actual'] is not None else '<missing>'}"
            )
            for item in drift
        )
        raise PureDriftError(f"pure source drift detected: {details}")


async def resolveSubflow(ref: str) -> dict[str, Any]:
    """Resolve a sub-flow ref to its frozen IR + manifest (deploy-time registry).

    Done in an activity, not in the child workflow, so the (constant) registry
    lookup stays outside the deterministic sandbox. The returned ``flowJson`` is
    already frozen — the child runs it directly.
    """
    spec = _CTX.subflows.get(ref)
    if spec is None:
        raise RuntimeError(f"no sub-flow registered for ref {ref!r}")
    return {
        "flowJson": spec["flowJson"],
        "manifestJson": spec.get("manifestJson", {}),
        "pinnedPures": spec.get("pinnedPures", spec.get("pureSourceHashes")),
    }


def _approval_value(raw: Any) -> bool:
    if isinstance(raw, str):
        return raw.lower() in {"1", "true", "yes", "required"}
    return bool(raw)


def _contract_payload(contract: ToolContract, *, approval: Optional[bool] = None) -> dict[str, Any]:
    payload = contract.to_json()
    if approval is not None:
        payload["approval"] = bool(approval)
    return payload


def _grant_contract_payload(grant: ToolGrant) -> dict[str, Any]:
    payload = _contract_payload(
        grant.contract() or CONSERVATIVE_DEFAULT,
        approval=grant.approval,
    )
    if grant.max_calls is not None:
        payload["maxCalls"] = grant.max_calls
    return payload


def _normalize_contract_payload(raw: Any) -> dict[str, Any]:
    if isinstance(raw, ToolContract):
        return raw.to_json()
    if not isinstance(raw, dict):
        return CONSERVATIVE_DEFAULT.to_json()
    payload = {
        "effect": Effect(raw.get("effect", CONSERVATIVE_DEFAULT.effect.value)).value,
        "idempotency": Idempotency(
            raw.get("idempotency", CONSERVATIVE_DEFAULT.idempotency.value)
        ).value,
    }
    if "approval" in raw:
        payload["approval"] = _approval_value(raw["approval"])
    max_calls = raw.get("maxCalls", raw.get("max_calls"))
    if max_calls is not None:
        payload["maxCalls"] = int(max_calls)
    return payload


async def resolveRuntimeCapabilities() -> dict[str, Any]:
    """Resolve deterministic workflow policy derived from worker capabilities."""
    if _CTX.capabilities is None:
        return {"maxCalls": {}}
    return {"maxCalls": _CTX.capabilities.max_call_limits()}


async def resolveAgentSpec(controller: str) -> dict[str, Any]:
    """Resolve an agent controller to its loop config + granted-tool allow-list.

    The budget defaults to the worker's active capability budget when the
    registered spec does not pin one, so an agent inherits the deployment's
    spend ceiling unless told otherwise.
    """
    spec = _CTX.agents.get(controller, {})
    config = dict(spec.get("config") or {})
    if "budget" not in config and _CTX.capabilities is not None and _CTX.capabilities.budget is not None:
        b = _CTX.capabilities.budget
        budget: dict[str, Any] = {}
        if b.cost is not None:
            budget["cost"] = b.cost
        if b.tokens is not None:
            budget["tokens"] = b.tokens
        if b.wall_seconds is not None:
            budget["wallSeconds"] = b.wall_seconds
        config["budget"] = budget

    if "grantedTools" in spec:
        granted = spec.get("grantedTools")
    elif _CTX.capabilities is not None and _CTX.capabilities._has_tools:
        granted = list(_CTX.capabilities.tools.keys())
    else:
        granted = None
    capability_tools = (
        list(_CTX.capabilities.tools.keys())
        if _CTX.capabilities is not None and _CTX.capabilities._has_tools
        else None
    )

    contracts: dict[str, dict[str, Any]] = {}
    if _CTX.capabilities is not None:
        contracts.update(
            {
                key: _grant_contract_payload(grant)
                for key, grant in _CTX.capabilities.tools.items()
            }
        )
    contracts.update(
        {
            key: _normalize_contract_payload(raw)
            for key, raw in (spec.get("grantedContracts") or {}).items()
        }
    )

    if "grantedSubflows" in spec:
        granted_subflows = spec.get("grantedSubflows")
    elif _CTX.capabilities is not None and _CTX.capabilities._has_subflows:
        granted_subflows = sorted(_CTX.capabilities.subflows)
    else:
        granted_subflows = None
    capability_subflows = (
        sorted(_CTX.capabilities.subflows)
        if _CTX.capabilities is not None and _CTX.capabilities._has_subflows
        else None
    )

    return {
        "config": config,
        "grantedTools": None if granted is None else list(granted),
        "capabilityTools": None if capability_tools is None else list(capability_tools),
        "grantedContracts": contracts,
        "grantedSubflows": None if granted_subflows is None else list(granted_subflows),
        "capabilitySubflows": None if capability_subflows is None else list(capability_subflows),
    }


def toolref_json_from_key(key: str) -> dict[str, Any]:
    """Reverse of :func:`~composable_agents.ir.toolref_key`.

    ``"server/tool"`` is an MCP tool; a bare name is a native hand.
    """
    if "/" in key:
        server, tool = key.split("/", 1)
        return {"kind": "mcp", "server": server, "tool": tool}
    return {"kind": "native", "name": key}
