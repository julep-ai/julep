"""Debounce / batch-collation dispatch helper for Temporal.

This is dispatch-boundary tooling (docs/dispatch-boundary.md), not IR: it
collapses a burst of single-item submissions into one batched
:class:`~composable_agents.execution.harness.FlowWorkflow` run whose input is
the collected list, in arrival order. The target flow just sees ``list[item]``
— typically fanning out with :func:`composable_agents.dsl.each`.

Semantics:

* :func:`submit_debounced` signal-with-starts a :class:`DebounceCollector`
  keyed by ``key``; every call appends one item. While a collector for the key
  is open, submissions join its batch; after it completes, the next submission
  opens a fresh one under the same id.
* The collector **fires** when the batch has been quiet for ``quiet_s``
  seconds, or holds ``max_items`` items, or ``max_wait_s`` has elapsed since
  the batch opened — whichever comes first. ``max_items`` is a hard batch cap:
  a fire sends at most that many items and rolls the surplus into the next
  segment.
* On fire it runs the frozen flow as a child workflow (id ``{key}:b{seq}``,
  deduplicated by Temporal like any dispatch), then continues-as-new with any
  remaining items — capped surplus plus arrivals during execution — or
  completes when drained. The batch-open and last-arrival clocks are carried
  across continue-as-new, so a carried batch that already satisfied the fire
  condition fires immediately instead of waiting a fresh window.

The collector is deterministic: time comes from ``workflow.now()`` / durable
timers, items from signals (workflow input on continue-as-new), and the only
effect is the child workflow. A child-flow failure fails the collector loudly —
undelivered late items are visible in its ``pending`` query and the failure,
never silently dropped.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import Any, Optional

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from .harness import FlowInput, FlowWorkflow


@dataclass
class DebounceInput:
    """Configuration for one :class:`DebounceCollector` (and its CaN segments)."""

    key: str
    flow_json: dict[str, Any]
    manifest_json: dict[str, Any]
    quiet_s: float
    max_items: Optional[int] = None
    max_wait_s: Optional[float] = None
    policy: Optional[dict[str, Any]] = None
    pinned_pures: Optional[dict[str, str]] = None
    max_call_limits: Optional[dict[str, int]] = None
    # Run principal: opaque tenant/credential reference (never a secret); the
    # whole batch runs as one principal — a multi-tenant stream is one
    # collector per tenant key, by construction of `key`.
    principal: Optional[dict[str, Any]] = None
    # Continue-as-new carriage: batch ordinal, items left over from the
    # previous segment (capped surplus + arrivals during execution), and the
    # carried batch clocks (ISO timestamps from workflow.now()).
    batch_seq: int = 0
    pending: list[Any] = field(default_factory=list)
    pending_first_at: Optional[str] = None
    pending_last_at: Optional[str] = None


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt is not None else None


def _parse_at(s: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(s) if s else None


@workflow.defn(name="DebounceCollector")
class DebounceCollector:
    """Collect ``submit`` signals into a batch, then run the flow once on it."""

    def __init__(self) -> None:
        self._items: list[Any] = []
        self._first_at: Optional[datetime] = None
        self._last_at: Optional[datetime] = None

    @workflow.signal(name="submit")
    def submit(self, item: Any) -> None:
        if not self._items:
            self._first_at = workflow.now()
        self._items.append(item)
        self._last_at = workflow.now()

    @workflow.query(name="pending")
    def pending(self) -> list[Any]:
        """Items collected so far in the open batch (for triage UIs)."""
        return list(self._items)

    @workflow.run
    async def run(self, inp: DebounceInput) -> dict[str, Any]:
        # Items handed over by a previous segment precede this segment's signals.
        if inp.pending:
            self._items = list(inp.pending) + self._items
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

        # --- fire: one child FlowWorkflow per batch --------------------------- #
        # max_items is a hard cap, not just a fire threshold: a burst that
        # outruns the loop sends only the first cap items; the surplus stays
        # queued (keeping its clocks) and rolls into the next segment.
        cap = inp.max_items if inp.max_items is not None else len(self._items)
        batch, self._items = self._items[:cap], self._items[cap:]
        if not self._items:
            self._first_at = None
            self._last_at = None
        child_id = f"{workflow.info().workflow_id}:b{inp.batch_seq}"
        result = await workflow.execute_child_workflow(
            FlowWorkflow.run,
            FlowInput(
                session_id=child_id,
                input=batch,
                flow_json=inp.flow_json,
                manifest_json=inp.manifest_json,
                pinned_pures=inp.pinned_pures,
                max_call_limits=inp.max_call_limits,
                policy=inp.policy,
                principal=inp.principal,
            ),
            id=child_id,
        )

        # Capped surplus and late arrivals (signals during the batch run) open
        # the next segment, carrying their clocks.
        if self._items:
            workflow.continue_as_new(
                replace(
                    inp,
                    batch_seq=inp.batch_seq + 1,
                    pending=list(self._items),
                    pending_first_at=_iso(self._first_at) or _iso(opened),
                    pending_last_at=_iso(self._last_at),
                )
            )
        return {"batchId": child_id, "items": len(batch), "result": result}


async def submit_debounced(
    client,
    flow_json: dict[str, Any],
    manifest_json: dict[str, Any],
    *,
    key: str,
    item: Any,
    quiet_s: float,
    max_items: Optional[int] = None,
    max_wait_s: Optional[float] = None,
    task_queue: str = "composable-agents",
    policy: Optional[dict[str, Any]] = None,
    pinned_pures: Optional[dict[str, str]] = None,
    max_call_limits: Optional[dict[str, int]] = None,
    principal: Optional[dict[str, Any]] = None,
):
    """Submit one item to the debounced batch for ``key`` (signal-with-start).

    Starts a :class:`DebounceCollector` with workflow id ``debounce:{key}`` if
    none is open, and signals ``submit(item)`` either way — Temporal makes the
    two cases atomic. Returns the workflow handle; the run result is the last
    segment's batch summary. ``max_items`` both fires a full batch early and
    hard-caps the batch size — surplus items roll into the next segment.

    ``flow_json`` / ``manifest_json`` come from
    :func:`composable_agents.freeze.freeze` (then serialized), exactly as for
    :func:`~composable_agents.execution.harness.run_flow`. Configuration is
    fixed by whichever submission opens the collector; later submissions to an
    open batch contribute only their item.
    """
    return await client.start_workflow(
        DebounceCollector.run,
        DebounceInput(
            key=key,
            flow_json=flow_json,
            manifest_json=manifest_json,
            quiet_s=quiet_s,
            max_items=max_items,
            max_wait_s=max_wait_s,
            policy=policy,
            pinned_pures=pinned_pures,
            max_call_limits=max_call_limits,
            principal=principal,
        ),
        id=f"debounce:{key}",
        task_queue=task_queue,
        start_signal="submit",
        start_signal_args=[item],
    )


__all__ = ["DebounceCollector", "DebounceInput", "submit_debounced"]
