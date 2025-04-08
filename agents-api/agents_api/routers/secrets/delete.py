"""Delete secret endpoint."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status

from ...dependencies.auth import get_api_key
from ...dependencies.db import get_db_connection
from ...models.secrets import Secret
from ...queries.secrets import delete_secret
from .router import router


@router.delete("/secrets/{secret_id}", response_model=Secret)
async def delete_secret(
    secret_id: UUID,
    conn: Annotated[get_db_connection, Depends()],
    developer_id: Annotated[UUID, Depends(get_api_key)],
) -> Secret:
    """Delete a secret.

    Args:
        secret_id: ID of the secret to delete
        conn: Database connection
        developer_id: ID of the developer who owns the secret

    Returns:
        The deleted secret

    Raises:
        HTTPException: If the secret doesn't exist
    """
    try:
        return await delete_secret(conn, secret_id, developer_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
