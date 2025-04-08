"""List secrets endpoint."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...dependencies.auth import get_api_key
from ...dependencies.db import get_db_connection
from ...models.secrets import Secret
from ...queries.secrets import list_secrets
from .router import router


@router.get("/secrets", response_model=list[Secret])
async def list_secrets(
    conn: Annotated[get_db_connection, Depends()],
    developer_id: Annotated[UUID, Depends(get_api_key)],
    *,
    limit: int = 100,
    offset: int = 0,
    name_prefix: str | None = None,
) -> list[Secret]:
    """List all secrets for a developer.

    Args:
        conn: Database connection
        developer_id: ID of the developer whose secrets to list
        limit: Maximum number of secrets to return
        offset: Number of secrets to skip
        name_prefix: Filter secrets by name prefix

    Returns:
        List of secrets
    """
    return await list_secrets(
        conn,
        developer_id,
        limit=limit,
        offset=offset,
        name_prefix=name_prefix,
    )
