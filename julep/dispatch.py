"""Public dispatch-boundary primitives for durable workflow starts.

Flows describe what happens after work starts.  This module owns the small,
backend-facing policies that decide whether and when work starts: stable
workflow identities, Temporal signal-with-start requests, and batch windows.
None of these values are part of the frozen IR.

The module is import-safe without the Temporal extra.  Constructing a generic
:class:`SignalWithStartRequest` and evaluating a :class:`BatchWindow` are pure;
executing a request (or constructing the built-in debounce collector input)
requires ``julep[temporal]``.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Awaitable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional, Protocol


_UNSAFE_ID_CHARS = re.compile(r"[^A-Za-z0-9_.-]+")
_RESERVED_START_OPTIONS = frozenset(
    {
        "id",
        "task_queue",
        "start_signal",
        "start_signal_args",
        "id_reuse_policy",
        "id_conflict_policy",
    }
)


def dedup_workflow_id(
    namespace: str,
    *identity: Any,
    max_length: int = 255,
) -> str:
    """Return an opaque, deterministic workflow id for a logical dispatch.

    ``identity`` must be JSON-serializable.  Mapping order and insignificant
    JSON whitespace do not affect the result.  The readable namespace is
    sanitized and bounded; the identity itself is represented only by a
    128-bit SHA-256 prefix so tenant ids and other dispatch data do not leak
    into Temporal workflow listings.

    Reuse the returned id for retries of the *same logical dispatch*.  Change
    any identity component when a fresh run is intended.
    """

    if not isinstance(namespace, str) or not namespace.strip():
        raise ValueError("namespace must be a non-empty string")
    if max_length < 34:
        raise ValueError("max_length must be at least 34")

    try:
        payload = json.dumps(
            {"namespace": namespace, "identity": identity},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise TypeError("workflow identity must be finite JSON data") from exc

    digest = hashlib.sha256(payload).hexdigest()[:32]
    safe_namespace = _UNSAFE_ID_CHARS.sub("-", namespace.strip()).strip("-._")
    if not safe_namespace:
        safe_namespace = "dispatch"
    prefix_limit = max_length - len(digest) - 1
    safe_namespace = safe_namespace[:prefix_limit].rstrip("-._") or "dispatch"
    return f"{safe_namespace}:{digest}"


class BatchTrigger(str, Enum):
    """Condition that will (or did) close a batch window."""

    QUIET = "quiet"
    MAX_ITEMS = "max_items"
    MAX_WAIT = "max_wait"


@dataclass(frozen=True)
class BatchWindowDecision:
    """Pure decision produced by :meth:`BatchWindow.evaluate`.

    ``trigger`` is the condition that is due now, or the condition associated
    with ``deadline`` while waiting.  An empty batch has no trigger, deadline,
    or wait duration.
    """

    fire: bool
    trigger: Optional[BatchTrigger]
    deadline: Optional[datetime]
    wait_s: Optional[float]


@dataclass(frozen=True)
class BatchWindow:
    """Trigger policy for a debounce or batch collector.

    A non-empty batch fires after ``quiet_s`` without an arrival, after
    ``max_wait_s`` from its first arrival, or as soon as ``max_items`` is
    reached.  The first condition reached wins.  ``max_items`` is also the
    natural hard cap used by Julep's collectors.
    """

    quiet_s: float
    max_items: Optional[int] = None
    max_wait_s: Optional[float] = None

    def __post_init__(self) -> None:
        if not isinstance(self.quiet_s, (int, float)) or not math.isfinite(self.quiet_s):
            raise ValueError("quiet_s must be finite")
        if self.quiet_s < 0:
            raise ValueError("quiet_s must be non-negative")
        if self.max_items is not None and (
            not isinstance(self.max_items, int)
            or isinstance(self.max_items, bool)
            or self.max_items < 1
        ):
            raise ValueError("max_items must be at least 1")
        if self.max_wait_s is not None:
            if not isinstance(self.max_wait_s, (int, float)) or not math.isfinite(
                self.max_wait_s
            ):
                raise ValueError("max_wait_s must be finite")
            if self.max_wait_s < 0:
                raise ValueError("max_wait_s must be non-negative")

    def evaluate(
        self,
        *,
        item_count: int,
        opened_at: Optional[datetime],
        last_arrival_at: Optional[datetime],
        now: datetime,
    ) -> BatchWindowDecision:
        """Evaluate the next trigger using caller-supplied deterministic time."""

        if item_count < 0:
            raise ValueError("item_count must be non-negative")
        if item_count == 0:
            return BatchWindowDecision(False, None, None, None)
        if opened_at is None or last_arrival_at is None:
            raise ValueError("non-empty batches require opened_at and last_arrival_at")

        if self.max_items is not None and item_count >= self.max_items:
            return BatchWindowDecision(True, BatchTrigger.MAX_ITEMS, now, 0.0)

        trigger = BatchTrigger.QUIET
        deadline = last_arrival_at + timedelta(seconds=self.quiet_s)
        if self.max_wait_s is not None:
            max_wait_deadline = opened_at + timedelta(seconds=self.max_wait_s)
            if max_wait_deadline < deadline:
                trigger = BatchTrigger.MAX_WAIT
                deadline = max_wait_deadline

        wait_s = max((deadline - now).total_seconds(), 0.0)
        return BatchWindowDecision(wait_s == 0.0, trigger, deadline, wait_s)


class _StartWorkflowClient(Protocol):
    def start_workflow(
        self,
        workflow: Any,
        arg: Any,
        **kwargs: Any,
    ) -> Awaitable[Any]: ...


@dataclass(frozen=True)
class SignalWithStartRequest:
    """Backend-neutral description of one Temporal signal-with-start call.

    The explicit Temporal id policies give this request the useful collector
    semantics: signal the existing open workflow, but allow a fresh workflow
    with the same deterministic id after the previous collector has closed.
    """

    workflow: Any
    input: Any
    workflow_id: str
    task_queue: str
    signal: str
    signal_args: Sequence[Any] = field(default_factory=tuple)
    start_options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, value in (
            ("workflow_id", self.workflow_id),
            ("task_queue", self.task_queue),
            ("signal", self.signal),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        reserved = _RESERVED_START_OPTIONS.intersection(self.start_options)
        if reserved:
            names = ", ".join(sorted(reserved))
            raise ValueError(f"start_options cannot override managed fields: {names}")

    def temporal_kwargs(self) -> dict[str, Any]:
        """Materialize Temporal start arguments without importing it at module load."""

        try:
            from temporalio.common import WorkflowIDConflictPolicy, WorkflowIDReusePolicy
        except ImportError as exc:  # pragma: no cover - exercised in no-Temporal CI
            raise RuntimeError(
                "Temporal dispatch requires the temporal extra; "
                "install it with pip install 'julep[temporal]'"
            ) from exc

        return {
            **dict(self.start_options),
            "id": self.workflow_id,
            "task_queue": self.task_queue,
            "id_reuse_policy": WorkflowIDReusePolicy.ALLOW_DUPLICATE,
            "id_conflict_policy": WorkflowIDConflictPolicy.USE_EXISTING,
            "start_signal": self.signal,
            "start_signal_args": list(self.signal_args),
        }

    async def start(self, client: _StartWorkflowClient) -> Any:
        """Execute this request and return the Temporal workflow handle."""

        return await client.start_workflow(
            self.workflow,
            self.input,
            **self.temporal_kwargs(),
        )


async def signal_with_start(
    client: _StartWorkflowClient,
    request: SignalWithStartRequest,
) -> Any:
    """Execute a pre-built signal-with-start request."""

    return await request.start(client)


def build_debounce_request(
    flow_json: Mapping[str, Any],
    manifest_json: Mapping[str, Any],
    *,
    key: str,
    item: Any,
    window: BatchWindow,
    task_queue: str = "julep",
    policy: Optional[Mapping[str, Any]] = None,
    pinned_pures: Optional[Mapping[str, str]] = None,
    max_call_limits: Optional[Mapping[str, int]] = None,
    principal: Optional[Mapping[str, Any]] = None,
    bundle: Optional[Sequence[Mapping[str, str]]] = None,
    runtime_declarations_ref: Optional[Mapping[str, Any]] = None,
    scope: Any = None,
    workflow_id: Optional[str] = None,
    start_options: Optional[Mapping[str, Any]] = None,
) -> SignalWithStartRequest:
    """Build an atomic debounce-by-key signal-with-start request.

    Unless ``workflow_id`` is supplied for migration compatibility, the id is
    derived from ``key``, ``scope``, and all collector configuration.  Items
    are deliberately excluded, so submissions with different items join the
    same open collector while a changed flow, principal, window, or queue does
    not accidentally signal an incompatible collector.
    """

    if not isinstance(key, str) or not key.strip():
        raise ValueError("key must be a non-empty string")
    if not isinstance(task_queue, str) or not task_queue.strip():
        raise ValueError("task_queue must be a non-empty string")

    try:
        from .execution.debounce import DebounceInput
    except ImportError as exc:  # pragma: no cover - exercised in no-Temporal CI
        raise RuntimeError(
            "Debounce dispatch requires the temporal extra; "
            "install it with pip install 'julep[temporal]'"
        ) from exc

    flow = dict(flow_json)
    manifest = dict(manifest_json)
    policy_dict = dict(policy) if policy is not None else None
    pinned = dict(pinned_pures) if pinned_pures is not None else None
    limits = dict(max_call_limits) if max_call_limits is not None else None
    principal_dict = dict(principal) if principal is not None else None
    bundle_list = [dict(row) for row in bundle] if bundle is not None else None
    declarations = (
        dict(runtime_declarations_ref) if runtime_declarations_ref is not None else None
    )

    if workflow_id is None:
        workflow_id = dedup_workflow_id(
            "debounce",
            {
                "key": key,
                "scope": scope,
                "flow": flow,
                "manifest": manifest,
                "window": {
                    "quiet_s": window.quiet_s,
                    "max_items": window.max_items,
                    "max_wait_s": window.max_wait_s,
                },
                "task_queue": task_queue,
                "policy": policy_dict,
                "pinned_pures": pinned,
                "max_call_limits": limits,
                "principal": principal_dict,
                "bundle": bundle_list,
                "runtime_declarations_ref": declarations,
            },
        )

    return SignalWithStartRequest(
        workflow="DebounceCollector",
        input=DebounceInput(
            key=key,
            flow_json=flow,
            manifest_json=manifest,
            quiet_s=window.quiet_s,
            max_items=window.max_items,
            max_wait_s=window.max_wait_s,
            policy=policy_dict,
            pinned_pures=pinned,
            max_call_limits=limits,
            principal=principal_dict,
            bundle=bundle_list,
            runtime_declarations_ref=declarations,
        ),
        workflow_id=workflow_id,
        task_queue=task_queue,
        signal="submit",
        signal_args=(item,),
        start_options=start_options or {},
    )


async def dispatch_debounced(
    client: _StartWorkflowClient,
    flow_json: Mapping[str, Any],
    manifest_json: Mapping[str, Any],
    *,
    key: str,
    item: Any,
    window: BatchWindow,
    task_queue: str = "julep",
    policy: Optional[Mapping[str, Any]] = None,
    pinned_pures: Optional[Mapping[str, str]] = None,
    max_call_limits: Optional[Mapping[str, int]] = None,
    principal: Optional[Mapping[str, Any]] = None,
    bundle: Optional[Sequence[Mapping[str, str]]] = None,
    runtime_declarations_ref: Optional[Mapping[str, Any]] = None,
    scope: Any = None,
    workflow_id: Optional[str] = None,
    start_options: Optional[Mapping[str, Any]] = None,
) -> Any:
    """Submit one item to the durable debounce collector for ``key``."""

    request = build_debounce_request(
        flow_json,
        manifest_json,
        key=key,
        item=item,
        window=window,
        task_queue=task_queue,
        policy=policy,
        pinned_pures=pinned_pures,
        max_call_limits=max_call_limits,
        principal=principal,
        bundle=bundle,
        runtime_declarations_ref=runtime_declarations_ref,
        scope=scope,
        workflow_id=workflow_id,
        start_options=start_options,
    )
    return await signal_with_start(client, request)


__all__ = [
    "BatchTrigger",
    "BatchWindow",
    "BatchWindowDecision",
    "SignalWithStartRequest",
    "build_debounce_request",
    "dedup_workflow_id",
    "dispatch_debounced",
    "signal_with_start",
]
