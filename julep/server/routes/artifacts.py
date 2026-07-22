"""Credential-free-for-workers artifact-store proxy endpoints."""

from __future__ import annotations

import hashlib
import re
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status

from ..auth import ApiKey, require_admin, require_key
from . import artifact_store

_SHA256 = re.compile(r"^[0-9a-f]{64}$")

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


def _validate_digest(digest: str) -> None:
    if _SHA256.fullmatch(digest) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sha256 must be 64 lowercase hexadecimal characters",
        )


@router.put("/{sha256}")
async def put_blob(
    sha256: str,
    request: Request,
    body: Annotated[bytes, Body(media_type="application/octet-stream")],
    _key: Annotated[ApiKey, Depends(require_admin)],
) -> Response:
    _validate_digest(sha256)
    actual = hashlib.sha256(body).hexdigest()
    if actual != sha256:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"content digest mismatch: expected {sha256}, got {actual}",
        )

    store = artifact_store(request)
    existed = store.has(sha256)
    stored = store.put(body)
    if stored != sha256:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="artifact-store returned an unexpected content digest",
        )
    return Response(status_code=200 if existed else 201)


@router.head("/{sha256}")
async def head_blob(
    sha256: str,
    request: Request,
    _key: Annotated[ApiKey, Depends(require_key)],
) -> Response:
    _validate_digest(sha256)
    return Response(status_code=200 if artifact_store(request).has(sha256) else 404)


__all__ = ["router"]
