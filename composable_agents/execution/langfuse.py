"""Langfuse export of a run's projection (OTLP/HTTP, GenAI semantic conventions).

The generic OTel exporter (execution/otel.py) emits a link-based DAG for any
backend. Langfuse renders a strict tree and ignores OTel links, so this module
owns the Langfuse-specific shaping: one synthetic root span per run, a
deterministic primary-parent tree, stable IDs derived from run_id/cid (so
history re-export is idempotent), and gen_ai/langfuse attribute mapping. The
OpenTelemetry SDK + OTLP exporter are optional; imports are guarded.
"""
from __future__ import annotations

import base64
from collections.abc import Sequence
from dataclasses import dataclass
import hashlib
import os
from typing import Any

try:
    from opentelemetry import trace as _t
    from opentelemetry.trace import Link, SpanContext, set_span_in_context

    HAVE_OTEL = True
except (ImportError, ModuleNotFoundError):
    HAVE_OTEL = False

try:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    HAVE_OTLP = True
except ModuleNotFoundError:
    HAVE_OTLP = False

from ..projection import ProjectionEvent, SpanData, to_otel_spans
from .otel import _json


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


def span_attributes(
    span: SpanData,
    *,
    session_id: str,
    trace_name: str,
    capture_io: bool,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "langfuse.session.id": session_id,
        "langfuse.trace.name": trace_name,
        "ca.cid": span.cid,
        "ca.node": span.node,
    }
    usage = span.attrs.get("llm.usage")
    model = span.attrs.get("llm.model")
    is_generation = model is not None or usage is not None
    if is_generation:
        out["langfuse.observation.type"] = "generation"
        if model is not None:
            out["gen_ai.request.model"] = model
            out["gen_ai.response.model"] = model
        if isinstance(usage, dict):
            if usage.get("input") is not None:
                out["gen_ai.usage.input_tokens"] = usage["input"]
            if usage.get("output") is not None:
                out["gen_ai.usage.output_tokens"] = usage["output"]
    if span.cost is not None:
        out["gen_ai.usage.cost"] = span.cost
    if capture_io:
        if "llm.input" in span.attrs:
            out["langfuse.observation.input"] = span.attrs["llm.input"]
        if "llm.output" in span.attrs:
            out["langfuse.observation.output"] = span.attrs["llm.output"]
    if span.attrs.get("llm.attempts"):
        out["ca.llm.attempts"] = _json(span.attrs["llm.attempts"])
    return out


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


def _ns(ts: float | None) -> int | None:
    return None if ts is None else int(ts * 1_000_000_000)


def _real_span_context(span: Any) -> Any | None:
    if not HAVE_OTEL:
        return None
    get_span_context = getattr(span, "get_span_context", None)
    if not callable(get_span_context):
        return None
    span_context = get_span_context()
    return span_context if isinstance(span_context, SpanContext) else None


def _ctx_of(span: Any) -> Any:
    if HAVE_OTEL and _real_span_context(span) is not None:
        return set_span_in_context(span)
    get_span_context = getattr(span, "get_span_context", None)
    if callable(get_span_context):
        return get_span_context()
    return span


def _links_for(ids: Sequence[int], contexts: dict[int, Any]) -> list[Any]:
    links: list[Any] = []
    for span_id in ids:
        ctx = contexts.get(span_id)
        if ctx is None:
            continue
        if HAVE_OTEL:
            try:
                span = _t.get_current_span(ctx)
                span_context = span.get_span_context()
            except Exception:
                span_context = None
            if isinstance(span_context, SpanContext):
                links.append(Link(span_context))
                continue
        links.append(ctx)
    return links


def export_run_to_langfuse(
    events: Sequence[ProjectionEvent],
    *,
    run_id: str,
    tracer: Any,
    trace_name: str | None = None,
    session_id: str | None = None,
    capture_io: bool = False,
) -> int:
    spans = to_otel_spans(list(events))
    nodes = build_tree(spans, run_id=run_id)
    resolved_trace_name = trace_name or run_id
    resolved_session_id = session_id or run_id
    count = 0
    contexts: dict[int, Any] = {}
    root_span: Any | None = None

    for node in nodes:
        if node.is_root:
            root_span = tracer.start_span(resolved_trace_name, context=None)
            root_span.set_attribute("langfuse.trace.name", resolved_trace_name)
            root_span.set_attribute("langfuse.session.id", resolved_session_id)
            contexts[node.span_id] = _ctx_of(root_span)
            count += 1
            continue

        span_data = node.span
        if span_data is None:
            continue
        parent_ctx = contexts.get(node.parent_id) if node.parent_id is not None else None
        start_ns = _ns(span_data.attrs.get("llm.started_at", span_data.start_ts))
        span = tracer.start_span(
            span_data.name,
            start_time=start_ns,
            context=parent_ctx,
            links=_links_for(node.link_ids, contexts),
        )
        for key, value in span_attributes(
            span_data,
            session_id=resolved_session_id,
            trace_name=resolved_trace_name,
            capture_io=capture_io,
        ).items():
            span.set_attribute(key, value)
        contexts[node.span_id] = _ctx_of(span)
        end_src = span_data.attrs.get("llm.ended_at", span_data.end_ts)
        if end_src is not None:
            span.end(end_time=_ns(end_src))
        count += 1

    if root_span is not None:
        root_span.end()
    return count


@dataclass(frozen=True)
class LangfuseConfig:
    host: str
    public_key: str
    secret_key: str
    capture_io: bool = False

    @staticmethod
    def from_env() -> LangfuseConfig:
        return LangfuseConfig(
            host=os.environ["LANGFUSE_HOST"],
            public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
            secret_key=os.environ["LANGFUSE_SECRET_KEY"],
            capture_io=os.environ.get("LANGFUSE_CAPTURE_IO", "").lower()
            in ("1", "true"),
        )

    def endpoint(self) -> str:
        return self.host.rstrip("/") + "/api/public/otel/v1/traces"

    def headers(self) -> dict[str, str]:
        auth = base64.b64encode(
            f"{self.public_key}:{self.secret_key}".encode()
        ).decode()
        return {"Authorization": f"Basic {auth}", "x-langfuse-ingestion-version": "4"}


@dataclass
class LangfuseExporterHandle:
    tracer: Any
    _provider: Any

    def flush(self) -> None:
        self._provider.force_flush()

    def shutdown(self) -> None:
        self._provider.shutdown()


def configure_langfuse(config: LangfuseConfig | None = None) -> LangfuseExporterHandle:
    if not HAVE_OTLP:
        raise RuntimeError("configure_langfuse requires composable-agents[langfuse]")
    cfg = config or LangfuseConfig.from_env()
    exporter = OTLPSpanExporter(endpoint=cfg.endpoint(), headers=cfg.headers())
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    return LangfuseExporterHandle(
        tracer=provider.get_tracer("composable_agents"),
        _provider=provider,
    )
