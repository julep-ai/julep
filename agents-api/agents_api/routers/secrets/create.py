"""Create secret endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from ...dependencies.auth import get_api_key
from ...dependencies.db import get_db_connection
from ...env import secrets_master_key
from ...models.secrets import Secret, SecretCreate
from ...queries.secrets import create_secret
from .router import router


@router.post("/secrets", response_model=Secret)
async def create_secret(
    secret: SecretCreate,
    conn: Annotated[get_db_connection, Depends()],
    developer_id: Annotated[UUID, Depends(get_api_key)],
) -> Secret:
    """Create a new secret.

    Args:
        secret: Secret to create
        conn: Database connection
        developer_id: ID of the developer creating the secret

    Returns:
        The created secret

    Raises:
        HTTPException: If a secret with this name already exists
    """
    try:
        return await create_secret(conn, developer_id, secret, secrets_master_key)
    except DuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e 