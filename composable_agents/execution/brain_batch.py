"""Temporal dispatch helpers for cross-run brain-call batching."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Optional, cast

from temporalio import activity, workflow
from temporalio.exceptions import ApplicationError
from temporalio.workflow import ParentClosePolicy

from ..ir import canonical_json

if TYPE_CHECKING:
    from .batch_provider import BatchProvider


@dataclass
class BrainCall:
    """Neutral brain-call payload submitted to a batch collector."""

    brain: str
    value: Any
    principal: Optional[dict[str, Any]] = None
    transcript: Optional[list[dict[str, Any]]] = None
    cid: str = ""
    reply_to: str = ""
    custom_id: str = ""


@dataclass
class SubmitBrainBatchInput:
    """Serializable input for the submitBrainBatch activity."""

    provider: str
    qos: str
    principal_key: str
    call: BrainCall


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
    task_queue: str = "composable-agents"
    batch_seq: int = 0
    pending: list[BrainCall] = field(default_factory=list)
    pending_first_at: Optional[str] = None
    pending_last_at: Optional[str] = None


@dataclass
class BatchPollInput:
    """Serializable input for one provider batch polling workflow."""

    provider: str
    qos: str
    principal: Optional[dict[str, Any]] = None
    task_queue: str = "composable-agents"
    calls: list[BrainCall] = field(default_factory=list)
    batch_id: Optional[str] = None


@dataclass
class BatchDispatchContext:
    """Worker-installed dispatch context, not serialized into workflow history.

    ``min_batch_window_s`` of 0.0 disables predictive QoS clamping.
    """

    client: Any
    task_queue: str = "composable-agents"
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
    calls: list[BrainCall] = field(default_factory=list)


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
    calls: list[BrainCall] = field(default_factory=list)


_BATCH_CTX: Optional[BatchDispatchContext] = None


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt is not None else None


def _parse_at(s: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(s) if s else None


def _coerce_call(item: Any) -> BrainCall:
    return BrainCall(**item) if isinstance(item, dict) else cast(BrainCall, item)


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


@workflow.defn(name="BatchCollector")
class BatchCollector:
    """Collect batchable brain calls and start detached provider pollers."""

    def __init__(self) -> None:
        self._items: list[BrainCall] = []
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
        while True:
            if inp.max_items is not None and len(self._items) >= inp.max_items:
                break
            now = workflow.now()
            if self._items:
                assert self._last_at is not None
                deadline = self._last_at + timedelta(seconds=inp.quiet_s)
                if inp.max_wait_s is not None:
                    deadline = min(deadline, opened + timedelta(seconds=inp.max_wait_s))
                if now >= deadline:
                    break
                timeout: Optional[float] = max((deadline - now).total_seconds(), 0.0)
            else:
                # Signal-with-start means at least one signal is on its way.
                timeout = None
            count = len(self._items)
            try:
                await workflow.wait_condition(
                    lambda count=count: len(self._items) > count, timeout=timeout
                )
            except asyncio.TimeoutError:
                pass  # re-evaluate the fire condition against workflow.now()

        # --- fire: one detached BatchPoll child per provider batch ------------ #
        cap = inp.max_items if inp.max_items is not None else len(self._items)
        batch, self._items = self._items[:cap], self._items[cap:]
        if not self._items:
            self._first_at = None
            self._last_at = None
        child_id = f"{workflow.info().workflow_id}:p{inp.batch_seq}"
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

    async def _signal_brain_result(
        self, reply_to: str, custom_id: str, payload: dict[str, Any]
    ) -> bool:
        handle = workflow.get_external_workflow_handle(reply_to)
        try:
            await handle.signal("submitBrainResult", payload)
        except Exception:
            workflow.logger.debug("failed to route batch result for %s", custom_id)
            return False
        return True

    @workflow.run
    async def run(self, inp: BatchPollInput) -> dict[str, Any]:
        calls = [_coerce_call(c) for c in inp.calls]
        batch_id = inp.batch_id
        if batch_id is None:
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
                break
            if status == "failed":
                for call in calls:
                    if not call.reply_to:
                        continue
                    await self._signal_brain_result(
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
                payload = {
                    "__ca_meta__": {"tier": "BATCH", "batch_id": batch_id},
                    "reply": entry["reply"],
                }
                signal_payload = {"custom_id": custom_id, "reply": payload}
            if await self._signal_brain_result(reply_to, custom_id, signal_payload):
                routed += 1

        return {"batchId": batch_id, "routed": routed}


async def submit_brain_batch(
    client: Any,
    *,
    provider: str,
    qos: str,
    principal: Optional[dict[str, Any]],
    call: BrainCall,
    quiet_s: float,
    max_items: Optional[int],
    max_wait_s: Optional[float],
    task_queue: str = "composable-agents",
) -> Any:
    """Submit one brain call to the provider/qos/principal batch collector."""

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


@activity.defn(name="submitBrainBatch")
async def submitBrainBatch(inp: SubmitBrainBatchInput) -> None:
    """Signal-with-start the batch collector from a Temporal activity."""

    ctx = get_batch_dispatch_context()
    await submit_brain_batch(
        ctx.client,
        provider=inp.provider,
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


def _coerce_calls(calls: list[BrainCall]) -> list[BrainCall]:
    return [_coerce_call(c) for c in calls]


@activity.defn(name="submitBatch")
async def submitBatch(inp: SubmitBatchInput) -> str:
    """Render each call, build provider requests, and submit the provider batch."""

    from . import effects
    from .batch_provider import select_batch_provider
    from ..prompt import rendered_brain_for

    calls = _coerce_calls(inp.calls)
    if not calls:
        raise ValueError("cannot submit an empty batch")

    first_brain = effects._registry().get_brain(calls[0].brain)
    first_rendered = rendered_brain_for(first_brain, calls[0].value)
    adapter = select_batch_provider(first_rendered.model)

    requests: list[dict[str, Any]] = []
    for call in calls:
        brain_obj = effects._registry().get_brain(call.brain)
        rendered = rendered_brain_for(brain_obj, call.value)
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
async def pollBatch(inp: PollBatchInput) -> str:
    """Return a normalized provider batch status."""

    adapter = _provider_adapter_by_name(inp.provider)
    return await adapter.poll_status(inp.batch_id)


@activity.defn(name="fetchBatchResults")
async def fetchBatchResults(inp: FetchBatchResultsInput) -> list[dict[str, Any]]:
    """Fetch provider batch results and parse them through the matching brain."""

    import inspect

    from . import effects

    adapter = _provider_adapter_by_name(inp.provider)
    calls = _coerce_calls(inp.calls)
    brains_by_custom_id = {
        call.custom_id: effects._registry().get_brain(call.brain) for call in calls
    }
    # Deferred: OTel AttemptRecord attribution; v1 uses __ca_meta__/Result.attrs projection.

    out: list[dict[str, Any]] = []
    data = adapter.results(inp.batch_id)
    if hasattr(data, "__aiter__"):
        async for custom_id, raw in data:
            cid = str(custom_id)
            brain_obj = brains_by_custom_id[cid]
            try:
                parsed = adapter.parse(raw, brain_obj)
            except Exception as exc:
                out.append({"custom_id": cid, "error": True, "reason": str(exc)})
            else:
                out.append({"custom_id": cid, "reply": parsed})
        return out

    if inspect.isawaitable(data):
        data = await data
    for custom_id, raw in data:
        cid = str(custom_id)
        brain_obj = brains_by_custom_id[cid]
        try:
            parsed = adapter.parse(raw, brain_obj)
        except Exception as exc:
            out.append({"custom_id": cid, "error": True, "reason": str(exc)})
        else:
            out.append({"custom_id": cid, "reply": parsed})
    return out


__all__ = [
    "BatchCollector",
    "BatchCollectorInput",
    "BatchDispatchContext",
    "BatchPoll",
    "BatchPollInput",
    "BrainCall",
    "FetchBatchResultsInput",
    "PollBatchInput",
    "SubmitBatchInput",
    "SubmitBrainBatchInput",
    "fetchBatchResults",
    "get_batch_dispatch_context",
    "install_batch_dispatch_context",
    "pollBatch",
    "submitBatch",
    "submitBrainBatch",
    "submit_brain_batch",
]
