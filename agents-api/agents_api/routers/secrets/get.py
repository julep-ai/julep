"""Get secret endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from ...dependencies.auth import get_api_key
from ...dependencies.db import get_db_connection
from ...models.secrets import Secret, SecretValue
from ...queries.secrets import get_secret, get_secret_value
from .router import router


@router.get("/secrets/{secret_id}", response_model=Secret)
async def get_secret(
    secret_id: UUID,
    conn: Annotated[get_db_connection, Depends()],
    developer_id: Annotated[UUID, Depends(get_api_key)],
) -> Secret:
    """Get a secret by ID.

    Args:
        secret_id: ID of the secret to get
        conn: Database connection
        developer_id: ID of the developer who owns the secret

    Returns:
        The secret

    Raises:
        HTTPException: If the secret doesn't exist
    """
    try:
        return await get_secret(conn, developer_id, secret_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get("/{secret_id}/value", response_model=SecretValue)
async def get_secret_value_endpoint(
    secret_id: UUID,
    conn: Annotated[get_db_connection, Depends()],
    developer_id: Annotated[UUID, Depends(get_api_key)],
) -> SecretValue:
    """Get a secret's decrypted value.

    Args:
        secret_id: ID of the secret to get
        conn: Database connection
        developer_id: ID of the developer who owns the secret

    Returns:
        The decrypted secret value

    Raises:
        HTTPException: If the secret doesn't exist
    """
    try:
        return await get_secret_value(conn, developer_id, secret_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e 