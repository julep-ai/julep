"""Query for creating a new secret."""

import logging
from typing import Any
from uuid import UUID

import bcrypt
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from pydantic import UUID4, BaseModel

logger = logging.getLogger(__name__)


class SecretInput(BaseModel):
    """Input model for creating a new secret."""

    name: str
    value: str
    description: str | None = None
    metadata: dict[str, Any] | None = None
    agent_id: UUID4 | None = None


class Secret(BaseModel):
    """Output model for a secret."""

    id: UUID4
    name: str
    description: str | None = None
    metadata: dict[str, Any] | None = None
    agent_id: UUID4 | None = None
    developer_id: UUID4
    created_at: str
    updated_at: str


async def create_secret(
    conn: AsyncConnection[dict[str, Any]],
    developer_id: UUID,
    input: SecretInput,
) -> Secret:
    """Create a new secret for a developer or agent.

    Args:
        conn: The database connection.
        developer_id: ID of the developer who owns the secret.
        input: The secret data to create.

    Returns:
        The created secret (without the value).

    Raises:
        Exception: If there's an error creating the secret.
    """
    try:
        # Generate salt and hash the secret value
        salt = bcrypt.gensalt()
        hashed_value = bcrypt.hashpw(input.value.encode(), salt).decode()

        # Create the query
        query = """
            INSERT INTO secrets (
                name,
                value,
                description,
                metadata,
                developer_id,
                agent_id
            )
            VALUES (
                $1, $2, $3, $4, $5, $6
            )
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

        # Execute the query
        params = [
            input.name,
            hashed_value,
            input.description,
            input.metadata or {},
            developer_id,
            input.agent_id,
        ]

        # Create a cursor with dict rows
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            result = await cur.fetchone()

        if not result:
            msg = "Failed to create secret"
            raise Exception(msg)

        # Convert result to Secret model
        return Secret(**result)

    except Exception as e:
        logger.error(f"Error creating secret: {e}")
        raise
