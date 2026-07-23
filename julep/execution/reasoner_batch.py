"""Temporal dispatch helpers for cross-run reasoner-call batching."""

from __future__ import annotations

import asyncio
import hashlib
import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Optional, cast

from temporalio import activity, workflow
from temporalio.exceptions import ApplicationError
from temporalio.workflow import ParentClosePolicy

from ..dispatch import BatchWindow
from ..ir import canonical_json
from .batch_provider import BatchReply
from .failure_scrub import activity_redacted_failure_text, secret_safe_activity
from .llm_result import LlmCallMeta

if TYPE_CHECKING:
    from .batch_provider import BatchProvider


_UNSAFE_CUSTOM_ID_CHARS = re.compile(r"[^A-Za-z0-9_-]")


def provider_safe_custom_id(raw: str) -> str:
    """Return a deterministic provider-safe opaque batch custom_id."""

    sanitized = _UNSAFE_CUSTOM_ID_CHARS.sub("-", raw)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{sanitized[:46]}-{digest}"


@dataclass
class ReasonerCall:
    """Neutral reasoner-call payload submitted to a batch collector."""

    reasoner: str
    value: Any
    principal: Optional[dict[str, Any]] = None
    transcript: Optional[list[dict[str, Any]]] = None
    cid: str = ""
    reply_to: str = ""
    custom_id: str = ""
    runtime_declarations_ref: Optional[dict[str, Any]] = None


@dataclass
class SubmitReasonerBatchInput:
    """Serializable input for the submitReasonerBatch activity."""

    provider: str
    qos: str
    principal_key: str
    call: ReasonerCall


@dataclass
class BatchCollectorInput:
    """Configuration and continue-as-new carriage for a BatchCollector."""

    key: str
    provider: str
    qos: str
    principal: Optional[dict[str, Any]] = None
    quiet_s: float = 0.0
    max_items: Optional[int] = None
    max_wait_s: Optional[float] = None
    task_queue: str = "julep"
    batch_seq: int = 0
    pending: list[ReasonerCall] = field(default_factory=list)
    pending_first_at: Optional[str] = None
    pending_last_at: Optional[str] = None


@dataclass
class BatchPollInput:
    """Serializable input for one provider batch polling workflow."""

    provider: str
    qos: str
    principal: Optional[dict[str, Any]] = None
    task_queue: str = "julep"
    calls: list[ReasonerCall] = field(default_factory=list)
    batch_id: Optional[str] = None


@dataclass
class BatchDispatchContext:
    """Worker-installed dispatch context, not serialized into workflow history.

    ``min_batch_window_s`` of 0.0 disables predictive QoS clamping.
    """

    client: Any
    task_queue: str = "julep"
    quiet_s: float = 1.0
    max_items: Optional[int] = 256
    max_wait_s: Optional[float] = 3600.0
    min_batch_window_s: float = 0.0


@dataclass
class SubmitBatchInput:
    """Activity input for submitting one frozen provider batch."""

    provider: str
    qos: str
    principal: Optional[dict[str, Any]] = None
    calls: list[ReasonerCall] = field(default_factory=list)


@dataclass
class PollBatchInput:
    """Activity input for polling a provider batch status."""

    provider: str
    batch_id: str


@dataclass
class FetchBatchResultsInput:
    """Activity input for fetching and parsing provider batch results."""

    provider: str
    batch_id: str
    calls: list[ReasonerCall] = field(default_factory=list)
    submitted_at: Optional[float] = None
    completed_at: Optional[float] = None


_BATCH_CTX: Optional[BatchDispatchContext] = None


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt is not None else None


