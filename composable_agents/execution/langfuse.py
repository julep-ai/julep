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
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    HAVE_OTLP = True
except ModuleNotFoundError:
    HAVE_OTLP = False

from ..projection import SpanData
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
