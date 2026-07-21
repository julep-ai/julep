"""Lane activation and optional worker reconciliation routes."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Mapping
from typing import Annotated, Any, Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from ...app_deploy import ApplicationRelease, ApplicationReleaseError, LaneReconciler
from ..auth import ApiKey, require_admin, require_key
from . import execution_store
from .releases import load_release

router = APIRouter(prefix="/deployments", tags=["deployments"])


class DeploymentRequest(BaseModel):
    lane: str
    release: str


def _logical_queue(release: ApplicationRelease, lane: str) -> str:
    queues = release.deployment_config.get("queues")
    if isinstance(queues, Mapping):
        queue = queues.get(lane)
        if isinstance(queue, str) and queue.strip():
            return queue
    return lane


async def _reconcile_lane(
    reconciler: LaneReconciler,
    release: ApplicationRelease,
    lane: str,
    *,
    task_queue: str,
) -> dict[str, Any]:
    try:
        result = await asyncio.to_thread(
            reconciler.reconcile,
            release,
            lane,
            task_queue=task_queue,
        )
    except ApplicationReleaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"worker reconciliation failed: {exc}",
        ) from exc
    return {
        "status": "ready",
        "release_name": result.release_name,
        "task_queue": result.task_queue,
    }


@router.post("")
async def activate_deployment(
    body: DeploymentRequest,
    request: Request,
    key: Annotated[ApiKey, Depends(require_admin)],
) -> dict[str, Any]:
    if not body.lane.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="lane must be non-empty",
        )
    _row, release = load_release(request, body.release)
    if body.lane not in release.lanes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"release {release.release_hash} has no lane {body.lane!r}",
        )

    reconciler = cast(Optional[LaneReconciler], request.app.state.reconciler)
    if reconciler is None:
        reconcile_status: dict[str, Any] = {
            "status": "external",
            "detail": "worker rollout is managed externally",
        }
    else:
        configured_queues = getattr(request.app.state.settings, "queue_by_lane", {})
        configured_queue = (
            configured_queues.get(body.lane)
            if isinstance(configured_queues, Mapping)
            else None
        )
        task_queue = (
            configured_queue
            if isinstance(configured_queue, str) and configured_queue.strip()
            else _logical_queue(release, body.lane)
        )
        reconcile_status = await _reconcile_lane(
            reconciler,
            release,
            body.lane,
            task_queue=task_queue,
        )

    store = execution_store(request)
    store.activate_deployment(
        body.lane,
        release.release_hash,
        time.time(),
        key.name,
    )
    request.app.state.deployment_reconcile_status[body.lane] = reconcile_status
    row = store.get_deployment(body.lane)
    assert row is not None
    return {**row, "reconcile": reconcile_status}


@router.get("")
async def list_deployments(
    request: Request,
    _key: Annotated[ApiKey, Depends(require_key)],
) -> dict[str, list[dict[str, Any]]]:
    statuses = cast(dict[str, dict[str, Any]], request.app.state.deployment_reconcile_status)
    rows: list[dict[str, Any]] = []
    for stored in execution_store(request).list_deployments():
        row = dict(stored)
        lane = row.get("lane")
        if isinstance(lane, str):
            row["reconcile"] = statuses.get(
                lane,
                {
                    "status": "external",
                    "detail": "worker rollout is managed externally",
                },
            )
        rows.append(row)
    return {"items": rows}


__all__ = ["router"]
