"""Liveness and dependency-readiness endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from ..auth import ApiKey, require_client
from . import artifact_store, execution_store

router = APIRouter(tags=["health"])


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


async def _dependency_checks(request: Request) -> dict[str, str]:
    checks: dict[str, str] = {}

    try:
        execution_store(request).list_runs(principal_subset=None, cursor=None, limit=1)
        checks["store"] = "ok"
    except Exception as exc:
        checks["store"] = f"error: {type(exc).__name__}"

    try:
        # An absent sentinel is a successful, read-only reachability check.
        artifact_store(request).has("0" * 64)
        checks["artifacts"] = "ok"
    except Exception as exc:
        checks["artifacts"] = f"error: {type(exc).__name__}"

    try:
        await _temporal_ready(request)
        checks["temporal"] = "ok"
    except Exception as exc:
        checks["temporal"] = f"error: {type(exc).__name__}"

    return checks


def _readiness_response(checks: dict[str, str]) -> JSONResponse:
    healthy = all(value == "ok" for value in checks.values())
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "ready" if healthy else "unavailable", "checks": checks},
    )


@router.get("/health/ready")
async def health_ready(request: Request) -> JSONResponse:
    if not getattr(request.app.state.settings, "unauthenticated_ready", False):
        raise HTTPException(status_code=404, detail="not found")
    return _readiness_response(await _dependency_checks(request))


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready(
    request: Request,
    key: Annotated[ApiKey, Depends(require_client)],
) -> JSONResponse:
    return _readiness_response(await _dependency_checks(request))


__all__ = ["router"]