def _parse_at(s: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(s) if s else None


def _coerce_call(item: Any) -> ReasonerCall:
    return ReasonerCall(**item) if isinstance(item, dict) else cast(ReasonerCall, item)


def install_batch_dispatch_context(ctx: BatchDispatchContext) -> None:
    """Install the process-wide batch dispatch context used by the activity."""

    global _BATCH_CTX
    _BATCH_CTX = ctx


def get_batch_dispatch_context() -> BatchDispatchContext:
    """Return the installed batch dispatch context."""

    if _BATCH_CTX is None:
        raise RuntimeError("no BatchDispatchContext installed")
    return _BATCH_CTX


def _principal_key(principal: Optional[dict[str, Any]]) -> str:
    """Stable collector partition key for one principal."""

    if principal is None:
        return ""
    return canonical_json(principal)


def batch_reply_attrs(
    br: BatchReply,
    *,
    model: str,
    provider: str,
    submitted_at: Optional[float] = None,
    completed_at: Optional[float] = None,
) -> dict[str, Any]:
    total = None
    if br.input_tokens is not None and br.output_tokens is not None:
        total = br.input_tokens + br.output_tokens
    meta = LlmCallMeta(
        served_model=model,
        provider=provider,
        input_tokens=br.input_tokens,
        output_tokens=br.output_tokens,
        total_tokens=total,
        started_at=submitted_at,
        ended_at=completed_at,
    )
    return meta.to_attrs()


@workflow.defn(name="BatchCollector")
class BatchCollector:
    """Collect batchable reasoner calls and start detached provider pollers."""

    def __init__(self) -> None:
        self._items: list[ReasonerCall] = []
        self._first_at: Optional[datetime] = None
        self._last_at: Optional[datetime] = None
        self._seen_custom_ids: set[str] = set()

    @workflow.signal(name="submit")
    def submit(self, item: Any) -> None:
        item = _coerce_call(item)
        if item.custom_id:
            if item.custom_id in self._seen_custom_ids:
                return
            self._seen_custom_ids.add(item.custom_id)
        if not self._items:
            self._first_at = workflow.now()
        self._items.append(item)
        self._last_at = workflow.now()

    @workflow.query(name="pending")
    def pending(self) -> list[str]:
        return [c.custom_id for c in self._items]

    @workflow.run
    async def run(self, inp: BatchCollectorInput) -> None:
        # Items handed over by a previous segment precede this segment's signals.
        if inp.pending:
            pending = [_coerce_call(c) for c in inp.pending]
            self._seen_custom_ids.update(c.custom_id for c in pending if c.custom_id)
            self._items = pending + self._items
        # Restore the carried batch clocks: a carried batch keeps its original
        # open/last-arrival times, so an already-due batch fires immediately.
        opened = _parse_at(inp.pending_first_at) or self._first_at or workflow.now()
        if self._items and self._last_at is None:
            self._last_at = _parse_at(inp.pending_last_at) or opened

        # --- collect until the fire condition holds -------------------------- #
        window = BatchWindow(
            quiet_s=inp.quiet_s,
            max_items=inp.max_items,
            max_wait_s=inp.max_wait_s,
        )
        while True:
            decision = window.evaluate(
                item_count=len(self._items),
                opened_at=opened if self._items else None,
                last_arrival_at=self._last_at,
                now=workflow.now(),
            )
            if decision.fire:
                break
            count = len(self._items)
            try:
                await workflow.wait_condition(
                    lambda count=count: len(self._items) > count,
                    timeout=decision.wait_s,
                )
            except asyncio.TimeoutError:
                pass  # re-evaluate the fire condition against workflow.now()

        # --- fire: one detached BatchPoll child per provider batch ------------ #
        cap = inp.max_items if inp.max_items is not None else len(self._items)
        batch, self._items = self._items[:cap], self._items[cap:]
        if not self._items:
            self._first_at = None
            self._last_at = None
        info = workflow.info()
        child_id = f"{info.workflow_id}:p{inp.batch_seq}:{info.run_id}"
        await workflow.start_child_workflow(
            BatchPoll.run,
            BatchPollInput(
                provider=inp.provider,
                qos=inp.qos,
                principal=inp.principal,
                task_queue=inp.task_queue,
                calls=batch,
            ),
            id=child_id,
            parent_close_policy=ParentClosePolicy.ABANDON,
        )

        workflow.continue_as_new(
            replace(
                inp,
                batch_seq=inp.batch_seq + 1,
                pending=list(self._items),
                pending_first_at=(
                    _iso(self._first_at) or (_iso(opened) if self._items else None)
                ),
                pending_last_at=_iso(self._last_at),
            )
        )


@workflow.defn(name="BatchPoll")
class BatchPoll:
    """Submit, poll, fetch, and route one provider batch."""

    async def _signal_reasoner_result(
        self, reply_to: str, custom_id: str, payload: dict[str, Any]
    ) -> bool:
        handle = workflow.get_external_workflow_handle(reply_to)
        try:
            await handle.signal("submitReasonerResult", payload)
        except Exception:
            workflow.logger.debug("failed to route batch result for %s", custom_id)
            return False
        return True

    @workflow.run
    async def run(self, inp: BatchPollInput) -> dict[str, Any]:
        calls = [_coerce_call(c) for c in inp.calls]
        batch_id = inp.batch_id
        submitted_at: Optional[float] = None
        completed_at: Optional[float] = None
        if batch_id is None:
            submitted_at = workflow.now().timestamp()
            batch_id = cast(
                str,
                await workflow.execute_activity(
                    submitBatch,
                    SubmitBatchInput(
                        provider=inp.provider,
                        qos=inp.qos,
                        principal=inp.principal,
                        calls=calls,
                    ),
                    start_to_close_timeout=timedelta(seconds=60),
                ),
            )

        while True:
            status = cast(
                str,
                await workflow.execute_activity(
                    pollBatch,
                    PollBatchInput(provider=inp.provider, batch_id=batch_id),
                    start_to_close_timeout=timedelta(seconds=60),
                ),
            )
            if status == "completed":
                completed_at = workflow.now().timestamp()
                break
            if status == "failed":
                for call in calls:
                    if not call.reply_to:
                        continue
                    await self._signal_reasoner_result(
                        call.reply_to,
                        call.custom_id,
                        {
                            "custom_id": call.custom_id,
                            "error": True,
                            "reason": "batch_failed",
                        },
                    )
                raise ApplicationError("batch failed")
            await asyncio.sleep(5.0)

        entries = cast(
            list[dict[str, Any]],
            await workflow.execute_activity(
                fetchBatchResults,
                FetchBatchResultsInput(
                    provider=inp.provider,
                    batch_id=batch_id,
                    calls=calls,
                    submitted_at=submitted_at,
                    completed_at=completed_at,
                ),
                start_to_close_timeout=timedelta(minutes=10),
            ),
        )

        reply_to_by_custom_id = {call.custom_id: call.reply_to for call in calls}
        routed = 0
        for entry in entries:
            custom_id = str(entry["custom_id"])
            reply_to = reply_to_by_custom_id.get(custom_id)
            if not reply_to:
                continue
            if entry.get("error"):
                signal_payload = {
                    "custom_id": custom_id,
                    "error": True,
                    "reason": entry.get("reason"),
                }
            else:
                attrs = dict(entry.get("attrs") or {})
                payload = {
                    "__julep_meta__": {
                        **attrs,
                        "tier": "BATCH",
                        "batch_id": batch_id,
                    },
                    "reply": entry["reply"],
                }
                signal_payload = {"custom_id": custom_id, "reply": payload}
            if await self._signal_reasoner_result(reply_to, custom_id, signal_payload):
                routed += 1

        return {"batchId": batch_id, "routed": routed}


async def submit_reasoner_batch(
    client: Any,
    *,
    provider: str,
    qos: str,
    principal: Optional[dict[str, Any]],
    call: ReasonerCall,
    quiet_s: float,
    max_items: Optional[int],
    max_wait_s: Optional[float],
    task_queue: str = "julep",
) -> Any:
    """Submit one reasoner call to the provider/qos/principal batch collector."""

    principal_key = _principal_key(principal)
    key = f"batch:{provider}:{qos}:{principal_key}"
    return await client.start_workflow(
        "BatchCollector",
        BatchCollectorInput(
            key=key,
            provider=provider,
            qos=qos,
            principal=principal,
            quiet_s=quiet_s,
            max_items=max_items,
            max_wait_s=max_wait_s,
            task_queue=task_queue,
        ),
        id=key,
        task_queue=task_queue,
        start_signal="submit",
        start_signal_args=[call],
    )


@activity.defn(name="submitReasonerBatch")
async def submitReasonerBatch(inp: SubmitReasonerBatchInput) -> None:
    """Signal-with-start the batch collector from a Temporal activity."""

    from . import effects
    from .llm import _split_model

    registry = effects._hydrate_runtime_declarations(inp.call.runtime_declarations_ref)
    provider = inp.provider
    if not provider:
        reasoner = registry.get_reasoner(inp.call.reasoner)
        provider, _ = _split_model(reasoner.model, "anthropic")
    ctx = get_batch_dispatch_context()
    await submit_reasoner_batch(
        ctx.client,
        provider=provider,
        qos=inp.qos,
        principal=inp.call.principal,
        call=inp.call,
        quiet_s=ctx.quiet_s,
        max_items=ctx.max_items,
        max_wait_s=ctx.max_wait_s,
        task_queue=ctx.task_queue,
    )


def _provider_adapter_by_name(provider: str) -> "BatchProvider":
    from .batch_provider import _PROVIDERS

    cls = _PROVIDERS.get(provider)
    if cls is None:
        raise NotImplementedError(f"no BatchProvider registered for provider {provider!r}")
    return cls()


def _coerce_calls(calls: list[ReasonerCall]) -> list[ReasonerCall]:
    return [_coerce_call(c) for c in calls]


def _record_batch_attempt(
    *,
    provider: str,
    batch_id: str,
    reasoner: Any,
) -> None:
    from . import effects
    from ..resilience import AttemptRecord

    effects._notify_attempt(
        AttemptRecord(
            model=str(getattr(reasoner, "model", "")),
            provider=provider,
            outcome="ok",
            tier="BATCH",
            batch_id=batch_id,
        )
    )


def _parse_batch_reply(adapter: "BatchProvider", raw: Any, reasoner: Any) -> BatchReply:
    parse_with_usage = getattr(adapter, "parse_with_usage", None)
    if callable(parse_with_usage):
        parsed = parse_with_usage(raw, reasoner)
        if isinstance(parsed, BatchReply):
            return parsed
        return BatchReply(reply=parsed)
    return BatchReply(reply=adapter.parse(raw, reasoner))


def _has_batch_projection_attrs(
    br: BatchReply,
    *,
    submitted_at: Optional[float],
    completed_at: Optional[float],
) -> bool:
    return (
        br.input_tokens is not None
        or br.output_tokens is not None
        or submitted_at is not None
        or completed_at is not None
    )


@activity.defn(name="submitBatch")
@secret_safe_activity
async def submitBatch(inp: SubmitBatchInput) -> str:
    """Render each call, build provider requests, and submit the provider batch."""

    from . import effects
    from .batch_provider import select_batch_provider
    from ..prompt import rendered_reasoner_for

    calls = _coerce_calls(inp.calls)
    if not calls:
        raise ValueError("cannot submit an empty batch")
    registries = {
        call.custom_id: effects._hydrate_runtime_declarations(
            call.runtime_declarations_ref
        )
        for call in calls
    }

    first_reasoner = registries[calls[0].custom_id].get_reasoner(calls[0].reasoner)
    first_rendered = rendered_reasoner_for(first_reasoner, calls[0].value)
    adapter = select_batch_provider(first_rendered.model)

    requests: list[dict[str, Any]] = []
    for call in calls:
        reasoner_obj = registries[call.custom_id].get_reasoner(call.reasoner)
        rendered = rendered_reasoner_for(reasoner_obj, call.value)
        requests.append(
            adapter.build_request(
                call.custom_id,
                rendered,
                call.value,
                transcript=call.transcript,
            )
        )

    return await adapter.submit(requests)


@activity.defn(name="pollBatch")
@secret_safe_activity
async def pollBatch(inp: PollBatchInput) -> str:
    """Return a normalized provider batch status."""

    adapter = _provider_adapter_by_name(inp.provider)
    return await adapter.poll_status(inp.batch_id)


@activity.defn(name="fetchBatchResults")
@secret_safe_activity
async def fetchBatchResults(inp: FetchBatchResultsInput) -> list[dict[str, Any]]:
    """Fetch provider batch results and parse them through the matching reasoner."""

    import inspect

    from . import effects

    adapter = _provider_adapter_by_name(inp.provider)
    calls = _coerce_calls(inp.calls)
    registries = {
        call.custom_id: effects._hydrate_runtime_declarations(
            call.runtime_declarations_ref
        )
        for call in calls
    }
    reasoners_by_custom_id = {
        call.custom_id: registries[call.custom_id].get_reasoner(call.reasoner)
        for call in calls
    }

    out: list[dict[str, Any]] = []
    data = adapter.results(inp.batch_id)
    if hasattr(data, "__aiter__"):
        async for custom_id, raw in data:
            cid = str(custom_id)
            reasoner_obj = reasoners_by_custom_id[cid]
            try:
                batch_reply = _parse_batch_reply(adapter, raw, reasoner_obj)
            except Exception as exc:
                out.append(
                    {
                        "custom_id": cid,
                        "error": True,
                        "reason": activity_redacted_failure_text(exc),
                    }
                )
            else:
                _record_batch_attempt(
                    provider=inp.provider,
                    batch_id=inp.batch_id,
                    reasoner=reasoner_obj,
                )
                attrs = batch_reply_attrs(
                    batch_reply,
                    model=str(getattr(reasoner_obj, "model", "")),
                    provider=inp.provider,
                    submitted_at=inp.submitted_at,
                    completed_at=inp.completed_at,
                )
                entry = {"custom_id": cid, "reply": batch_reply.reply}
                if _has_batch_projection_attrs(
                    batch_reply,
                    submitted_at=inp.submitted_at,
                    completed_at=inp.completed_at,
                ):
                    entry["attrs"] = attrs
                out.append(entry)
        return out

    if inspect.isawaitable(data):
        data = await data
    for custom_id, raw in data:
        cid = str(custom_id)
        reasoner_obj = reasoners_by_custom_id[cid]
        try:
            batch_reply = _parse_batch_reply(adapter, raw, reasoner_obj)
        except Exception as exc:
            out.append(
                {
                    "custom_id": cid,
                    "error": True,
                    "reason": activity_redacted_failure_text(exc),
                }
            )
        else:
            _record_batch_attempt(
                provider=inp.provider,
                batch_id=inp.batch_id,
                reasoner=reasoner_obj,
            )
            attrs = batch_reply_attrs(
                batch_reply,
                model=str(getattr(reasoner_obj, "model", "")),
                provider=inp.provider,
                submitted_at=inp.submitted_at,
                completed_at=inp.completed_at,
            )
            entry = {"custom_id": cid, "reply": batch_reply.reply}
            if _has_batch_projection_attrs(
                batch_reply,
                submitted_at=inp.submitted_at,
                completed_at=inp.completed_at,
            ):
                entry["attrs"] = attrs
            out.append(entry)
    return out


__all__ = [
    "batch_reply_attrs",
    "BatchCollector",
    "BatchCollectorInput",
    "BatchDispatchContext",
    "BatchPoll",
    "BatchPollInput",
    "ReasonerCall",
    "FetchBatchResultsInput",
    "PollBatchInput",
    "SubmitBatchInput",
    "SubmitReasonerBatchInput",
    "fetchBatchResults",
    "get_batch_dispatch_context",
    "install_batch_dispatch_context",
    "pollBatch",
    "provider_safe_custom_id",
    "submitBatch",
    "submitReasonerBatch",
    "submit_reasoner_batch",
]
