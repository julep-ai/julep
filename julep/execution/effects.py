"""Backend-neutral effect implementations (the Tools + Reasoners boundary).

These are the bodies of the Temporal activities, factored out so any durable
backend (Temporal, DBOS) can wrap them in its own retry/checkpoint unit.
This module must never import an engine: no temporalio, no dbos.
Configuration is process-global via :func:`configure` (one WorkerContext per
worker process), exactly as before.
"""

from __future__ import annotations

import inspect
import json
import logging
import os
import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional, Protocol, cast

from .. import agent_loop as al
from ..capabilities import CapabilityManifest, ToolGrant
from ..contracts import CONSERVATIVE_DEFAULT, ToolContract
from ..dotctx import Reasoner
from ..errors import CapabilityDenied, PlanRejected, PureDriftError, ToolInputValidation
from ..ir import Ann, ContextPolicy, Node, canonical_json, toolref_from_json, toolref_key
from ..kinds import ContextScope, Effect, Idempotency
from ..qos import ReasonerDispatch, QoSTier, default_resolve_qos
from ..registry import DEFAULT_REGISTRY, Registry
from ..resilience import AttemptRecord, OnAttempt
from ..prompt import rendered_reasoner_for, rendered_user_for
from ..staged import admit_plan
from ..trajectory import (
    Redactor,
    TrajectoryRun,
    TrajectorySink,
    TrajectoryStep,
    TrajectoryValue,
    _REDACTION_DROP,
    _best_effort,
    redact_for_capture,
    redact_secret_shaped,
)
from ..transcript import (
    SUMMARY_KEY,
    Transcript,
    approx_token_count,
    elision_marker,
    is_controller_value,
    render_opening_ask,
    split_to_budget,
    summary_turn,
)
from ..artifact_store import artifact_store_from_url
from ..worker_store import bundle_ref_entries, resolve_entries
from .blobstore import BlobStore, parse_ref
from .llm_result import LlmResult
from .session_store import SessionStore, _canonical_json_text

logger = logging.getLogger("julep.execution.effects")

# An opaque, JSON-serializable tenant/credential *reference* supplied at
# dispatch and threaded through workflow input into every effect payload. The
# framework never interprets it, and it must never contain a secret: Temporal
# history is a durable, replayable record — carry a token *ref* and let the
# worker resolve the actual credential at call time.
RunPrincipal = dict[str, Any]

# Caller signatures the worker supplies.
# (server, tool, args, key, principal, run_secrets, input_schema_validated) -> result
McpCaller = Callable[
    [
        str,
        str,
        Any,
        str,
        Optional[RunPrincipal],
        Optional[dict[str, str]],
        bool,
    ],
    Awaitable[Any],
]


# ``transcript`` is the hydrated, budget-bounded neutral turn list for
# transcript-scoped app rounds (None everywhere else); the caller maps it to
# its provider's wire format. ``tools`` is the frozen provider-neutral native
# tool surface for agent rounds (None everywhere else).
class LlmCaller(Protocol):
    """Canonical model seam used by workers and local execution."""

    def __call__(
        self,
        reasoner: Reasoner,
        value: Any,
        principal: Optional[RunPrincipal],
        transcript: Optional[Transcript],
        dispatch: ReasonerDispatch,
        *,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> Awaitable[Any]: ...


@dataclass
class WorkerContext:
    """Process-global configuration read by the activities.

    ``mcp_call`` receives ``(server, tool, value, idempotency_key, principal,
    run_secrets, input_schema_validated)``.
    The key is the deterministic activation ``cid`` from :class:`CallToolInput`;
    Temporal retries re-invoke the activity with the same input, so MCP retry
    keys are stable by construction. MCP now carries the key, so MCP tools that
    require transport-level idempotency are admissible. ``principal`` is the
    run's :data:`RunPrincipal` (or ``None``); legacy 4-argument callers are
    wrapped once by :func:`configure` and keep working unchanged.
    """

    tool_urls: dict[str, str] = field(default_factory=dict)  # native name -> URL
    mcp_call: Optional[McpCaller] = None
    # Optional explicit discovery seam for run-start MCP preflight.  The
    # standard http_mcp_caller also exposes its transport on the callable.
    mcp_transport: Optional[Any] = None
    llm: Optional[LlmCaller] = None
    on_attempt: Optional[OnAttempt] = None
    # QoS resolver seam for reasoner dispatch; deployments can override it with
    # deploy/runtime policy beyond the default principal + annotation rule.
    resolve_qos: Callable[..., QoSTier] = field(default=default_resolve_qos)
    blob_store: Optional[BlobStore] = None
    session_store: Optional[SessionStore] = None
    capabilities: Optional[CapabilityManifest] = None
    registry: Optional[Registry] = None
    http_timeout_s: float = 30.0
    # Resolves the run principal into extra transport headers for native tools.
    # Absent means no extra headers; native tools keep working unchanged.
    principal_headers: Optional[Callable[[RunPrincipal], dict[str, str]]] = None
    # Tokenizer hook for transcript budgets (text -> token count). Absent means
    # the char heuristic (transcript.approx_token_count); the real count is the
    # LlmCaller's business.
    count_tokens: Optional[Callable[[str], int]] = None
    # Deploy-time registries. A sub-flow is a separately frozen flow addressable
    # by ref; an agent spec is the controller's loop policy. Both are fixed at
    # worker startup, so the resolve* activities below read them deterministically.
    # ref -> {flowJson, manifestJson, pureSourceHashes?, bundle?}
    subflows: dict[str, dict[str, Any]] = field(default_factory=dict)
    # controller -> {config, grantedTools, grantedContracts, grantedSubflows, subflowQueues}
    agents: dict[str, dict[str, Any]] = field(default_factory=dict)
    trajectory_sink: Optional[TrajectorySink] = None
    trajectory_blob_store: Optional[BlobStore] = None
    # Injectable trajectory redactor; None uses redact_secret_shaped at the
    # capture seam before every blob put. A raising redactor fails closed.
    redactor: Optional[Redactor] = None


@dataclass
class VerifyPuresInput:
    pinned: dict[str, str]
    bundle: Optional[list[dict[str, str]]] = None
    flow_json: Optional[dict[str, Any]] = None
    artifact_hash: Optional[str] = None


_CTX = WorkerContext()
_TRAJECTORY_SINK: Optional[TrajectorySink] = None
_TRAJECTORY_BLOB_STORE: Optional[BlobStore] = None
_TRAJECTORY_REDACTOR: Optional[Redactor] = None
_DEFAULT_REASONER_DISPATCH = ReasonerDispatch()
_JULEP_META_KEY = "__julep_meta__"
_RUNTIME_DECLARATIONS_CACHE: dict[str, tuple[int, Registry]] = {}


def _unwrap_llm(out: Any) -> tuple[Any, dict[str, Any]]:
    """Accept either an LlmResult or a bare reply (back-compat for fake callers)."""
    if isinstance(out, LlmResult):
        return out.reply, out.meta.to_attrs()
    return out, {}


def _with_julep_meta(value: Any, attrs: dict[str, Any]) -> Any:
    if not attrs:
        return value
    if isinstance(value, dict) and _JULEP_META_KEY in value and "reply" in value:
        meta = value[_JULEP_META_KEY]
        existing = dict(meta) if isinstance(meta, dict) else {"meta": meta}
        return {**value, _JULEP_META_KEY: {**existing, **attrs}}
    if isinstance(value, dict) and SUMMARY_KEY in value and "reply" in value:
        return {**value, _JULEP_META_KEY: attrs}
    return {"reply": value, _JULEP_META_KEY: attrs}


def set_trajectory_sink(
    sink: Optional[TrajectorySink],
    blob_store: Optional[BlobStore] = None,
    redactor: Optional[Redactor] = None,
) -> None:
    """Install a process-wide trajectory sink (+ optional blob store for value refs).

    Best-effort capture only: a missing sink disables capture entirely. Mirrors
    julep.execution.dbos_backend.set_projection_sink. ``redactor``
    overrides the default secret-shaped-key scrubber for trajectory blobs.
    """
    global _TRAJECTORY_SINK, _TRAJECTORY_BLOB_STORE, _TRAJECTORY_REDACTOR
    _TRAJECTORY_SINK = sink
    _TRAJECTORY_BLOB_STORE = blob_store
    _TRAJECTORY_REDACTOR = redactor


def _accepts_positional(fn: Callable[..., Any], arity: int) -> bool:
    """True when ``fn`` can take ``arity`` positional arguments (new signature)."""
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):  # uninspectable callables: assume new-style
        return True
    positional = 0
    for param in sig.parameters.values():
        if param.kind is inspect.Parameter.VAR_POSITIONAL:
            return True
        if param.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            positional += 1
    return positional >= arity


