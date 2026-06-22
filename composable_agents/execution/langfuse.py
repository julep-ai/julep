"""Langfuse export of a run's projection (OTLP/HTTP, GenAI semantic conventions).

The generic OTel exporter (execution/otel.py) emits a link-based DAG for any
backend. Langfuse renders a strict tree and ignores OTel links, so this module
owns the Langfuse-specific shaping: one synthetic root span per run, a
deterministic primary-parent tree, stable IDs derived from run_id/cid (so
history re-export is idempotent), and gen_ai/langfuse attribute mapping. The
OpenTelemetry SDK + OTLP exporter are optional; imports are guarded.
"""
from __future__ import annotations

import hashlib


def trace_id_for(run_id: str) -> int:
    h = hashlib.sha256(("trace:" + run_id).encode()).digest()
    return int.from_bytes(h[:16], "big") or 1


def span_id_for(cid: str) -> int:
    h = hashlib.sha256(("span:" + cid).encode()).digest()
    return int.from_bytes(h[:8], "big") or 1
