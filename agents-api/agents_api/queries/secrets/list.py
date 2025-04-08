"""Query functions for listing secrets."""

from typing import Any, Optional
from uuid import UUID

from asyncpg import Connection

from ...models.secrets import Secret


async def list_secrets(
    conn: Connection,
    developer_id: UUID,
    *,
    limit: int = 100,
    offset: int = 0,
    name_prefix: Optional[str] = None,
    metadata_filter: Optional[dict[str, Any]] = None,
) -> list[Secret]:
    """List secrets for a developer.

    Args:
        conn: Database connection
        developer_id: ID of the developer who owns the secrets
        limit: Maximum number of secrets to return
        offset: Number of secrets to skip
        name_prefix: Filter secrets by name prefix
        metadata_filter: Filter secrets by metadata

    Returns:
        List of secrets
    """
    query = """
        SELECT
            secret_id, developer_id, name, description,
            encryption_key_id, created_at, updated_at, metadata
        FROM secrets
        WHERE developer_id = $1
    """
    params: list[Any] = [developer_id]

    if name_prefix:
        query += " AND name LIKE $" + str(len(params) + 1) + " || '%'"
        params.append(name_prefix)

    if metadata_filter:
        for key, value in metadata_filter.items():
            query += f" AND metadata->>${len(params) + 1} = ${len(params) + 2}"
            params.extend([key, value])

    query += " ORDER BY name LIMIT $" + str(len(params) + 1) + " OFFSET $" + str(len(params) + 2)
    params.extend([limit, offset])

    rows = await conn.fetch(query, *params)
    return [Secret(**dict(row)) for row in rows] 