def _accepts_keyword(fn: Callable[..., Any], keyword: str) -> bool:
    """True when ``fn`` declares ``keyword`` or accepts arbitrary keywords."""
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):  # uninspectable callables: assume canonical
        return True
    if any(param.kind is inspect.Parameter.VAR_KEYWORD for param in sig.parameters.values()):
        return True
    param = sig.parameters.get(keyword)
    return param is not None and param.kind in (
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.KEYWORD_ONLY,
    )


def _predictive_qos_kwargs(
    fn: Callable[..., Any],
    *,
    timeout_s: Optional[float],
    min_batch_window_s: Optional[float],
) -> dict[str, Any]:
    """Select the predictive-clamp kwargs a QoS resolver actually accepts.

    A legacy resolver accepts neither; a resolver with ``**kwargs`` accepts both;
    a resolver that declares only one of the two gets only that one. This keeps a
    resolver like ``def r(..., *, timeout_s=None)`` from raising on the unknown
    ``min_batch_window_s``.
    """
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return {}
    if any(param.kind is inspect.Parameter.VAR_KEYWORD for param in sig.parameters.values()):
        return {"timeout_s": timeout_s, "min_batch_window_s": min_batch_window_s}
    out: dict[str, Any] = {}
    if "timeout_s" in sig.parameters:
        out["timeout_s"] = timeout_s
    if "min_batch_window_s" in sig.parameters:
        out["min_batch_window_s"] = min_batch_window_s
    return out


def _adapt_mcp_caller(fn: Callable[..., Awaitable[Any]]) -> McpCaller:
    if _accepts_positional(fn, 7):
        return fn

    if _accepts_positional(fn, 6):

        async def run_secret_aware(
            server: str,
            tool: str,
            value: Any,
            key: str,
            principal: Optional[RunPrincipal],
            run_secrets: Optional[dict[str, str]],
            input_schema_validated: bool,
        ) -> Any:
            del input_schema_validated
            return await fn(server, tool, value, key, principal, run_secrets)

        return run_secret_aware

    if _accepts_positional(fn, 5):

        async def principal_aware(
            server: str,
            tool: str,
            value: Any,
            key: str,
            principal: Optional[RunPrincipal],
            run_secrets: Optional[dict[str, str]],
            input_schema_validated: bool,
        ) -> Any:
            del run_secrets, input_schema_validated
            return await fn(server, tool, value, key, principal)

        return principal_aware

    async def legacy(
        server: str,
        tool: str,
        value: Any,
        key: str,
        principal: Optional[RunPrincipal],
        run_secrets: Optional[dict[str, str]],
        input_schema_validated: bool,
    ) -> Any:
        del principal, run_secrets, input_schema_validated
        return await fn(server, tool, value, key)

    return legacy


def _reject_transcript(fn: Callable[..., Awaitable[Any]]) -> RuntimeError:
    return RuntimeError(
        f"this worker's LlmCaller {getattr(fn, '__name__', fn)!r} does not accept a "
        "transcript, but a transcript-scoped app round produced one; update the "
        "caller to the canonical form "
        "(reasoner, value, principal, transcript, dispatch, *, tools=None)"
    )


def _reject_tools(fn: Callable[..., Awaitable[Any]]) -> RuntimeError:
    return RuntimeError(
        f"this worker's LlmCaller {getattr(fn, '__name__', fn)!r} does not accept "
        "tools=, but a native-tool agent round produced a frozen tool surface; "
        "update the caller to the canonical form "
        "(reasoner, value, principal, transcript, dispatch, *, tools=None)"
    )


def _llm_tool_kwargs(
    fn: Callable[..., Awaitable[Any]],
    *,
    accepts_tools: bool,
    tools: Optional[list[dict[str, Any]]],
) -> dict[str, Any]:
    if tools is None:
        return {}
    if not accepts_tools:
        raise _reject_tools(fn)
    return {"tools": tools}


