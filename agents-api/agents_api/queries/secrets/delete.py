"""Query functions for deleting secrets."""

from uuid import UUID

from asyncpg import Connection

from ...models.secrets import Secret


async def delete_secret(conn: Connection, secret_id: UUID, developer_id: UUID) -> Secret:
    """Delete a secret.

    Args:
        conn: Database connection
        secret_id: ID of the secret to delete
        developer_id: ID of the developer who owns the secret

    Returns:
        Deleted secret

    Raises:
        NotFoundError: If the secret does not exist
    """
    query = """
        DELETE FROM secrets
        WHERE secret_id = $1 AND developer_id = $2
        RETURNING
            secret_id, developer_id, name, description,
            encryption_key_id, created_at, updated_at, metadata
    """

    row = await conn.fetchrow(query, secret_id, developer_id)
    if not row:
        raise NotFoundError(f"Secret {secret_id} not found")

    return Secret(**dict(row)) 