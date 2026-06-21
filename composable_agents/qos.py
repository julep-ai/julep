"""QoS dispatch ladder for brain calls.

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

from enum import Enum
from typing import Any


class QoSTier(str, Enum):
    """Brain dispatch quality-of-service tier."""

    PRIORITY = "PRIORITY"
    STANDARD = "STANDARD"
    FLEX = "FLEX"
    BATCH = "BATCH"


def _requested_qos_from_principal(principal: Any) -> QoSTier:
    if not isinstance(principal, dict):
        return QoSTier.STANDARD

    try:
        return QoSTier(principal.get("qos"))
    except (TypeError, ValueError):
        return QoSTier.STANDARD


def default_resolve_qos(
    brain: Any,
    node_ann: Any,
    principal: Any,
    load: Any | None = None,
) -> QoSTier:
    """Resolve the day-one QoS tier from principal hints and node annotations.

    ``brain`` and ``load`` are part of the stable resolver seam, but the default
    policy intentionally ignores them until deploy/runtime policy is wired in.
    """

    del brain, load

    requested = _requested_qos_from_principal(principal)
    if not getattr(node_ann, "batchable", False) and requested is QoSTier.BATCH:
        return QoSTier.FLEX
    return requested
