"""QoS dispatch ladder for reasoner calls.

The ladder is:

- ``PRIORITY``: sync API, priority tier (premium cost, lowest latency).
- ``STANDARD``: sync API, default.
- ``FLEX``: sync API, degraded tier (cheaper, slower).
- ``BATCH``: Batch API, cheaper with a longer completion window.

Only ``BATCH`` crosses the async boundary and changes workflow control flow.
The three synchronous rungs only change cost and latency. A non-batchable node
must not cross the async boundary, so the clamp rule is:
``if not batchable: floor = FLEX``.

``load`` is accepted by the resolver seam for future backpressure policy, but
is ignored by this v1 default implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class QoSTier(str, Enum):
    """Reasoner dispatch quality-of-service tier."""

    PRIORITY = "PRIORITY"
    STANDARD = "STANDARD"
    FLEX = "FLEX"
    BATCH = "BATCH"


@dataclass(frozen=True)
class ReasonerDispatch:
    qos: QoSTier = QoSTier.STANDARD
    batch_id: str | None = None


def _requested_qos_from_principal(principal: Any) -> QoSTier:
    if not isinstance(principal, dict):
        return QoSTier.STANDARD

    try:
        return QoSTier(principal.get("qos"))
    except (TypeError, ValueError):
        return QoSTier.STANDARD


def default_resolve_qos(
    reasoner: Any,
    node_ann: Any,
    principal: Any,
    load: Any | None = None,
    *,
    timeout_s: float | None = None,
    min_batch_window_s: float | None = None,
) -> QoSTier:
    """Resolve the day-one QoS tier from principal hints and node annotations.

    ``reasoner`` and ``load`` are part of the stable resolver seam, but the default
    policy intentionally ignores them until deploy/runtime policy is wired in.
    ``timeout_s`` is ``None`` for unbounded waits and does not clamp BATCH.
    """

    del reasoner, load

    requested = _requested_qos_from_principal(principal)
    if requested is not QoSTier.BATCH:
        return requested
    if not getattr(node_ann, "batchable", False):
        return QoSTier.FLEX
    if (
        timeout_s is not None
        and min_batch_window_s is not None
        and timeout_s < min_batch_window_s
    ):
        return QoSTier.FLEX
    return requested
