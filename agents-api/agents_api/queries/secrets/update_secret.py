"""Query for updating a secret."""

import logging
from typing import Any
from uuid import UUID

import bcrypt
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from pydantic import UUID4, BaseModel

from .create_secret import Secret

logger = logging.getLogger(__name__)


class UpdateSecretInput(BaseModel):
    """Input model for updating a secret."""

    name: str
    value: str
    description: str | None = None
    metadata: dict[str, Any] | None = None
    agent_id: UUID4 | None = None


async def update_secret(
    conn: AsyncConnection[dict[str, Any]],
    secret_id: UUID,
    developer_id: UUID,
    input: UpdateSecretInput,
) -> Secret | None:
    """Update a secret.

    Args:
        conn: The database connection.
        secret_id: ID of the secret to update.
        developer_id: ID of the developer who owns the secret.
        input: The updated secret data.

    Returns:
        The updated secret or None if not found.
    """
    try:
        # Generate salt and hash the secret value
        salt = bcrypt.gensalt()
        hashed_value = bcrypt.hashpw(input.value.encode(), salt).decode()

        query = """
            UPDATE secrets
            SET
                name = $1,
                value = $2,
                description = $3,
                metadata = $4,
                agent_id = $5,
                updated_at = NOW()
            WHERE id = $6 AND developer_id = $7
            RETURNING
                id,
                name,
                description,
                metadata,
                developer_id,
                agent_id,
                created_at,
                updated_at
        """

        params = [
            input.name,
            hashed_value,
            input.description,
            input.metadata or {},
            input.agent_id,
            secret_id,
            developer_id,
        ]

        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            result = await cur.fetchone()

        if not result:
            return None

        return Secret(**result)

    except Exception as e:
        logger.error(f"Error updating secret: {e}")
        raise
