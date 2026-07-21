"""Liveness and authenticated dependency-readiness endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from ..auth import ApiKey, require_key
from . import cas_store, execution_store

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def _temporal_ready(request: Request) -> None:
    gateway: Any = request.app.state.gateway
    if gateway is None:
        error = getattr(request.app.state, "gateway_error", None)
        raise RuntimeError(str(error or "Temporal gateway is not connected"))

    ready = getattr(gateway, "ready", None)
    if callable(ready):
        result = ready()
        if hasattr(result, "__await__"):
            result = await result
        if result is False:
            raise RuntimeError("Temporal readiness check failed")
        return

    try:
        await gateway.describe("__julep_readiness_probe__")
    except Exception as exc:
        # A not-found response proves that the Temporal frontend was reached.
        if "notfound" in type(exc).__name__.replace("_", "").lower():
            return
        raise


@router.get("/ready")
async def ready(
    request: Request,
    key: Annotated[ApiKey, Depends(require_key)],
) -> JSONResponse:
    checks: dict[str, str] = {}

    try:
        execution_store(request).list_runs(principal_subset=None, cursor=None, limit=1)
        checks["store"] = "ok"
    except Exception as exc:
        checks["store"] = f"error: {type(exc).__name__}"

    try:
        # An absent sentinel is a successful, read-only reachability check.
        cas_store(request).has("0" * 64)
        checks["cas"] = "ok"
    except Exception as exc:
        checks["cas"] = f"error: {type(exc).__name__}"

    try:
        await _temporal_ready(request)
        checks["temporal"] = "ok"
    except Exception as exc:
        checks["temporal"] = f"error: {type(exc).__name__}"

    healthy = all(value == "ok" for value in checks.values())
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "ready" if healthy else "unavailable", "checks": checks},
    )


__all__ = ["router"]
