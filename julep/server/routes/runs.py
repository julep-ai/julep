"""Authenticated execution submission, control, and retrieval routes."""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Mapping
from dataclasses import replace
from typing import Annotated, Any, Literal, Optional, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from ...app_deploy import ApplicationRelease, PipelineRelease, lane_task_queue
from ...execution.projection_store import (
    MAX_INLINE_VALUE_BYTES,
    TERMINAL_RUN_STATUSES,
    ExecutionStore,
)
from ...ir import canonical_json
from ...projection import value_ref
from ...secrets import scrubber_for_values, validate_run_secrets
from ...trajectory import redact_secret_shaped
from ..auth import ApiKey, merge_principal, owner_scoped, require_client
from ..sse import EVENT_PAGE_LIMIT, event_sequence, run_event_response
from ..temporal import TemporalGateway, TemporalStartAmbiguous
from . import execution_store, require_owned_run, temporal_gateway
from .releases import load_release, normalize_release_hash, rehydrate_release

router = APIRouter(prefix="/runs", tags=["runs"])
_RESULT_TERMINAL_STATUSES = TERMINAL_RUN_STATUSES | {"start_failed"}


class RunRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    release: Optional[str] = None
    pipeline: str
    input: Any = None
    session_id: Optional[str] = Field(default=None, alias="sessionId")
    principal: Optional[dict[str, Any]] = None
    queue_lanes: Optional[dict[str, str]] = Field(default=None, alias="queueLanes")
    run_id: Optional[str] = Field(default=None, alias="runId")
    secrets: Optional[dict[str, str]] = None
    mcp_preflight: Optional[Literal["pin", "names", "off"]] = Field(
        default=None, alias="mcpPreflight"
    )


class HumanSignalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cid: str
    value: Any


def _find_pipeline(release: ApplicationRelease, name: str) -> Optional[PipelineRelease]:
    return next((pipeline for pipeline in release.pipelines if pipeline.name == name), None)


def _release_queue_lanes(release: ApplicationRelease) -> dict[str, str]:
    configured = release.deployment_config.get("queues")
    queues = configured if isinstance(configured, Mapping) else {}
    return {
        lane: lane_task_queue(str(queues.get(lane, lane)), release.release_hash)
        for lane in release.lanes
    }


def _active_release_for_pipeline(
    request: Request,
    pipeline_name: str,
) -> tuple[dict[str, Any], ApplicationRelease, PipelineRelease]:
    store = execution_store(request)
    matches: list[tuple[dict[str, Any], ApplicationRelease, PipelineRelease]] = []
    for deployment in store.list_deployments():
        release_hash = deployment.get("release_hash")
        lane = deployment.get("lane")
        if not isinstance(release_hash, str) or not isinstance(lane, str):
            continue
        row = store.get_release(release_hash)
        if row is None:
            continue
        release = rehydrate_release(row)
        pipeline = _find_pipeline(release, pipeline_name)
        if pipeline is not None and pipeline.lane == lane:
            matches.append((row, release, pipeline))
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no active deployment contains pipeline {pipeline_name!r}",
        )
    if len(matches) > 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"pipeline {pipeline_name!r} is active in more than one deployment",
        )
    return matches[0]


def _resolve_pipeline(
    request: Request,
    release_hash: Optional[str],
    pipeline_name: str,
) -> tuple[dict[str, Any], ApplicationRelease, PipelineRelease]:
    if release_hash is None:
        return _active_release_for_pipeline(request, pipeline_name)
    row, release = load_release(request, release_hash)
    pipeline = _find_pipeline(release, pipeline_name)
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"release has no pipeline {pipeline_name!r}",
        )
    return row, release, pipeline


def _deterministic_run_id(idempotency_key: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"julep:run:{idempotency_key}"))


