"""Backend-neutral effect implementations (the Hands + Brains boundary).

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
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

from .. import agent_loop as al
from ..capabilities import CapabilityManifest, ToolGrant
from ..contracts import CONSERVATIVE_DEFAULT, ToolContract
from ..dotctx import Brain
from ..errors import CapabilityDenied, PureDriftError
from ..ir import Ann, ContextPolicy, Node, canonical_json, toolref_from_json, toolref_key
from ..kinds import ContextScope, Effect, Idempotency
from ..qos import BrainDispatch, QoSTier, default_resolve_qos
from ..registry import DEFAULT_REGISTRY, Registry
from ..prompt import rendered_brain_for
from ..staged import admit_plan
from ..trajectory import (
    TrajectoryRun,
    TrajectorySink,
    TrajectoryStep,
    TrajectoryValue,
    _best_effort,
)
from ..transcript import (
    SUMMARY_KEY,
    Transcript,
    approx_token_count,
    elision_marker,
    split_to_budget,
    summary_turn,
)
from ..cas import cas_from_url
from ..worker_store import bundle_ref_entries, resolve_entries
from .blobstore import BlobStore, parse_ref
from .session_store import SessionStore

logger = logging.getLogger("composable_agents.execution.effects")

# An opaque, JSON-serializable tenant/credential *reference* supplied at
# dispatch and threaded through workflow input into every effect payload. The
# framework never interprets it, and it must never contain a secret: Temporal
# history is a durable, replayable record — carry a token *ref* and let the
# worker resolve the actual credential at call time.
RunPrincipal = dict[str, Any]

# Caller signatures the worker supplies.
# (server, tool, args, key, principal) -> result
McpCaller = Callable[[str, str, Any, str, Optional[RunPrincipal]], Awaitable[Any]]
# (brain, value, principal, transcript, dispatch) -> result. ``transcript`` is the
# hydrated, budget-bounded neutral turn list for transcript-scoped app rounds
# (None everywhere else); the caller maps it to its provider's wire format.
# The 5-arg form is canonical; :func:`configure` wraps legacy 2-, 3-, and
# 4-arg callers once (2-/3-arg callers fail fast if a transcript arrives).
LlmCaller = Callable[
    [Brain, Any, Optional[RunPrincipal], Optional[Transcript], BrainDispatch],
    Awaitable[Any],
]


@dataclass
class WorkerContext:
    """Process-global configuration read by the activities.

    ``mcp_call`` receives ``(server, tool, value, idempotency_key, principal)``.
    The key is the deterministic activation ``cid`` from :class:`CallHandInput`;
    Temporal retries re-invoke the activity with the same input, so MCP retry
    keys are stable by construction. MCP now carries the key, so MCP tools that
    require transport-level idempotency are admissible. ``principal`` is the
    run's :data:`RunPrincipal` (or ``None``); legacy 4-argument callers are
    wrapped once by :func:`configure` and keep working unchanged.
    """

    hand_urls: dict[str, str] = field(default_factory=dict)   # native name -> URL
    mcp_call: Optional[McpCaller] = None
    llm: Optional[LlmCaller] = None
    # QoS resolver seam for brain dispatch; deployments can override it with
    # deploy/runtime policy beyond the default principal + annotation rule.
    resolve_qos: Callable[..., QoSTier] = field(default=default_resolve_qos)
    blob_store: Optional[BlobStore] = None
    session_store: Optional[SessionStore] = None
    capabilities: Optional[CapabilityManifest] = None
    registry: Optional[Registry] = None
    http_timeout_s: float = 30.0
    # Resolves the run principal into extra transport headers for native hands.
    # Absent means no extra headers; native hands keep working unchanged.
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
    # controller -> {config, grantedTools, grantedContracts, grantedSubflows}
    agents: dict[str, dict[str, Any]] = field(default_factory=dict)
    trajectory_sink: Optional[TrajectorySink] = None
    trajectory_blob_store: Optional[BlobStore] = None


@dataclass
class VerifyPuresInput:
    pinned: dict[str, str]
    bundle: Optional[list[dict[str, str]]] = None
    flow_json: Optional[dict[str, Any]] = None
    artifact_hash: Optional[str] = None


_CTX = WorkerContext()
_TRAJECTORY_SINK: Optional[TrajectorySink] = None
_TRAJECTORY_BLOB_STORE: Optional[BlobStore] = None
_DEFAULT_BRAIN_DISPATCH = BrainDispatch()


def set_trajectory_sink(
    sink: Optional[TrajectorySink],
    blob_store: Optional[BlobStore] = None,
) -> None:
    """Install a process-wide trajectory sink (+ optional blob store for value refs).

    Best-effort capture only: a missing sink disables capture entirely. Mirrors
    composable_agents.execution.dbos_backend.set_projection_sink.
    """
    global _TRAJECTORY_SINK, _TRAJECTORY_BLOB_STORE
    _TRAJECTORY_SINK = sink
    _TRAJECTORY_BLOB_STORE = blob_store


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


def _adapt_mcp_caller(fn: Callable[..., Awaitable[Any]]) -> McpCaller:
    if _accepts_positional(fn, 5):
        return fn

    async def legacy(
        server: str, tool: str, value: Any, key: str, principal: Optional[RunPrincipal]
    ) -> Any:
        return await fn(server, tool, value, key)

    return legacy


def _reject_transcript(fn: Callable[..., Awaitable[Any]]) -> RuntimeError:
    return RuntimeError(
        f"this worker's LlmCaller {getattr(fn, '__name__', fn)!r} does not accept a "
        "transcript, but a transcript-scoped app round produced one; update the "
        "caller to the canonical 5-argument form "
        "(brain, value, principal, transcript, dispatch)"
    )


def _adapt_llm_caller(fn: Callable[..., Awaitable[Any]]) -> LlmCaller:
    """Adapt legacy callers to the 5-argument canonical LlmCaller form."""
    if _accepts_positional(fn, 5):
        return fn

    if _accepts_positional(fn, 4):
        async def transcript_aware(
            brain: Brain,
            value: Any,
            principal: Optional[RunPrincipal],
            transcript: Optional[Transcript],
            dispatch: BrainDispatch = _DEFAULT_BRAIN_DISPATCH,
        ) -> Any:
            del dispatch
            return await fn(brain, value, principal, transcript)

        return transcript_aware

    if _accepts_positional(fn, 3):
        # Principal-aware caller from the run-principal design. No silent drop:
        # a transcript it cannot receive is a hard error (G-8).
        async def principal_aware(
            brain: Brain,
            value: Any,
            principal: Optional[RunPrincipal],
            transcript: Optional[Transcript],
            dispatch: BrainDispatch = _DEFAULT_BRAIN_DISPATCH,
        ) -> Any:
            del dispatch
            if transcript is not None:
                raise _reject_transcript(fn)
            return await fn(brain, value, principal)

        return principal_aware

    async def legacy(
        brain: Brain,
        value: Any,
        principal: Optional[RunPrincipal],
        transcript: Optional[Transcript],
        dispatch: BrainDispatch = _DEFAULT_BRAIN_DISPATCH,
    ) -> Any:
        del dispatch
        if transcript is not None:
            raise _reject_transcript(fn)
        return await fn(brain, value)

    return legacy


def configure(ctx: WorkerContext) -> None:
    """Install the worker-wide context the activities read.

    Legacy callers (``mcp_call`` without the trailing ``principal``; ``llm``
    taking ``(brain, value)``, ``(brain, value, principal)``, or
    ``(brain, value, principal, transcript)``) are wrapped here, once, so they
    keep working unchanged. The canonical ``llm`` form is
    ``(brain, value, principal, transcript, dispatch)``; wrapped narrower callers fail
    fast if a transcript-scoped app round hands them a transcript.
    """
    global _CTX
    if ctx.mcp_call is not None:
        ctx.mcp_call = _adapt_mcp_caller(ctx.mcp_call)
    if ctx.llm is not None:
        ctx.llm = _adapt_llm_caller(ctx.llm)
    _CTX = ctx
    set_trajectory_sink(ctx.trajectory_sink, ctx.trajectory_blob_store or ctx.blob_store)


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
    principal: Optional[RunPrincipal] = None  # run principal (opaque, never a secret)
    run_id: Optional[str] = None
    root_run_id: Optional[str] = None
    segment_seq: Optional[int] = None
    node_id: Optional[str] = None
    op: Optional[str] = None
    kind: Optional[str] = None
    causes: tuple[str, ...] = ()


@dataclass
class InvokeBrainInput:
    brain: str
    value: Any
    cid: str
    principal: Optional[RunPrincipal] = None
    # Transcript plan for transcript-scoped app rounds (agent-transcripts
    # design): ref-bearing turns projected deterministically in workflow code.
    # invokeBrain hydrates the refs, enforces ctx.max_tokens, and (SUMMARY
    # scope) folds elided turns into the running summary via ``summarizer``.
    transcript: Optional[list[dict[str, Any]]] = None
    ctx: Optional[dict[str, Any]] = None         # ContextPolicy JSON (scope + maxTokens)
    summarizer: Optional[str] = None             # named summarizer brain (SUMMARY scope)
    summary: Optional[str] = None                # running summary from AgentState
    run_id: Optional[str] = None
    root_run_id: Optional[str] = None
    segment_seq: Optional[int] = None
    node_id: Optional[str] = None
    op: Optional[str] = None
    kind: Optional[str] = None
    causes: tuple[str, ...] = ()
    # Recorded QoS tier (M0: advisory; dispatch still sync). Carried so the
    # brain step input reflects the resolved tier deterministically.
    qos: Optional[str] = None


@dataclass
class ResolveQoSInput:
    brain: str
    node_batchable: bool = False
    principal: Optional[RunPrincipal] = None
    cid: Optional[str] = None
    run_id: Optional[str] = None
    root_run_id: Optional[str] = None
    segment_seq: Optional[int] = None
    node_id: Optional[str] = None


@dataclass
class CompilePlanInput:
    planner: str
    value: Any
    cid: str
    manifest: Optional[dict[str, Any]] = None  # parent frozen manifest (for schema checks)
    principal: Optional[RunPrincipal] = None


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
) -> None:
    """Best-effort trajectory capture for one effect activation.

    Lives only in the effect layer, so both the Temporal and DBOS backends
    (which both call effects.callHand / effects.invokeBrain) get capture for
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
        try:
            return await blob_store.put(
                root_run_id, json.dumps(value, sort_keys=True).encode()
            )
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
            TrajectoryValue(
                ref=input_ref, root_run_id=root_run_id, step_id=step_id, kind="input"
            )
        )
    if output_ref is not None:
        values.append(
            TrajectoryValue(
                ref=output_ref, root_run_id=root_run_id, step_id=step_id, kind="output"
            )
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
        try:
            ref = await blob_store.put(
                root_run_id, json.dumps(value, sort_keys=True).encode()
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


async def callHand(inp: CallHandInput) -> Any:
    ref = toolref_from_json(inp.tool_ref)
    key = toolref_key(ref)

    if inp.tool_ref.get("kind") == "mcp":
        if _CTX.mcp_call is None:
            raise RuntimeError("worker has no MCP caller configured")
        server = inp.tool_ref["server"]
        tool = inp.tool_ref["tool"]
        result = await _CTX.mcp_call(server, tool, inp.value, inp.cid, inp.principal)
    else:
        # Native hand: HTTP POST with an idempotency key derived from the cid.
        url = _CTX.hand_urls.get(key)
        if url is None:
            raise RuntimeError(f"no URL registered for native hand {key!r}")
        if _CTX.capabilities is not None and not _CTX.capabilities.network_allows(_domain_of(url)):
            raise CapabilityDenied(f"network egress to {_domain_of(url)!r} is not granted")

        import httpx  # imported in-activity so the module loads without httpx

        logger.debug("callHand %s -> %s", key, url)
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
        kind="hand",
        node_id=inp.node_id,
        cid=inp.cid,
        run_id=inp.run_id,
        root_run_id=inp.root_run_id,
        segment_seq=inp.segment_seq,
        causes=inp.causes,
        input_value=inp.value,
        output_value=result,
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
        f"summarizer brain {summarizer!r} must reply with text or {{'summary': str}}; "
        f"got {type(reply).__name__}"
    )


async def _materialize_transcript(inp: InvokeBrainInput) -> tuple[Transcript, Optional[str]]:
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
            f"invokeBrain received a transcript with scope {policy.scope.value!r}; "
            "only whole_session/summary app rounds carry transcripts"
        )
    if policy.max_tokens is None:
        raise RuntimeError(
            f"transcript for brain {inp.brain!r} carries no max_tokens budget; "
            "whole_session/summary scopes require an explicit budget (no implicit default)"
        )
    count_tokens = _CTX.count_tokens or approx_token_count
    hydrated = [await _hydrate_turn(t) for t in inp.transcript]
    elided, kept = split_to_budget(hydrated, policy.max_tokens, count_tokens)

    if policy.scope is ContextScope.WHOLE_SESSION:
        if elided:
            return [elision_marker(len(elided)), *kept], None
        return kept, None

    # SUMMARY: a named summarizer is mandatory — no silent downgrade to truncation.
    if inp.summarizer is None:
        raise RuntimeError(
            "summary transcript scope requires a named summarizer brain "
            "(AgentConfig.summarizer); none was supplied"
        )
    assert _CTX.llm is not None
    summary = inp.summary
    new_summary: Optional[str] = None
    if elided:
        summarizer_payload = {"summary": summary, "turns": elided}
        summarizer = rendered_brain_for(
            _registry().get_brain(inp.summarizer), summarizer_payload
        )
        raw = await _CTX.llm(
            summarizer, summarizer_payload, inp.principal, None, BrainDispatch()
        )
        new_summary = _summary_text(raw, inp.summarizer)
        summary = new_summary
    if summary:
        return [summary_turn(summary), *kept], new_summary
    return kept, new_summary


