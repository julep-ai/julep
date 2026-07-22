"""Write-only operator vault endpoints and the scoped worker read seam."""

from __future__ import annotations

import logging
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from ...secrets import VaultCipher, register_secret_value, validate_secret_name
from ..auth import ApiKey, require_admin, require_worker
from . import execution_store

logger = logging.getLogger("julep.server.secrets")

router = APIRouter(prefix="/secrets", tags=["secrets"])


class PutSecretRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str = Field(min_length=1)


def _name(raw: str) -> str:
    try:
        return validate_secret_name(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _cipher(request: Request) -> VaultCipher:
    cipher = getattr(request.app.state, "vault_cipher", None)
    if not isinstance(cipher, VaultCipher):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="vault encryption is not configured",
        )
    return cipher


@router.put("/{name}")
async def put_secret(
    name: str,
    body: PutSecretRequest,
    request: Request,
    key: Annotated[ApiKey, Depends(require_admin)],
) -> dict[str, Any]:
    resolved_name = _name(name)
    row = execution_store(request).put_secret(
        resolved_name,
        body.value,
        key.name,
        _cipher(request),
    )
    register_secret_value(body.value)
    logger.info(
        "vault secret written name=%s generation=%s actor=%s",
        resolved_name,
        row["generation"],
        key.name,
    )
    return row


@router.get("")
async def list_secrets(
    request: Request,
    _key: Annotated[ApiKey, Depends(require_admin)],
) -> dict[str, Any]:
    return {"items": execution_store(request).list_secrets()}


@router.get("/{name}/value")
async def get_secret_value(
    name: str,
    request: Request,
    key: Annotated[ApiKey, Depends(require_worker)],
) -> JSONResponse:
    resolved_name = _name(name)
    allowlist = cast(frozenset[str], request.app.state.settings.worker_secret_allowlist)
    if resolved_name not in allowlist:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="secret is not in the worker read allowlist",
        )
    row = execution_store(request).get_secret(resolved_name)
    if row is None:
        raise HTTPException(status_code=404, detail="secret not found")
    if row.get("archived_at") is not None or row.get("ciphertext") is None:
        raise HTTPException(status_code=410, detail="secret is archived")
    try:
        value = _cipher(request).decrypt(
            resolved_name,
            int(row["generation"]),
            bytes(row["ciphertext"]),
            str(row["key_id"]),
        )
    except Exception as exc:
        logger.error(
            "vault secret decryption failed name=%s generation=%s error=%s",
            resolved_name,
            row.get("generation"),
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="vault secret could not be decrypted",
        ) from exc
    register_secret_value(value)
    logger.info(
        "vault secret read name=%s generation=%s worker=%s",
        resolved_name,
        row["generation"],
        key.name,
    )
    return JSONResponse(
        content={"value": value, "generation": int(row["generation"])},
        headers={"Cache-Control": "no-store"},
    )


@router.post("/{name}/archive")
async def archive_secret(
    name: str,
    request: Request,
    key: Annotated[ApiKey, Depends(require_admin)],
) -> dict[str, Any]:
    resolved_name = _name(name)
    row = execution_store(request).archive_secret(resolved_name, key.name)
    if row is None:
        raise HTTPException(status_code=404, detail="secret not found")
    logger.info("vault secret archived name=%s actor=%s", resolved_name, key.name)
    return row


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_secret(
    name: str,
    request: Request,
    key: Annotated[ApiKey, Depends(require_admin)],
) -> Response:
    resolved_name = _name(name)
    if not execution_store(request).delete_secret(resolved_name):
        raise HTTPException(status_code=404, detail="secret not found")
    logger.info("vault secret deleted name=%s actor=%s", resolved_name, key.name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["router"]
