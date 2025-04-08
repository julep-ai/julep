"""Query functions for creating secrets."""

from typing import Any
from uuid import UUID

from asyncpg import Connection, UniqueViolationError

from ...errors import DuplicateError
from ...models.secrets import Secret, SecretCreate


async def create_secret(
    conn: Connection,
    developer_id: UUID,
    secret: SecretCreate,
    encryption_key_id: str,
) -> Secret:
    """Create a new secret.

    Args:
        conn: Database connection
        developer_id: ID of the developer creating the secret
        secret: Secret to create
        encryption_key_id: ID of the key used for encryption

    Returns:
        The created secret

    Raises:
        DuplicateError: If a secret with this name already exists
    """
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO secrets (
                developer_id, name, description, value_encrypted,
                encryption_key_id, metadata
            )
            VALUES (
                $1, $2, $3,
                encrypt_secret($4, $5),
                $5, $6
            )
            RETURNING
                secret_id, developer_id, name, description,
                encryption_key_id, created_at, updated_at, metadata
            """,
            developer_id,
            secret.name,
            secret.description,
            secret.value,
            encryption_key_id,
            secret.metadata,
        )
    except UniqueViolationError as e:
        raise DuplicateError(f"Secret with name {secret.name} already exists") from e

    return Secret(**dict(row)) 