"""Immutable application-release publication and lookup routes."""

from __future__ import annotations

import json
import re
import time
from collections.abc import Mapping
from typing import Annotated, Any, Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from ...app_deploy import (
    ApplicationRelease,
    ApplicationReleaseError,
    release_from_bytes,
)
from ...ir import canonical_json
from ..auth import ApiKey, require_admin, require_client
from . import artifact_store, execution_store

_SHA256 = re.compile(r"^[0-9a-f]{64}$")

router = APIRouter(prefix="/releases", tags=["releases"])


def normalize_release_hash(value: str) -> str:
    normalized = value if value.startswith("sha256:") else f"sha256:{value}"
    if _SHA256.fullmatch(normalized.removeprefix("sha256:")) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="release must be sha256:<64 lowercase hexadecimal characters>",
        )
    return normalized


def rehydrate_release(row: Mapping[str, Any]) -> ApplicationRelease:
    manifest = row.get("manifest")
    if not isinstance(manifest, Mapping):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="stored release manifest is invalid",
        )
    try:
        encoded = canonical_json(manifest).encode("utf-8")
        release = release_from_bytes(encoded)
    except (ApplicationReleaseError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"stored release manifest is invalid: {exc}",
        ) from exc
    stored_hash = row.get("release_hash")
    if stored_hash != release.release_hash:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="stored release hash does not match its manifest",
        )
    return release


def load_release(request: Request, release_hash: str) -> tuple[dict[str, Any], ApplicationRelease]:
    normalized = normalize_release_hash(release_hash)
    row = execution_store(request).get_release(normalized)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="release not found")
    return row, rehydrate_release(row)


def _referenced_digests(release: ApplicationRelease) -> set[str]:
    digests: set[str] = set()
    for pipeline in release.pipelines:
        for reference in pipeline.bundle_ref or ():
            for name in ("bundleHash", "signatureDigest"):
                value = reference.get(name)
                if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"invalid {name} in bundleRef for pipeline {pipeline.name!r}",
                    )
                digests.add(value)
        runtime_ref = pipeline.runtime_declarations_ref
        if runtime_ref is not None:
            value = runtime_ref.get("hash")
            if not isinstance(value, str):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"invalid runtimeDeclarationsRef for pipeline {pipeline.name!r}",
                )
            digest = value.removeprefix("sha256:")
            if _SHA256.fullmatch(digest) is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"invalid runtimeDeclarationsRef for pipeline {pipeline.name!r}",
                )
            digests.add(digest)
    return digests


@router.post("")
async def publish_release(
    request: Request,
    _key: Annotated[ApiKey, Depends(require_admin)],
) -> JSONResponse:
    data = await request.body()
    try:
        release = release_from_bytes(data)
    except (ApplicationReleaseError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    artifacts = artifact_store(request)
    missing = sorted(digest for digest in _referenced_digests(release) if not artifacts.has(digest))
    if missing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "release references missing artifact-store blobs", "digests": missing},
        )

    manifest_digest = artifacts.put(release.manifest_bytes)
    if manifest_digest != release.release_hash.removeprefix("sha256:"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="artifact-store returned an unexpected release-manifest digest",
        )

    store = execution_store(request)
    existing = store.get_release(release.release_hash)
    manifest = cast(dict[str, Any], json.loads(release.manifest_bytes))
    store.put_release(
        release.release_hash,
        release.application,
        manifest,
        time.time(),
    )
    row = store.get_release(release.release_hash)
    assert row is not None
    return JSONResponse(status_code=200 if existing is not None else 201, content=row)


@router.get("")
async def list_releases(
    request: Request,
    _key: Annotated[ApiKey, Depends(require_client)],
    cursor: Optional[str] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, Any]:
    try:
        rows, next_cursor = execution_store(request).list_releases(cursor, limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid release cursor") from exc
    return {"items": rows, "next_cursor": next_cursor}


@router.get("/{release_hash}")
async def get_release(
    release_hash: str,
    request: Request,
    _key: Annotated[ApiKey, Depends(require_client)],
) -> dict[str, Any]:
    row, _release = load_release(request, release_hash)
    return row


__all__ = ["load_release", "normalize_release_hash", "rehydrate_release", "router"]
