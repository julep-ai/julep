"""HTTP routes for the Julep execution control plane."""

from __future__ import annotations

from typing import cast

from fastapi import HTTPException, Request, status

from ...artifact_store import ArtifactStore
from ...execution.projection_store import ExecutionStore
from ..auth import ApiKey, owner_scoped
from ..temporal import TemporalGateway


def execution_store(request: Request) -> ExecutionStore:
    """Return the request application's configured execution store."""

    return cast(ExecutionStore, request.app.state.store)


def artifact_store(request: Request) -> ArtifactStore:
    """Return the request application's configured content-addressed store."""

    return cast(ArtifactStore, request.app.state.artifacts)


def temporal_gateway(request: Request) -> TemporalGateway:
    """Return the connected Temporal gateway or a service-unavailable response."""

    gateway = cast(TemporalGateway | None, request.app.state.gateway)
    if gateway is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal is unavailable",
        )
    return gateway


def require_owned_run(
    request: Request,
    key: ApiKey,
    run_id: str,
) -> dict[str, object]:
    """Load a run while deliberately hiding absent and non-owned rows alike."""

    row = execution_store(request).get_run(run_id)
    if row is None or not owner_scoped(key, row):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
    return cast(dict[str, object], row)


__all__ = [
    "artifact_store",
    "execution_store",
    "require_owned_run",
    "temporal_gateway",
]
