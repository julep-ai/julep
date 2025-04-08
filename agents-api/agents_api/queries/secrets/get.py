"""Query functions for getting secrets."""

from typing import Any
from uuid import UUID

from asyncpg import Connection

from ...errors import NotFoundError
from ...models.secrets import Secret, SecretValue


async def get_secret(
    conn: Connection,
    developer_id: UUID,
    secret_id: UUID,
) -> Secret:
    """Get a secret by ID.

    Args:
        conn: Database connection
        developer_id: ID of the developer who owns the secret
        secret_id: ID of the secret to get

    Returns:
        The secret

    Raises:
        NotFoundError: If the secret doesn't exist
    """
    row = await conn.fetchrow(
        """
        SELECT
            secret_id, developer_id, name, description,
            encryption_key_id, created_at, updated_at, metadata
        FROM secrets
        WHERE secret_id = $1 AND developer_id = $2
        """,
        secret_id,
        developer_id,
    )
    if not row:
        raise NotFoundError(f"Secret {secret_id} not found")

    return Secret(**dict(row))


async def get_secret_value(
    conn: Connection,
    developer_id: UUID,
    secret_id: UUID,
) -> SecretValue:
    """Get a secret's decrypted value.

    Args:
        conn: Database connection
        developer_id: ID of the developer who owns the secret
        secret_id: ID of the secret to get

    Returns:
        The decrypted secret value

    Raises:
        NotFoundError: If the secret doesn't exist
    """
    row = await conn.fetchrow(
        """
        SELECT decrypt_secret(value_encrypted, encryption_key_id) as value
        FROM secrets
        WHERE secret_id = $1 AND developer_id = $2
        """,
        secret_id,
        developer_id,
    )
    if not row:
        raise NotFoundError(f"Secret {secret_id} not found")

    return SecretValue(value=row["value"])


async def get_secret_by_name(
    conn: Connection,
    developer_id: UUID,
    secret_name: str,
) -> str:
    """Get a secret's value by its name.

    This is the main function to use in tasks and sessions to access secrets.
    It's designed to be used at setup time, not during execution.

    Args:
        conn: Database connection
        developer_id: ID of the developer who owns the secret
        secret_name: Name of the secret to get

    Returns:
        The decrypted secret value

    Raises:
        ValueError: If the secret doesn't exist
    """
    row = await conn.fetchrow(
        """
        SELECT decrypt_secret(value_encrypted, encryption_key_id) as value
        FROM secrets
        WHERE developer_id = $1 AND name = $2
        """,
        developer_id,
        secret_name,
    )
    if not row:
        raise ValueError(f"Secret {secret_name} not found")

    return row["value"]


async def get_secrets_by_prefix(
    conn: Connection,
    developer_id: UUID,
    prefix: str,
) -> dict[str, str]:
    """Get all secrets with names starting with a prefix.

    This is useful for getting groups of related secrets, like all API keys
    for a particular service.

    Args:
        conn: Database connection
        developer_id: ID of the developer who owns the secrets
        prefix: Prefix to match secret names against

    Returns:
        Dictionary mapping secret names to their decrypted values
    """
    rows = await conn.fetch(
        """
        SELECT
            name,
            decrypt_secret(value_encrypted, encryption_key_id) as value
        FROM secrets
        WHERE developer_id = $1 AND name LIKE $2 || '%'
        ORDER BY name
        """,
        developer_id,
        prefix,
    )
    return {row["name"]: row["value"] for row in rows}


async def get_secret_metadata(
    conn: Connection,
    developer_id: UUID,
    secret_name: str,
) -> dict[str, Any]:
    """Get a secret's metadata by its name.

    Args:
        conn: Database connection
        developer_id: ID of the developer who owns the secret
        secret_name: Name of the secret to get

    Returns:
        The secret's metadata

    Raises:
        ValueError: If the secret doesn't exist
    """
    row = await conn.fetchrow(
        """
        SELECT metadata
        FROM secrets
        WHERE developer_id = $1 AND name = $2
        """,
        developer_id,
        secret_name,
    )
    if not row:
        raise ValueError(f"Secret {secret_name} not found")

    return row["metadata"] 