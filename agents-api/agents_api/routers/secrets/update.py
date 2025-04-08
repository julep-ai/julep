"""Update secret endpoint."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status

from ...dependencies.auth import get_api_key
from ...dependencies.db import get_db_connection
from ...models.secrets import Secret, SecretUpdate
from ...queries.secrets import update_secret
from .router import router


@router.put("/secrets/{secret_id}", response_model=Secret)
async def update_secret(
    secret_id: UUID,
    secret: SecretUpdate,
    conn: Annotated[get_db_connection, Depends()],
    developer_id: Annotated[UUID, Depends(get_api_key)],
) -> Secret:
    """Update a secret.

    Args:
        secret_id: ID of the secret to update
        secret: New secret data
        conn: Database connection
        developer_id: ID of the developer who owns the secret

    Returns:
        The updated secret

    Raises:
        HTTPException: If the secret doesn't exist
    """
    try:
        return await update_secret(
            conn,
            secret_id,
            developer_id,
            name=secret.name,
            description=secret.description,
            metadata=secret.metadata,
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
