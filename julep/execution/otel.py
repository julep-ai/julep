"""OpenTelemetry export of the pomset projection (blueprint, derived plane).

The projection is the framework's observability substrate; OTel is one *sink* for
it. :func:`~julep.projection.to_otel_spans` already folds the raw
``Planned``/``Did``/``Failed`` event stream into per-activation
:class:`~julep.projection.SpanData` (start, end, status, causing
cids). This module turns those into real OpenTelemetry spans, preserving the
causal DAG via span links so a trace UI can render the same shape the projection
describes.

``opentelemetry`` is an optional dependency: the import is guarded and
:data:`HAVE_OTEL` says whether it is installed. With it absent, the pure
projection and :func:`spans_to_dicts` (a dependency-free dictionary rendering,
useful for tests or a custom exporter) still work.

This export runs *outside* the workflow — it consumes events surfaced by the
``projection`` query or assembled by a history-tailing interceptor — so it never
touches workflow determinism.
"""

from __future__ import annotations

import json
from typing import Any, Optional, Sequence

from ..projection import ProjectionEvent, SpanData, to_otel_spans

try:  # optional dependency
    from opentelemetry import trace as _ot_trace
    from opentelemetry.trace import Link, SpanContext, Status, StatusCode

    HAVE_OTEL = True
except ModuleNotFoundError:  # pragma: no cover - exercised only without otel
    HAVE_OTEL = False


def spans_to_dicts(events: Sequence[ProjectionEvent]) -> list[dict[str, Any]]:
    """Render projected spans as plain dicts (no OTel dependency required).

    Handy for tests, JSON export, or feeding a non-OTel tracing backend. Each
    dict mirrors a :class:`~julep.projection.SpanData`.
    """
    out: list[dict[str, Any]] = []
    for s in to_otel_spans(list(events)):
        out.append(
            {
                "name": s.name,
                "cid": s.cid,
                "node": s.node,
                "startTs": s.start_ts,
                "endTs": s.end_ts,
                "status": s.status,
                "parents": list(s.parents),
                "error": s.error,
                "attrs": s.attrs,
                "cost": s.cost,
            }
        )
    return out


def _ns(ts: Optional[float]) -> Optional[int]:
    return None if ts is None else int(ts * 1_000_000_000)


def _json(v: Any) -> str:
    return json.dumps(v, default=str)


def export_spans(
    events: Sequence[ProjectionEvent],
    *,
    tracer_name: str = "julep",
    tracer: Any = None,
) -> int:
    """Emit OpenTelemetry spans for a projection event stream.

    Causality is preserved as span *links* (each activation links to the spans
    of its causing cids) rather than strict parent/child nesting, because a
    pomset activation can have several causes — the projection is a DAG, not a
    tree. Returns the number of spans emitted.

    Requires ``opentelemetry``; raises :class:`RuntimeError` if it is not
    installed (call :func:`spans_to_dicts` for a dependency-free rendering).
    """
    if not HAVE_OTEL:
        raise RuntimeError(
            "export_spans requires opentelemetry; install it or use spans_to_dicts()"
        )

    tr = tracer or _ot_trace.get_tracer(tracer_name)
    spans = to_otel_spans(list(events))

    # First pass: create spans and remember their contexts by cid so later
    # activations can link back to their causes.
    contexts: dict[str, "SpanContext"] = {}
    count = 0
    for s in spans:
        links = [Link(contexts[p]) for p in s.parents if p in contexts]
        start_ns = _ns(s.attrs.get("llm.started_at", s.start_ts))
        span = tr.start_span(s.name, start_time=start_ns, links=links)
        span.set_attribute("ca.cid", s.cid)
        span.set_attribute("ca.node", s.node)
        for k, v in s.attrs.items():
            attr = v if isinstance(v, (str, int, float, bool)) else _json(v)
            span.set_attribute(k, attr)
        if s.cost is not None:
            span.set_attribute("ca.cost", s.cost)
        if s.status == "error":
            span.set_status(Status(StatusCode.ERROR, s.error or "error"))
            if s.error:
                span.record_exception(RuntimeError(s.error))
        elif s.status == "ok":
            span.set_status(Status(StatusCode.OK))
        contexts[s.cid] = span.get_span_context()
        # An unfinished activation has no end; leave it open for the live UI.
        end_src = s.attrs.get("llm.ended_at", s.end_ts)
        if end_src is not None:
            span.end(end_time=_ns(end_src))
        count += 1
    return count


__all__ = ["HAVE_OTEL", "SpanData", "spans_to_dicts", "export_spans"]
