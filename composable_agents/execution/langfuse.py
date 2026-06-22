"""Langfuse export of a run's projection (OTLP/HTTP, GenAI semantic conventions).

The generic OTel exporter (execution/otel.py) emits a link-based DAG for any
backend. Langfuse renders a strict tree and ignores OTel links, so this module
owns the Langfuse-specific shaping: one synthetic root span per run, a
deterministic primary-parent tree, stable IDs derived from run_id/cid (so
history re-export is idempotent), and gen_ai/langfuse attribute mapping. The
OpenTelemetry SDK + OTLP exporter are optional; imports are guarded.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import hashlib

from ..projection import SpanData


@dataclass(frozen=True)
class TreeNode:
    span: SpanData | None
    span_id: int
    parent_id: int | None
    link_ids: tuple[int, ...]
    is_root: bool


_ROOT_CID = "__run_root__"


def trace_id_for(run_id: str) -> int:
    h = hashlib.sha256(("trace:" + run_id).encode()).digest()
    return int.from_bytes(h[:16], "big") or 1


def span_id_for(cid: str) -> int:
    h = hashlib.sha256(("span:" + cid).encode()).digest()
    return int.from_bytes(h[:8], "big") or 1


def build_tree(spans: Sequence[SpanData], run_id: str) -> list[TreeNode]:
    root_id = span_id_for(_ROOT_CID + ":" + run_id)
    present = {s.cid for s in spans}
    ordered = sorted(spans, key=lambda s: (s.start_ts, s.cid))
    nodes: list[TreeNode] = [
        TreeNode(
            span=None,
            span_id=root_id,
            parent_id=None,
            link_ids=(),
            is_root=True,
        )
    ]

    def resolves_without_cycle(cid: str, primary: str) -> bool:
        seen = {cid}
        cur: str | None = primary
        chain = {s.cid: (s.parents[0] if s.parents else None) for s in spans}
        while cur is not None and cur in present:
            if cur in seen:
                return False
            seen.add(cur)
            cur = chain.get(cur)
        return True

    for s in ordered:
        causes = [c for c in s.parents if c in present]
        primary = causes[0] if causes else None
        if primary is not None and not resolves_without_cycle(s.cid, primary):
            primary = None
        parent_id = span_id_for(primary) if primary is not None else root_id
        links = tuple(span_id_for(c) for c in causes[1:]) if causes else ()
        nodes.append(
            TreeNode(
                span=s,
                span_id=span_id_for(s.cid),
                parent_id=parent_id,
                link_ids=links,
                is_root=False,
            )
        )
    return nodes