async def resolveQoS(inp: ResolveQoSInput) -> str:
    """Resolve + record the QoS tier for a brain step.

    Resolved once at first execution; durable backend replay reads the recorded
    string verbatim from history instead of re-running dispatch policy.
    """
    try:
        brain_obj = _registry().get_brain(inp.brain)
    except KeyError:
        brain_obj = inp.brain
    ann = Ann(batchable=inp.node_batchable)
    tier = _CTX.resolve_qos(brain_obj, ann, inp.principal)
    return QoSTier(tier).value


async def invokeBrain(inp: InvokeBrainInput) -> Any:
    if _CTX.llm is None:
        raise RuntimeError("worker has no LLM caller configured")
    transcript: Optional[Transcript] = None
    new_summary: Optional[str] = None
    if inp.transcript is not None:
        transcript, new_summary = await _materialize_transcript(inp)
    brain = rendered_brain_for(_registry().get_brain(inp.brain), inp.value)
    tier = QoSTier.STANDARD
    if inp.qos is not None:
        try:
            tier = QoSTier(inp.qos)
        except (TypeError, ValueError):
            tier = QoSTier.STANDARD
    if tier is QoSTier.BATCH:
        tier = QoSTier.STANDARD
    dispatch = BrainDispatch(qos=tier)
    reply = await _CTX.llm(brain, inp.value, inp.principal, transcript, dispatch)
    if new_summary is not None:
        # Envelope so the workflow can persist the running summary in
        # AgentState.summary; split_summary_reply unwraps it deterministically.
        result = {SUMMARY_KEY: new_summary, "reply": reply}
    else:
        result = reply
    await _capture_effect(
        op="think",
        kind="brain",
        node_id=inp.node_id,
        cid=inp.cid,
        run_id=inp.run_id,
        root_run_id=inp.root_run_id,
        segment_seq=inp.segment_seq,
        causes=inp.causes,
        input_value=inp.value,
        output_value=result,
    )
    return result


