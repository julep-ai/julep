"""Temporal workflow-header propagation for explicit start trace context."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Optional

from temporalio.api.common.v1 import Payload
from temporalio.client import Interceptor, OutboundInterceptor, StartWorkflowInput
from temporalio.common import HeaderCodecBehavior

_TRACE_HEADERS: ContextVar[Optional[Mapping[str, str | bytes]]] = ContextVar(
    "julep_temporal_trace_headers",
    default=None,
)


def _validated_headers(
    headers: Optional[Mapping[str, str | bytes]],
) -> Optional[dict[str, str | bytes]]:
    if headers is None:
        return None
    validated: dict[str, str | bytes] = {}
    for name, value in headers.items():
        if not isinstance(name, str) or not name or name.strip() != name:
            raise ValueError("trace header names must be non-empty trimmed strings")
        if not isinstance(value, (str, bytes)):
            raise TypeError(f"trace header {name!r} must be str or bytes")
        validated[name] = value
    return validated


@contextmanager
def workflow_trace_headers(
    headers: Optional[Mapping[str, str | bytes]],
) -> Iterator[None]:
    """Scope headers to one client start so concurrent starts cannot leak them."""

    token = _TRACE_HEADERS.set(_validated_headers(headers))
    try:
        yield
    finally:
        _TRACE_HEADERS.reset(token)


def current_workflow_trace_headers() -> Optional[Mapping[str, str | bytes]]:
    """Return the headers in scope for the current asynchronous start call."""

    return _TRACE_HEADERS.get()


class WorkflowTraceHeadersInterceptor(Interceptor):
    """Copy scoped trace values into durable Temporal workflow headers."""

    def intercept_client(self, next: OutboundInterceptor) -> OutboundInterceptor:
        return _TraceHeadersOutboundInterceptor(next)


class _TraceHeadersOutboundInterceptor(OutboundInterceptor):
    async def start_workflow(self, input: StartWorkflowInput) -> Any:
        trace_headers = current_workflow_trace_headers()
        if trace_headers:
            encoded = {
                name: Payload(
                    metadata={"encoding": b"binary/plain"},
                    data=value.encode("utf-8") if isinstance(value, str) else value,
                )
                for name, value in trace_headers.items()
            }
            input.headers = {**input.headers, **encoded}
        return await self.next.start_workflow(input)


def require_trace_headers_interceptor(client: Any) -> None:
    """Fail clearly when a real Temporal client cannot persist trace headers."""

    config_method = getattr(client, "config", None)
    if not callable(config_method):
        raise ValueError(
            "trace_headers require a verifiable Temporal client with config()"
        )
    config = config_method(active_config=True)
    interceptors = config.get("interceptors", ()) if isinstance(config, dict) else ()
    if not any(isinstance(item, WorkflowTraceHeadersInterceptor) for item in interceptors):
        raise ValueError(
            "trace_headers require WorkflowTraceHeadersInterceptor on the Temporal client"
        )
    behavior = config.get("header_codec_behavior") if isinstance(config, dict) else None
    if behavior is not HeaderCodecBehavior.CODEC:
        raise ValueError(
            "trace_headers require HeaderCodecBehavior.CODEC so header payloads "
            "use the AES-256-GCM codec"
        )


__all__ = [
    "WorkflowTraceHeadersInterceptor",
    "current_workflow_trace_headers",
    "require_trace_headers_interceptor",
    "workflow_trace_headers",
]
