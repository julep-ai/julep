"""Pure timeout helpers shared by execution backends."""

from __future__ import annotations

from datetime import timedelta
from typing import Optional


def activity_timeout(node_ann_timeout: Optional[int], default_s: int) -> timedelta:
    """Resolve a node-level activity timeout override against a policy default."""
    seconds = node_ann_timeout if node_ann_timeout is not None else default_s
    return timedelta(seconds=seconds)