async def compilePlan(inp: CompilePlanInput) -> dict[str, Any]:
    """Run the planner brain, parse its Plan, admit it (§8), return plan JSON.

    Admission happens here, in an activity, so a rejected plan fails the activity
    (and surfaces as a clean ``PlanRejected``) instead of corrupting the
    deterministic workflow.
    """
    if _CTX.llm is None:
        raise RuntimeError("worker has no LLM caller configured")
    planner = _registry().get_brain(inp.planner)
    raw = await _CTX.llm(planner, inp.value, inp.principal, None, BrainDispatch())

    plan_json = raw["plan"] if isinstance(raw, dict) and "plan" in raw else raw
    plan = Node.from_json(plan_json)

    if _CTX.capabilities is not None:
        from ..contracts import manifest_from_json  # local import keeps hot path light

        manifest = manifest_from_json(inp.manifest) if inp.manifest else None
        plan = admit_plan(plan, _CTX.capabilities, manifest)

    return plan.to_json()


def _verify_pures_input(raw: Any) -> tuple[dict[str, str], Any, Any, Optional[str]]:
    if isinstance(raw, VerifyPuresInput):
        return raw.pinned, raw.bundle, raw.flow_json, raw.artifact_hash
    if (
        isinstance(raw, dict)
        and set(raw).issubset({"pinned", "bundle", "flow_json", "flowJson", "artifact_hash", "artifactHash"})
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
    raise PureDriftError(f"verifyPures input must be pinned dict or VerifyPuresInput, got {type(raw).__name__}")


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
        store_url = os.environ.get("STORE_URL", "").strip()
        if not store_url:
            raise PureDriftError("bundle resolution before pure verification requires STORE_URL")
        try:
            records = resolve_entries(cas_from_url(store_url), entries, registry=registry)
        except Exception as exc:
            raise PureDriftError(f"bundle resolution before pure verification failed: {exc}") from exc
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
