"""Query functions for updating secrets."""

from typing import Any, Optional
from uuid import UUID

from asyncpg import Connection

from ...models.secrets import Secret


async def update_secret(
    conn: Connection,
    secret_id: UUID,
    developer_id: UUID,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> Secret:
    """Update a secret's metadata.

    Args:
        conn: Database connection
        secret_id: ID of the secret to update
        developer_id: ID of the developer who owns the secret
        name: New name for the secret
        description: New description for the secret
        metadata: New metadata for the secret

    Returns:
        Updated secret

    Raises:
        NotFoundError: If the secret does not exist
    """
    updates: list[str] = []
    params: list[Any] = [secret_id, developer_id]

    if name is not None:
        updates.append("name = $" + str(len(params) + 1))
        params.append(name)

    if description is not None:
        updates.append("description = $" + str(len(params) + 1))
        params.append(description)

    if metadata is not None:
        updates.append("metadata = $" + str(len(params) + 1))
        params.append(metadata)

    if not updates:
        return await get_secret(conn, secret_id, developer_id)

    query = f"""
        UPDATE secrets
        SET {", ".join(updates)}, updated_at = NOW()
        WHERE secret_id = $1 AND developer_id = $2
        RETURNING
            secret_id, developer_id, name, description,
            encryption_key_id, created_at, updated_at, metadata
    """

    row = await conn.fetchrow(query, *params)
    if not row:
        raise NotFoundError(f"Secret {secret_id} not found")

    return Secret(**dict(row)) 