def _input_claim(
    payload: Any,
    *,
    secrets: Optional[Mapping[str, str]] = None,
) -> tuple[str, Any, int, bool]:
    # The workflow receives the caller's exact input, while the durable claim
    # applies the same default secret-shaped redaction floor as projection data.
    redact = (
        redact_secret_shaped
        if not secrets
        else scrubber_for_values(secrets.values(), base=redact_secret_shaped)
    )
    stored_payload = redact(payload)
    ref = value_ref(stored_payload)
    encoded = canonical_json(stored_payload).encode("utf-8")
    byte_len = len(encoded)
    return ref, stored_payload, byte_len, byte_len > MAX_INLINE_VALUE_BYTES


def _run_json_response(row: Mapping[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=dict(row))


def _raise_idempotency_conflict(field: Literal["pipeline", "release"]) -> None:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "error": "idempotency_conflict",
            "field": field,
            "message": f"idempotency key was already used for a different {field}",
        },
    )


def _assert_idempotency_retry_matches(
    existing: Mapping[str, Any],
    *,
    pipeline: str,
    requested_release_hash: str,
) -> None:
    """Require the effective pipeline and release to match the original run."""

    if existing.get("pipeline") != pipeline:
        _raise_idempotency_conflict("pipeline")
    if existing.get("release_hash") != requested_release_hash:
        _raise_idempotency_conflict("release")


@router.post("")
async def start_run(
    body: RunRequest,
    request: Request,
    key: Annotated[ApiKey, Depends(require_client)],
    idempotency_key: Annotated[Optional[str], Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    if not body.pipeline.strip():
        raise HTTPException(status_code=400, detail="pipeline must be non-empty")
    if body.secrets:
        if bool(getattr(request.app.state, "local_echo_mode", False)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="local echo execution does not accept run secrets",
            )
        settings = request.app.state.settings
        if not settings.payload_encryption_required:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="run secrets require Temporal payload encryption",
            )
        try:
            validate_run_secrets(body.secrets)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
    idempotency_key = (idempotency_key.strip() or None) if idempotency_key else None
    requested_run_id = (body.run_id.strip() or None) if body.run_id else None
    if idempotency_key is None and requested_run_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header or runId is required",
        )
    run_id = requested_run_id or _deterministic_run_id(cast(str, idempotency_key))
    workflow_id = f"run-{run_id}"
    principal = merge_principal(key, body.principal)

    # Fast-path retries before resolving today's deployment. This preserves
    # the original response even if routing changed after the first submit;
    # create_run below remains the authoritative atomic race winner.
    store = execution_store(request)
    existing = (
        store.get_run_by_idempotency_key(idempotency_key)
        if idempotency_key is not None
        else store.get_run(run_id)
    )
    if existing is not None:
        if not owner_scoped(key, existing):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="idempotency key or runId is already in use",
            )
        if idempotency_key is not None:
            if existing.get("pipeline") != body.pipeline:
                _raise_idempotency_conflict("pipeline")
            effective_release_hash = (
                normalize_release_hash(body.release)
                if body.release is not None
                else _active_release_for_pipeline(request, body.pipeline)[1].release_hash
            )
            _assert_idempotency_retry_matches(
                existing,
                pipeline=body.pipeline,
                requested_release_hash=effective_release_hash,
            )
        return _run_json_response(existing, 200)

    requested_release_hash = (
        normalize_release_hash(body.release) if body.release is not None else None
    )
    _release_row, release, pipeline = _resolve_pipeline(
        request,
        requested_release_hash,
        body.pipeline,
    )
    if body.secrets and pipeline.mcp_preflight_policy is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "this release predates run-secret binding enforcement; "
                "publish a new release before supplying secrets"
            ),
        )
    if body.mcp_preflight is not None:
        if key.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="admin API key required to override MCP preflight policy",
            )
        pipeline = replace(
            pipeline,
            mcp_preflight_policy=body.mcp_preflight,
        )

    input_ref, stored_input, input_byte_len, input_oversize = _input_claim(
        body.input,
        secrets=body.secrets,
    )
    created = store.create_run(
        run_id=run_id,
        idempotency_key=idempotency_key,
        workflow_id=workflow_id,
        session_id=body.session_id or workflow_id,
        release_hash=release.release_hash,
        pipeline=pipeline.name,
        application=release.application,
        principal=principal,
        input_ref=input_ref,
        status="submitting",
        started_at=time.time(),
    )
    if created != "created":
        if not owner_scoped(key, created):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="idempotency key or runId is already in use",
            )
        if (
            idempotency_key is not None
            and created.get("idempotency_key") == idempotency_key
        ):
            _assert_idempotency_retry_matches(
                created,
                pipeline=body.pipeline,
                requested_release_hash=release.release_hash,
            )
        return _run_json_response(created, 200)

    # Only the atomic create_run winner writes the input claim. A concurrent
    # idempotency loser therefore cannot leave an unreferenced value behind.
    try:
        store.put_value(
            input_ref,
            stored_input,
            input_byte_len,
            input_oversize,
        )
    except Exception as exc:
        store.set_run_status(run_id, "start_failed", finished_at=time.time())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"input claim persistence failed: {type(exc).__name__}",
        ) from exc

    try:
        temporal_run_id = await temporal_gateway(request).start_flow(
            pipeline,
            workflow_id=workflow_id,
            run_id=run_id,
            input=body.input,
            principal=principal,
            queue_lanes=_release_queue_lanes(release),
            secrets=dict(body.secrets) if body.secrets else None,
        )
    except TemporalStartAmbiguous as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Temporal workflow start is unconfirmed; "
                "run left submitting for reconciliation"
            ),
        ) from exc
    except Exception as exc:
        store.set_run_status(run_id, "start_failed", finished_at=time.time())
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Temporal workflow start failed: {type(exc).__name__}",
        ) from exc

    store.set_run_status(
        run_id,
        "accepted",
        temporal_run_id=temporal_run_id,
    )
    # Projection egress can win the race with the Temporal start response. In
    # that case attach the Temporal run id first, then advance through the
    # normal accepted -> running transition without regressing state.
    if store.read_events(run_id, after_seq=0, limit=1):
        store.set_run_status(run_id, "running")
    row = store.get_run(run_id)
    assert row is not None
    return _run_json_response(row, 201)