def _adapt_llm_caller(fn: Callable[..., Awaitable[Any]]) -> LlmCaller:
    """Adapt legacy callers to the canonical :class:`LlmCaller` form."""
    accepts_tools = _accepts_keyword(fn, "tools")

    if _accepts_positional(fn, 5):
        if accepts_tools:
            # Already canonical. Returning it unchanged makes configure()
            # idempotent when gateways temporarily install and later restore
            # the same WorkerContext.
            return cast(LlmCaller, fn)

        async def canonical(
            reasoner: Reasoner,
            value: Any,
            principal: Optional[RunPrincipal],
            transcript: Optional[Transcript],
            dispatch: ReasonerDispatch = _DEFAULT_REASONER_DISPATCH,
            *,
            tools: Optional[list[dict[str, Any]]] = None,
        ) -> Any:
            kwargs = _llm_tool_kwargs(fn, accepts_tools=accepts_tools, tools=tools)
            return await fn(reasoner, value, principal, transcript, dispatch, **kwargs)

        return canonical

    if _accepts_positional(fn, 4):

        async def transcript_aware(
            reasoner: Reasoner,
            value: Any,
            principal: Optional[RunPrincipal],
            transcript: Optional[Transcript],
            dispatch: ReasonerDispatch = _DEFAULT_REASONER_DISPATCH,
            *,
            tools: Optional[list[dict[str, Any]]] = None,
        ) -> Any:
            del dispatch
            kwargs = _llm_tool_kwargs(fn, accepts_tools=accepts_tools, tools=tools)
            return await fn(reasoner, value, principal, transcript, **kwargs)

        return transcript_aware

    if _accepts_positional(fn, 3):
        # Principal-aware caller from the run-principal design. No silent drop:
        # a transcript it cannot receive is a hard error (G-8).
        async def principal_aware(
            reasoner: Reasoner,
            value: Any,
            principal: Optional[RunPrincipal],
            transcript: Optional[Transcript],
            dispatch: ReasonerDispatch = _DEFAULT_REASONER_DISPATCH,
            *,
            tools: Optional[list[dict[str, Any]]] = None,
        ) -> Any:
            del dispatch
            if transcript is not None:
                raise _reject_transcript(fn)
            kwargs = _llm_tool_kwargs(fn, accepts_tools=accepts_tools, tools=tools)
            return await fn(reasoner, value, principal, **kwargs)

        return principal_aware

    async def legacy(
        reasoner: Reasoner,
        value: Any,
        principal: Optional[RunPrincipal],
        transcript: Optional[Transcript],
        dispatch: ReasonerDispatch = _DEFAULT_REASONER_DISPATCH,
        *,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> Any:
        del dispatch
        if transcript is not None:
            raise _reject_transcript(fn)
        kwargs = _llm_tool_kwargs(fn, accepts_tools=accepts_tools, tools=tools)
        return await fn(reasoner, value, **kwargs)

    return legacy


def configure(ctx: WorkerContext) -> None:
    """Install the worker-wide context the activities read.

    Legacy callers (``mcp_call`` without the trailing ``principal``; ``llm``
    taking ``(reasoner, value)``, ``(reasoner, value, principal)``, or
    ``(reasoner, value, principal, transcript)``) are wrapped here, once, so they
    keep working unchanged. The canonical ``llm`` form is
    ``(reasoner, value, principal, transcript, dispatch, *, tools=None)``;
    wrapped narrower callers fail fast if a transcript-scoped app round gives
    them a transcript or a native-tool round gives them tools they cannot accept.
    """
    global _CTX
    if ctx.mcp_call is not None:
        ctx.mcp_call = _adapt_mcp_caller(ctx.mcp_call)
    if ctx.llm is not None:
        ctx.llm = _adapt_llm_caller(ctx.llm)
    _CTX = ctx
    _RUNTIME_DECLARATIONS_CACHE.clear()
    set_trajectory_sink(
        ctx.trajectory_sink,
        ctx.trajectory_blob_store or ctx.blob_store,
        ctx.redactor,
    )


def _registry() -> Registry:
    return _CTX.registry or DEFAULT_REGISTRY


def _hydrate_runtime_declarations(ref: Optional[Mapping[str, Any]]) -> Registry:
    """Load and return one release-scoped declaration registry."""

    if ref is None:
        return _registry()
    if not isinstance(ref, Mapping) or set(ref) != {"hash", "size"}:
        raise RuntimeError("runtime declarations ref must contain exactly 'hash' and 'size'")
    expected_hash = ref.get("hash")
    expected_size = ref.get("size")
    if (
        not isinstance(expected_hash, str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", expected_hash) is None
    ):
        raise RuntimeError("runtime declarations ref hash must be sha256:<64 lowercase hex>")
    if not isinstance(expected_size, int) or isinstance(expected_size, bool) or expected_size < 0:
        raise RuntimeError("runtime declarations ref size must be a non-negative integer")
    cached = _RUNTIME_DECLARATIONS_CACHE.get(expected_hash)
    if cached is not None:
        cached_size, cached_registry = cached
        if cached_size != expected_size:
            raise RuntimeError(
                f"runtime declarations ref size mismatch for {expected_hash}: "
                f"expected {expected_size}, cached {cached_size}"
            )
        return cached_registry

    store_url = os.environ.get("JULEP_ARTIFACT_STORE_URL", "").strip()
    if not store_url:
        raise RuntimeError("runtime declarations hydration requires JULEP_ARTIFACT_STORE_URL")
    blob = artifact_store_from_url(store_url).get(expected_hash.removeprefix("sha256:"))
    if len(blob) != expected_size:
        raise RuntimeError(
            f"runtime declarations blob size mismatch for {expected_hash}: "
            f"expected {expected_size}, got {len(blob)}"
        )
    from ..declarations import load_declarations

    release_registry = Registry()
    load_declarations(
        blob,
        expected_hash=expected_hash,
        registry=release_registry,
        release_scoped=True,
    )
    _RUNTIME_DECLARATIONS_CACHE[expected_hash] = (expected_size, release_registry)
    return release_registry


def _notify_attempt(record: AttemptRecord) -> None:
    if _CTX.on_attempt is not None:
        _CTX.on_attempt(record)


def _domain_of(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).hostname or ""


# --------------------------------------------------------------------------- #
# Payloads (Temporal serializes these to/from the data converter).
# --------------------------------------------------------------------------- #
@dataclass
class CallToolInput:
    tool_ref: dict[str, Any]  # ToolRef JSON (native or mcp)
    value: Any
    cid: str  # deterministic activation id -> Idempotency-Key
    # Advisory CacheHint JSON. The tool/transport may honor it; the framework
    # does not provide a cache backend or change replay behavior from this hint.
    cache: Optional[dict[str, Any]] = None
    principal: Optional[RunPrincipal] = None  # run principal (opaque, never a secret)
    run_id: Optional[str] = None
    root_run_id: Optional[str] = None
    segment_seq: Optional[int] = None
    node_id: Optional[str] = None
    op: Optional[str] = None
    kind: Optional[str] = None
    causes: tuple[str, ...] = ()
    secrets: Optional[dict[str, str]] = None
    # Optional activity-side gate for callers that cannot validate in workflow
    # code. AgentWorkflow normally uses validateJsonSchema first and then sets
    # ``input_schema_validated``; ordinary authored flows do not claim this.
    frozen_input_schema: Optional[dict[str, Any]] = None
    # Workflow code may set this only after validating against a frozen schema.
    input_schema_validated: bool = False


@dataclass
class InvokeReasonerInput:
    reasoner: str
    value: Any
    cid: str
    principal: Optional[RunPrincipal] = None
    # Transcript plan for transcript-scoped app rounds (agent-transcripts
    # design): ref-bearing turns projected deterministically in workflow code.
    # invokeReasoner hydrates the refs, enforces ctx.max_tokens, and (SUMMARY
    # scope) folds elided turns into the running summary via ``summarizer``.
    transcript: Optional[list[dict[str, Any]]] = None
    ctx: Optional[dict[str, Any]] = None  # ContextPolicy JSON (scope + maxTokens)
    summarizer: Optional[str] = None  # named summarizer reasoner (SUMMARY scope)
    summary: Optional[str] = None  # running summary from AgentState
    tools: Optional[list[dict[str, Any]]] = None
    run_id: Optional[str] = None
    root_run_id: Optional[str] = None
    segment_seq: Optional[int] = None
    node_id: Optional[str] = None
    op: Optional[str] = None
    kind: Optional[str] = None
    causes: tuple[str, ...] = ()
    # Recorded QoS tier (M0: advisory; dispatch still sync). Carried so the
    # reasoner step input reflects the resolved tier deterministically.
    qos: Optional[str] = None
    runtime_declarations_ref: Optional[dict[str, Any]] = None
    secrets: Optional[dict[str, str]] = None


@dataclass
class ResolveQoSInput:
    reasoner: str
    node_batchable: bool = False
    principal: Optional[RunPrincipal] = None
    cid: Optional[str] = None
    run_id: Optional[str] = None
    root_run_id: Optional[str] = None
    segment_seq: Optional[int] = None
    node_id: Optional[str] = None
    timeout_s: Optional[float] = None
    runtime_declarations_ref: Optional[dict[str, Any]] = None


@dataclass
class CompilePlanInput:
    planner: str
    value: Any
    cid: str
    manifest: Optional[dict[str, Any]] = None  # parent frozen manifest (for schema checks)
    principal: Optional[RunPrincipal] = None
    runtime_declarations_ref: Optional[dict[str, Any]] = None


@dataclass
class RunSubInput:
    ref: str
    value: Any
    cid: str
    principal: Optional[RunPrincipal] = None
    run_id: Optional[str] = None
    root_run_id: Optional[str] = None
    segment_seq: Optional[int] = None
    node_id: Optional[str] = None
    op: Optional[str] = None
    kind: Optional[str] = None
    causes: tuple[str, ...] = ()
    secrets: Optional[dict[str, str]] = None


@dataclass
class ResolveAgentSpecInput:
    controller: str
    runtime_declarations_ref: Optional[dict[str, Any]] = None


@dataclass
class ValidateJsonSchemaInput:
    value: Any
    schema: dict[str, Any]


# Compatibility name for histories/workers that registered the narrower
# output-only activity while the validator was first introduced.
ValidateAgentOutputInput = ValidateJsonSchemaInput


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
class LoadValueInput:
    session_id: str
    cursor: int


@dataclass
class CommitValueInput:
    session_id: str
    base: int
    value: Any
    value_hash: str


@dataclass
class PutBlobInput:
    tenant: str
    value: Any
    secrets: Optional[dict[str, str]] = None


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
    return await _CTX.session_store.commit(inp.session_id, inp.base, state, inp.state_hash)


async def loadValue(inp: LoadValueInput) -> Any:
    if _CTX.session_store is None:
        raise RuntimeError("worker has no session store configured")
    return await _CTX.session_store.load_value(inp.session_id, inp.cursor)


async def commitValue(inp: CommitValueInput) -> int:
    if _CTX.session_store is None:
        raise RuntimeError("worker has no session store configured")
    return await _CTX.session_store.commit_value(
        inp.session_id, inp.base, inp.value, inp.value_hash
    )


async def putBlob(inp: PutBlobInput) -> str:
    """JSON-canonical claim check for trace/context refs (``trace_content_refs``).

    Refs address the compact canonical JSON encoding — a deliberately distinct
    ref-space from the wire codec's raw-payload refs (``codec.py``);
    non-JSON values are rejected loudly (``TypeError``).
    """
    if _CTX.blob_store is None:
        raise RuntimeError("worker has no blob store configured")

    redactor = _scoped_redactor(inp.secrets)
    redacted = redact_for_capture(redactor, inp.value)
    if redacted is _REDACTION_DROP:
        redacted = None
    return await _CTX.blob_store.put(inp.tenant, _canonical_json_text(redacted).encode())


def _scoped_redactor(secrets: Optional[Mapping[str, str]]) -> Redactor:
    """Compose per-run value scrubbing without mutating global state."""
    from ..secrets import operator_secret_redactor

    base = operator_secret_redactor(_TRAJECTORY_REDACTOR or redact_secret_shaped)
    if not secrets:
        return base
    from ..secrets import scrubber_for_values

    return scrubber_for_values(secrets.values(), base=base)


async def _capture_effect(
    *,
    op: str,
    kind: str,
    node_id: Optional[str],
    cid: str,
    run_id: Optional[str],
    root_run_id: Optional[str],
    segment_seq: Optional[int],
    causes: tuple[str, ...],
    input_value: Any,
    output_value: Any,
    secrets: Optional[Mapping[str, str]] = None,
) -> None:
    """Best-effort trajectory capture for one effect activation.

    Lives only in the effect layer, so both the Temporal and DBOS backends
    (which both call effects.callTool / effects.invokeReasoner) get capture for
    free. NEVER raises into the run: every sink/blob op is wrapped in the
    shared trajectory._best_effort helper, so a failing sink or blob leaves the
    effect result byte-identical.
    """
    sink = _TRAJECTORY_SINK
    if sink is None or root_run_id is None:
        return

    blob_store = _TRAJECTORY_BLOB_STORE
    effective_run_id = run_id or root_run_id
    seg = segment_seq if segment_seq is not None else 0
    step_id = f"{effective_run_id}:s{seg}:{cid}"

    # Lazy run-start: upsert the TrajectoryRun on the first step we see for this
    # run id, so the run tree (parent_run_id) exists for
    # list_trajectory_steps(include_children=True). A child run (run_id !=
    # root_run_id) links to the root so descendants resolve from the root run.
    # Best-effort like every other sink op: a failing start_run never breaks the
    # run, and a re-seen run id is left untouched (no payload buffering).
    if _best_effort(lambda: sink.get_trajectory_run(effective_run_id)) is None:
        _parent = root_run_id if effective_run_id != root_run_id else None
        _best_effort(
            lambda: sink.start_run(
                TrajectoryRun(
                    run_id=effective_run_id,
                    root_run_id=root_run_id,
                    parent_run_id=_parent,
                    session_id=effective_run_id,
                )
            )
        )

    async def _put_best_effort(value: Any) -> Optional[str]:
        if blob_store is None:
            return None
        redactor = _scoped_redactor(secrets)
        redacted = redact_for_capture(redactor, value)
        if redacted is _REDACTION_DROP:
            return None
        try:
            return await blob_store.put(root_run_id, json.dumps(redacted, sort_keys=True).encode())
        except Exception as exc:
            # Mirror trajectory._best_effort: swallow + count + log.
            from ..trajectory import _best_effort as _be

            def _reraise(e: BaseException = exc) -> None:
                raise e

            _be(_reraise)
            return None

    input_ref = await _put_best_effort(input_value)
    output_ref = await _put_best_effort(output_value)

    step = TrajectoryStep(
        step_id=step_id,
        run_id=effective_run_id,
        root_run_id=root_run_id,
        cid=cid,
        node_id=node_id or cid,
        op=op,
        kind=kind,
        causes=tuple(causes),
        status="did",
        input_ref=input_ref,
        output_ref=output_ref,
    )
    _best_effort(lambda: sink.append_steps([step]))

    values: list[TrajectoryValue] = []
    if input_ref is not None:
        values.append(
            TrajectoryValue(ref=input_ref, root_run_id=root_run_id, step_id=step_id, kind="input")
        )
    if output_ref is not None:
        values.append(
            TrajectoryValue(ref=output_ref, root_run_id=root_run_id, step_id=step_id, kind="output")
        )
    if values:
        _best_effort(lambda: sink.record_values(values))


async def record_marker_step(
    *,
    kind: str,
    run_id: Optional[str],
    root_run_id: Optional[str],
    segment_seq: Optional[int],
    value: Any,
    cid: str,
    value_kind: str,
    secrets: Optional[Mapping[str, str]] = None,
) -> None:
    """Best-effort synthetic trajectory marker for root input / final output.

    This lives beside effect capture because it uses the same sink/blob plane,
    but callers invoke it only from activity/step bodies so workflow replay is
    not coupled to IO or sink state.
    """
    sink = _TRAJECTORY_SINK
    if sink is None or root_run_id is None:
        return

    blob_store = _TRAJECTORY_BLOB_STORE
    effective_run_id = run_id or root_run_id
    seg = segment_seq if segment_seq is not None else 0
    step_id = f"{effective_run_id}:s{seg}:{cid}"

    if _best_effort(lambda: sink.get_trajectory_run(effective_run_id)) is None:
        _parent = root_run_id if effective_run_id != root_run_id else None
        _best_effort(
            lambda: sink.start_run(
                TrajectoryRun(
                    run_id=effective_run_id,
                    root_run_id=root_run_id,
                    parent_run_id=_parent,
                    session_id=effective_run_id,
                )
            )
        )

    ref: Optional[str] = None
    if blob_store is not None:
        redactor = _scoped_redactor(secrets)
        redacted = redact_for_capture(redactor, value)
        if redacted is not _REDACTION_DROP:
            try:
                ref = await blob_store.put(
                    root_run_id, json.dumps(redacted, sort_keys=True).encode()
                )
            except Exception as exc:

                def _reraise(e: BaseException = exc) -> None:
                    raise e

                _best_effort(_reraise)

    step = TrajectoryStep(
        step_id=step_id,
        run_id=effective_run_id,
        root_run_id=root_run_id,
        cid=cid,
        node_id=cid,
        op=kind,
        kind=kind,
        status="did",
        input_ref=ref if kind == "root" else None,
        output_ref=ref if kind == "final" else None,
    )
    _best_effort(lambda: sink.append_steps([step]))
    if ref is not None:
        _best_effort(
            lambda: sink.record_values(
                [
                    TrajectoryValue(
                        ref=ref,
                        root_run_id=root_run_id,
                        step_id=step_id,
                        kind=value_kind,
                    )
                ]
            )
        )


async def callTool(inp: CallToolInput) -> Any:
    ref = toolref_from_json(inp.tool_ref)
    key = toolref_key(ref)

    if inp.tool_ref.get("kind") == "mcp":
        if _CTX.mcp_call is None:
            raise RuntimeError("worker has no MCP caller configured")
        server = inp.tool_ref["server"]
        tool = inp.tool_ref["tool"]
        input_schema_validated = inp.input_schema_validated
        if inp.frozen_input_schema is not None:
            from .llm import json_schema_error

            if json_schema_error(inp.value, inp.frozen_input_schema) is not None:
                raise ToolInputValidation(server, tool)
            input_schema_validated = True
        result = await _CTX.mcp_call(
            server,
            tool,
            inp.value,
            inp.cid,
            inp.principal,
            inp.secrets,
            input_schema_validated,
        )
    else:
        # Native tool: HTTP POST with an idempotency key derived from the cid.
        url = _CTX.tool_urls.get(key)
        if url is None:
            raise RuntimeError(f"no URL registered for native tool {key!r}")
        if _CTX.capabilities is not None and not _CTX.capabilities.network_allows(_domain_of(url)):
            raise CapabilityDenied(f"network egress to {_domain_of(url)!r} is not granted")

        import httpx  # imported in-activity so the module loads without httpx

        logger.debug("callTool %s -> %s", key, url)
        headers = {"Idempotency-Key": inp.cid}
        if inp.principal is not None and _CTX.principal_headers is not None:
            headers.update(_CTX.principal_headers(inp.principal))
        async with httpx.AsyncClient(timeout=_CTX.http_timeout_s) as client:
            body = {"input": inp.value}
            if inp.cache is not None:
                body["cache"] = inp.cache
            resp = await client.post(
                url,
                json=body,
                headers=headers,
            )
            resp.raise_for_status()
            result = resp.json()

    await _capture_effect(
        op="call",
        kind="tool",
        node_id=inp.node_id,
        cid=inp.cid,
        run_id=inp.run_id,
        root_run_id=inp.root_run_id,
        segment_seq=inp.segment_seq,
        causes=inp.causes,
        input_value=inp.value,
        output_value=result,
        secrets=inp.secrets,
    )
    return result


async def runSub(inp: RunSubInput, output: Any) -> Any:
    """Capture a sub-flow activation (input + output) at the effect boundary.

    The actual child-flow execution lives in the backend Env (Temporal child
    workflow / DBOS inline); this records the run-identity step + value refs so
    both backends share one capture path. Returns ``output`` unchanged.
    """
    await _capture_effect(
        op="sub",
        kind="flow",
        node_id=inp.node_id,
        cid=inp.cid,
        run_id=inp.run_id,
        root_run_id=inp.root_run_id,
        segment_seq=inp.segment_seq,
        causes=inp.causes,
        input_value=inp.value,
        output_value=output,
        secrets=inp.secrets,
    )
    return output


async def _hydrate_turn(turn: dict[str, Any]) -> dict[str, Any]:
    """Resolve a turn's ``content_ref`` to its blob content (canonical JSON)."""
    ref = turn.get("content_ref")
    if ref is None:
        return dict(turn)
    if _CTX.blob_store is None:
        raise RuntimeError(
            "worker has no blob store configured; transcript content refs cannot hydrate"
        )
    import json

    tenant, _ = parse_ref(ref)
    data = await _CTX.blob_store.get(tenant, ref)
    hydrated = {k: v for k, v in turn.items() if k != "content_ref"}
    hydrated["content"] = json.loads(data)
    return hydrated


def _summary_text(reply: Any, summarizer: str) -> str:
    if isinstance(reply, str):
        return reply
    if isinstance(reply, dict) and isinstance(reply.get("summary"), str):
        return reply["summary"]
    raise RuntimeError(
        f"summarizer reasoner {summarizer!r} must reply with text or {{'summary': str}}; "
        f"got {type(reply).__name__}"
    )


def _strip_reserved_controller_keys(value: Any) -> Any:
    """Drop reserved loop keys before a value reaches a prompt renderer.

    ROUND_NOTE_KEY / FEEDBACK_KEY are framework channels (a trailing system /
    user turn), never business context; a custom system/user renderer must not
    observe them projected into its Context.
    """
    if is_controller_value(value):
        return {k: v for k, v in value.items() if k not in (al.ROUND_NOTE_KEY, al.FEEDBACK_KEY)}
    return value


async def _materialize_transcript(
    inp: InvokeReasonerInput,
    registry: Registry,
    *,
    opening_user_text: Optional[str] = None,
) -> tuple[Transcript, Optional[str]]:
    """Hydrate the transcript plan, enforce the hard token budget, and (SUMMARY
    scope) fold elided turns into the running summary via the named summarizer.

    Returns ``(turns, new_summary)``; ``new_summary`` is non-None only when the
    summarizer actually ran this round. Runs inside the recorded activity, so
    retries re-summarize from the same refs and replays never re-summarize.
    """
    assert inp.transcript is not None
    policy = ContextPolicy.from_json(inp.ctx or {})
    if policy.scope not in (ContextScope.WHOLE_SESSION, ContextScope.SUMMARY):
        raise RuntimeError(
            f"invokeReasoner received a transcript with scope {policy.scope.value!r}; "
            "only whole_session/summary app rounds carry transcripts"
        )
    if policy.max_tokens is None:
        raise RuntimeError(
            f"transcript for reasoner {inp.reasoner!r} carries no max_tokens budget; "
            "whole_session/summary scopes require an explicit budget (no implicit default)"
        )
    count_tokens = _CTX.count_tokens or approx_token_count
    hydrated = [await _hydrate_turn(t) for t in inp.transcript]
    if opening_user_text is not None and is_controller_value(inp.value):
        hydrated = render_opening_ask(hydrated, opening_user_text)
    if is_controller_value(inp.value) and isinstance(inp.value, Mapping):
        if al.FEEDBACK_KEY in inp.value:
            hydrated.append(
                {"role": "user", "content": inp.value[al.FEEDBACK_KEY]}
            )
        round_note = inp.value.get(al.ROUND_NOTE_KEY)
        if isinstance(round_note, str) and round_note:
            hydrated.append({"role": "system", "content": round_note})
    elided, kept = split_to_budget(hydrated, policy.max_tokens, count_tokens)

    if policy.scope is ContextScope.WHOLE_SESSION:
        if elided:
            return [elision_marker(len(elided)), *kept], None
        return kept, None

    # SUMMARY: a named summarizer is mandatory — no silent downgrade to truncation.
    if inp.summarizer is None:
        raise RuntimeError(
            "summary transcript scope requires a named summarizer reasoner "
            "(AgentConfig.summarizer); none was supplied"
        )
    assert _CTX.llm is not None
    summary = inp.summary
    new_summary: Optional[str] = None
    if elided:
        summarizer_payload = {"summary": summary, "turns": elided}
        summarizer = rendered_reasoner_for(
            registry.get_reasoner(inp.summarizer), summarizer_payload
        )
        raw = await _CTX.llm(
            summarizer, summarizer_payload, inp.principal, None, ReasonerDispatch()
        )
        summary_reply, _ = _unwrap_llm(raw)
        new_summary = _summary_text(summary_reply, inp.summarizer)
        summary = new_summary
    if summary:
        return [summary_turn(summary), *kept], new_summary
    return kept, new_summary


async def resolveQoS(inp: ResolveQoSInput) -> str:
    """Resolve + record the QoS tier for a reasoner step.

    Resolved once at first execution; durable backend replay reads the recorded
    string verbatim from history instead of re-running dispatch policy.
    """
    registry = _hydrate_runtime_declarations(inp.runtime_declarations_ref)
    try:
        reasoner_obj = registry.get_reasoner(inp.reasoner)
    except KeyError:
        reasoner_obj = inp.reasoner
    ann = Ann(batchable=inp.node_batchable)
    from .reasoner_batch import get_batch_dispatch_context

    try:
        min_window = get_batch_dispatch_context().min_batch_window_s
    except Exception:
        min_window = None

    resolver = _CTX.resolve_qos
    kwargs = _predictive_qos_kwargs(
        resolver, timeout_s=inp.timeout_s, min_batch_window_s=min_window
    )
    tier = QoSTier(resolver(reasoner_obj, ann, inp.principal, **kwargs))
    if not ann.batchable and tier is QoSTier.BATCH:
        tier = QoSTier.FLEX
    return tier.value


async def invokeReasoner(inp: InvokeReasonerInput) -> Any:
    registry = _hydrate_runtime_declarations(inp.runtime_declarations_ref)
    if _CTX.llm is None:
        raise RuntimeError("worker has no LLM caller configured")
    model_value = _strip_reserved_controller_keys(inp.value)
    render_value = model_value
    if inp.transcript is not None and is_controller_value(model_value):
        # A transcript-scoped loop carries the original run input under
        # ``input`` on every round. Render authored business templates from
        # that stable value, never from mutable trace/feedback controller
        # fields or the preceding tool observation.
        render_value = model_value["input"]
    reasoner = rendered_reasoner_for(
        registry.get_reasoner(inp.reasoner),
        render_value,
    )
    transcript: Optional[Transcript] = None
    new_summary: Optional[str] = None
    if inp.transcript is not None:
        transcript, new_summary = await _materialize_transcript(
            inp,
            registry,
            opening_user_text=rendered_user_for(reasoner, render_value),
        )
    tier = QoSTier.STANDARD
    if inp.qos is not None:
        try:
            tier = QoSTier(inp.qos)
        except (TypeError, ValueError):
            tier = QoSTier.STANDARD
    if tier is QoSTier.BATCH:
        tier = QoSTier.STANDARD
    dispatch = ReasonerDispatch(qos=tier)
    if inp.tools:
        raw = await _CTX.llm(
            reasoner,
            model_value,
            inp.principal,
            transcript,
            dispatch,
            tools=inp.tools,
        )
    else:
        raw = await _CTX.llm(
            reasoner,
            model_value,
            inp.principal,
            transcript,
            dispatch,
        )
    reply, llm_attrs = _unwrap_llm(raw)
    if new_summary is not None:
        # Envelope so the workflow can persist the running summary in
        # AgentState.summary; split_summary_reply unwraps it deterministically.
        result = {SUMMARY_KEY: new_summary, "reply": reply}
    else:
        result = reply
    result = _with_julep_meta(result, llm_attrs)
    await _capture_effect(
        op="think",
        kind="reasoner",
        node_id=inp.node_id,
        cid=inp.cid,
        run_id=inp.run_id,
        root_run_id=inp.root_run_id,
        segment_seq=inp.segment_seq,
        causes=inp.causes,
        input_value=inp.value,
        output_value=result,
        secrets=inp.secrets,
    )
    return result


async def compilePlan(inp: CompilePlanInput) -> dict[str, Any]:
    """Run the planner reasoner, parse its Plan, admit it (§8), return plan JSON.

    Admission happens here, in an activity, so a rejected plan fails the activity
    (and surfaces as a clean ``PlanRejected``) instead of corrupting the
    deterministic workflow.
    """
    registry = _hydrate_runtime_declarations(inp.runtime_declarations_ref)
    if _CTX.llm is None:
        raise RuntimeError("worker has no LLM caller configured")
    planner = registry.get_reasoner(inp.planner)
    raw = await _CTX.llm(planner, inp.value, inp.principal, None, ReasonerDispatch())

    plan_json = raw["plan"] if isinstance(raw, dict) and "plan" in raw else raw
    plan = Node.from_json(plan_json)

    from ..contracts import manifest_from_json  # local import keeps hot path light

    manifest = manifest_from_json(inp.manifest) if inp.manifest else None
    if _CTX.capabilities is not None:
        plan = admit_plan(plan, _CTX.capabilities, manifest)
    from ..validate import blocking, validate

    session_diagnostics = [
        diagnostic
        for diagnostic in blocking(validate(plan, manifest, target="flow"))
        if diagnostic.code.startswith("SESSION_")
    ]
    if session_diagnostics:
        raise PlanRejected(
            f"{diagnostic.code}: {diagnostic.message}" for diagnostic in session_diagnostics
        )

    return plan.to_json()


def _verify_pures_input(raw: Any) -> tuple[dict[str, str], Any, Any, Optional[str]]:
    if isinstance(raw, VerifyPuresInput):
        return raw.pinned, raw.bundle, raw.flow_json, raw.artifact_hash
    if (
        isinstance(raw, dict)
        and set(raw).issubset(
            {"pinned", "bundle", "flow_json", "flowJson", "artifact_hash", "artifactHash"}
        )
        and isinstance(raw.get("pinned"), dict)
    ):
        return (
            raw["pinned"],
            raw.get("bundle"),
            raw.get("flow_json", raw.get("flowJson")),
            raw.get("artifact_hash", raw.get("artifactHash")),
        )
    if isinstance(raw, dict):
        return raw, None, None, None
    raise PureDriftError(
        f"verifyPures input must be pinned dict or VerifyPuresInput, got {type(raw).__name__}"
    )


def _canonical_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _verify_bundle_binding(
    records: list[dict[str, Any]],
    *,
    flow_json: Any,
    artifact_hash: Optional[str],
) -> None:
    if not records:
        return
    if flow_json is None and artifact_hash is None:
        raise PureDriftError("bundle verification requires flow_json or artifact_hash")

    flow_digest: Optional[str] = None
    if flow_json is not None:
        if not isinstance(flow_json, dict):
            raise PureDriftError(
                f"bundle verification flow_json must be an object, got {type(flow_json).__name__}"
            )
        flow_digest = _canonical_digest(flow_json)

    for record in records:
        bundle_hash = record.get("bundleHash", "<unknown>")
        if flow_digest is not None and record.get("flow") != flow_digest:
            raise PureDriftError(
                "bundle flow mismatch: "
                f"bundle={bundle_hash} signed={record.get('flow')} actual={flow_digest}"
            )
        if artifact_hash is not None and record.get("artifactHash") != artifact_hash:
            raise PureDriftError(
                "bundle artifact mismatch: "
                f"bundle={bundle_hash} signed={record.get('artifactHash')} actual={artifact_hash}"
            )


async def verifyPures(inp: Any) -> None:
    """Verify deploy-pinned pure source hashes against this worker's registry."""
    pinned, bundle, flow_json, artifact_hash = _verify_pures_input(inp)
    registered: dict[str, str] = {}
    registry = _registry()
    entries = bundle_ref_entries(bundle)
    if entries:
        store_url = os.environ.get("JULEP_ARTIFACT_STORE_URL", "").strip()
        if not store_url:
            raise PureDriftError(
                "bundle resolution before pure verification requires JULEP_ARTIFACT_STORE_URL"
            )
        try:
            records = resolve_entries(
                artifact_store_from_url(store_url), entries, registry=registry
            )
        except Exception as exc:
            raise PureDriftError(
                f"bundle resolution before pure verification failed: {exc}"
            ) from exc
        _verify_bundle_binding(records, flow_json=flow_json, artifact_hash=artifact_hash)
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
        "bundle": spec.get("bundle"),
        "runtimeDeclarationsRef": spec.get("runtimeDeclarationsRef"),
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
    payload["asserted"] = True
    return payload


def _normalize_contract_payload(raw: Any) -> dict[str, Any]:
    if isinstance(raw, ToolContract):
        return {**raw.to_json(), "asserted": True}
    if not isinstance(raw, dict):
        return CONSERVATIVE_DEFAULT.to_json()
    payload = {
        "effect": Effect(raw.get("effect", CONSERVATIVE_DEFAULT.effect.value)).value,
        "idempotency": Idempotency(
            raw.get("idempotency", CONSERVATIVE_DEFAULT.idempotency.value)
        ).value,
        "asserted": bool(raw.get("asserted", False)),
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


async def resolveAgentSpec(
    value: str | ResolveAgentSpecInput,
) -> dict[str, Any]:
    """Resolve an agent controller to its loop config + granted-tool allow-list.

    The budget defaults to the worker's active capability budget when the
    registered spec does not pin one, so an agent inherits the deployment's
    spend ceiling unless told otherwise.
    """
    if isinstance(value, ResolveAgentSpecInput):
        controller = value.controller
        registry = _hydrate_runtime_declarations(value.runtime_declarations_ref)
    else:
        controller = value
        registry = _registry()
    spec = registry.agent_specs.get(controller, _CTX.agents.get(controller, {}))
    config = dict(spec.get("config") or {})
    if (
        "budget" not in config
        and _CTX.capabilities is not None
        and _CTX.capabilities.budget is not None
    ):
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
            {key: _grant_contract_payload(grant) for key, grant in _CTX.capabilities.tools.items()}
        )
    contracts.update(
        {
            key: _normalize_contract_payload(raw)
            for key, raw in (spec.get("grantedContracts") or {}).items()
        }
    )

    if "toolDefs" in spec:
        tool_defs = spec.get("toolDefs")
    elif config.get("nativeTools", config.get("native_tools")) and isinstance(granted, list):
        registry = _registry()
        tool_defs = []
        for key in granted:
            exp = registry.get_tool_expectation(key)
            if exp is None:
                raise RuntimeError(
                    "native_tools on a durable backend needs provider tool definitions. "
                    f"Tool {key!r} has no registered tool schema expectation; supply "
                    'a spec-level "toolDefs" list or register a ToolSchemaExpectation '
                    "for this granted tool."
                )
            tool_defs.append(
                {
                    "type": "function",
                    "function": {
                        "name": key,
                        "description": "",
                        "parameters": exp.input_schema,
                    },
                }
            )
    else:
        tool_defs = None

    if "grantedSubflows" in spec:
        granted_subflows = spec.get("grantedSubflows")
    elif _CTX.capabilities is not None and _CTX.capabilities._has_subflows:
        granted_subflows = sorted(_CTX.capabilities.subflows)
    else:
        granted_subflows = None
    subflow_queues = spec.get("subflowQueues")
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
        "subflowQueues": None if subflow_queues is None else dict(subflow_queues),
        "capabilitySubflows": None if capability_subflows is None else list(capability_subflows),
        "toolDefs": tool_defs,
        "toolAliases": dict(spec.get("toolAliases") or {}),
    }


async def validateJsonSchema(inp: ValidateJsonSchemaInput) -> Optional[str]:
    """Validate any workflow-owned value outside workflow sandbox code."""
    from .llm import json_schema_error

    return json_schema_error(inp.value, inp.schema)


async def validateAgentOutput(inp: ValidateJsonSchemaInput) -> Optional[str]:
    """Backward-compatible output-only spelling of :func:`validateJsonSchema`."""
    return await validateJsonSchema(inp)


def toolref_json_from_key(key: str) -> dict[str, Any]:
    """Reverse of :func:`~julep.ir.toolref_key`.

    ``"server/tool"`` is an MCP tool; a bare name is a native tool.
    """
    if "/" in key:
        server, tool = key.split("/", 1)
        return {"kind": "mcp", "server": server, "tool": tool}
    return {"kind": "native", "name": key}