@router.get("")
async def list_runs(
    request: Request,
    key: Annotated[ApiKey, Depends(require_client)],
    cursor: Optional[str] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, Any]:
    principal_subset = None if key.admin else key.principal_base
    try:
        rows, next_cursor = execution_store(request).list_runs(
            principal_subset=principal_subset,
            cursor=cursor,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid run cursor") from exc
    return {"items": rows, "next_cursor": next_cursor}


@router.get("/{run_id}")
async def get_run(
    run_id: str,
    request: Request,
    key: Annotated[ApiKey, Depends(require_client)],
) -> dict[str, object]:
    return require_owned_run(request, key, run_id)


async def _control_run(
    request: Request,
    key: ApiKey,
    run_id: str,
    operation: str,
) -> dict[str, str]:
    run = require_owned_run(request, key, run_id)
    workflow_id = run.get("workflow_id")
    if not isinstance(workflow_id, str) or not workflow_id:
        raise HTTPException(status_code=409, detail="run has no Temporal workflow ID")
    gateway = temporal_gateway(request)
    try:
        if operation == "cancel":
            await gateway.cancel(workflow_id)
        else:
            await gateway.terminate(workflow_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Temporal {operation} failed: {type(exc).__name__}",
        ) from exc
    return {"status": f"{operation}_requested"}


@router.post("/{run_id}/cancel")
async def cancel_run(
    run_id: str,
    request: Request,
    key: Annotated[ApiKey, Depends(require_client)],
) -> dict[str, str]:
    return await _control_run(request, key, run_id, "cancel")


@router.post("/{run_id}/terminate")
async def terminate_run(
    run_id: str,
    request: Request,
    key: Annotated[ApiKey, Depends(require_client)],
) -> dict[str, str]:
    return await _control_run(request, key, run_id, "terminate")


def _event_cursor(request: Request, after_seq: int) -> int:
    raw = request.headers.get("Last-Event-ID")
    if raw is None:
        return after_seq
    try:
        parsed = int(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Last-Event-ID must be an integer") from exc
    if parsed < 0:
        raise HTTPException(status_code=400, detail="Last-Event-ID must be non-negative")
    return parsed


def _run_references_value(
    store: ExecutionStore,
    run: Mapping[str, object],
    requested_ref: str,
) -> bool:
    if requested_ref == run.get("input_ref") or requested_ref == run.get("result_ref"):
        return True
    cursor = 0
    while True:
        rows = store.read_events(cast(str, run["run_id"]), cursor, EVENT_PAGE_LIMIT)
        if any(row.get("value_ref") == requested_ref for row in rows):
            return True
        if len(rows) < EVENT_PAGE_LIMIT:
            return False
        cursor = event_sequence(rows[-1])


@router.get("/{run_id}/events")
async def run_events(
    run_id: str,
    request: Request,
    key: Annotated[ApiKey, Depends(require_client)],
    after_seq: Annotated[int, Query(ge=0, alias="after")] = 0,
    limit: Annotated[int, Query(ge=1, le=EVENT_PAGE_LIMIT)] = EVENT_PAGE_LIMIT,
) -> Response:
    require_owned_run(request, key, run_id)
    cursor = _event_cursor(request, after_seq)
    store = execution_store(request)
    if "application/json" in request.headers.get("Accept", "").lower():
        rows = store.read_events(run_id, cursor, limit)
        next_cursor = None
        if len(rows) == limit:
            candidate_cursor = event_sequence(rows[-1])
            if store.read_events(run_id, candidate_cursor, 1):
                next_cursor = str(candidate_cursor)
        return JSONResponse(content={"items": rows, "next_cursor": next_cursor})

    heartbeat = cast(int, request.app.state.sse_heartbeat_seconds)
    poll_seconds = cast(float, request.app.state.sse_poll_seconds)
    return run_event_response(
        request,
        store,
        run_id,
        after_seq=cursor,
        heartbeat_seconds=heartbeat,
        poll_seconds=poll_seconds,
    )


@router.get("/{run_id}/result")
async def run_result(
    run_id: str,
    request: Request,
    key: Annotated[ApiKey, Depends(require_client)],
    wait_s: Annotated[float, Query(ge=0.0, le=60.0)] = 0.0,
) -> Response:
    store = execution_store(request)
    deadline = time.monotonic() + wait_s
    while True:
        run = require_owned_run(request, key, run_id)
        if run.get("status") in _RESULT_TERMINAL_STATUSES:
            result_ref = run.get("result_ref")
            payload: Any = None
            if isinstance(result_ref, str):
                value = store.get_value(result_ref)
                if value is None or value.get("oversize") is True:
                    raise HTTPException(status_code=404, detail="run result is unavailable")
                payload = value.get("payload")
            return JSONResponse(content={"run": run, "result": payload})
        if time.monotonic() >= deadline:
            return JSONResponse(status_code=202, content={"run": run})
        await asyncio.sleep(min(0.1, max(0.0, deadline - time.monotonic())))


@router.get("/{run_id}/values/{value_ref}")
async def get_run_value(
    run_id: str,
    value_ref: str,
    request: Request,
    key: Annotated[ApiKey, Depends(require_client)],
) -> dict[str, Any]:
    run = require_owned_run(request, key, run_id)
    store = execution_store(request)
    if not _run_references_value(store, run, value_ref):
        raise HTTPException(status_code=404, detail="value not found")
    value = store.get_value(value_ref)
    if value is None or value.get("oversize") is True:
        raise HTTPException(status_code=404, detail="value not found")
    return value


@router.get("/{run_id}/gates")
async def get_open_gates(
    run_id: str,
    request: Request,
    key: Annotated[ApiKey, Depends(require_client)],
) -> dict[str, Any]:
    run = require_owned_run(request, key, run_id)
    workflow_id = run.get("workflow_id")
    if not isinstance(workflow_id, str):
        raise HTTPException(status_code=409, detail="run has no Temporal workflow ID")
    gates = await temporal_gateway(request).query(workflow_id, "openGates")
    return {"gates": gates}


@router.post("/{run_id}/signals/human")
async def signal_human_gate(
    run_id: str,
    body: HumanSignalRequest,
    request: Request,
    key: Annotated[ApiKey, Depends(require_client)],
) -> dict[str, str]:
    run = require_owned_run(request, key, run_id)
    workflow_id = run.get("workflow_id")
    if not isinstance(workflow_id, str):
        raise HTTPException(status_code=409, detail="run has no Temporal workflow ID")
    await temporal_gateway(request).signal(
        workflow_id,
        "submitHuman",
        {"cid": body.cid, "value": body.value},
    )
    return {"status": "delivered"}


def _normalized_temporal_status(raw: str) -> str:
    normalized = (
        raw.rsplit(".", 1)[-1]
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
        .replace("cancelled", "canceled")
    )
    if normalized == "notfound":
        return "not_found"
    if normalized in {"timed_out", "timeout"}:
        return "failed"
    return normalized


def _reconciled_terminal_event(
    run_id: str,
    workflow_id: str,
    status: str,
    error: Optional[str] = None,
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "runId": run_id,
        "workflowId": workflow_id,
        "segmentSeq": 0,
        "eventId": "__reconciled_terminal__",
        "type": "Did" if status == "completed" else "Failed",
        "node": "__run__",
        "cid": f"{run_id}:reconciled-terminal",
        "ts": time.time(),
        "causes": [],
        "attrs": {
            "terminal": True,
            "status": status,
            "reconciled": True,
        },
    }
    if error is not None:
        event["error"] = error
    return event


def _reconcile_terminal_run(
    store: ExecutionStore,
    *,
    run_id: str,
    workflow_id: str,
    status: str,
    error: Optional[str] = None,
) -> None:
    store.set_run_status(run_id, status, finished_at=time.time())
    row = store.get_run(run_id)
    if row is not None and row.get("status") == status:
        store.insert_events(
            [_reconciled_terminal_event(run_id, workflow_id, status, error)]
        )


async def reconcile_runs_once(store: ExecutionStore, gateway: TemporalGateway) -> None:
    """Repair submission and terminal-write crash windows idempotently."""

    for run in store.list_runs_by_status("submitting"):
        run_id = run.get("run_id")
        workflow_id = run.get("workflow_id")
        if not isinstance(run_id, str) or not isinstance(workflow_id, str):
            continue
        try:
            temporal_status = _normalized_temporal_status(await gateway.describe(workflow_id))
        except Exception as exc:
            if "notfound" not in type(exc).__name__.replace("_", "").lower():
                continue
            temporal_status = "not_found"
        if temporal_status in {"not_found", "missing"}:
            store.set_run_status(run_id, "start_failed", finished_at=time.time())
        elif temporal_status == "running":
            store.set_run_status(run_id, "accepted")
        elif temporal_status in TERMINAL_RUN_STATUSES:
            _reconcile_terminal_run(
                store,
                run_id=run_id,
                workflow_id=workflow_id,
                status=temporal_status,
            )

    for source_status in ("accepted", "running"):
        for run in store.list_runs_by_status(source_status):
            run_id = run.get("run_id")
            workflow_id = run.get("workflow_id")
            if not isinstance(run_id, str) or not isinstance(workflow_id, str):
                continue
            try:
                temporal_status = _normalized_temporal_status(
                    await gateway.describe(workflow_id)
                )
            except Exception:
                continue
            if temporal_status in TERMINAL_RUN_STATUSES:
                _reconcile_terminal_run(
                    store,
                    run_id=run_id,
                    workflow_id=workflow_id,
                    status=temporal_status,
                )


__all__ = ["reconcile_runs_once", "router"]
