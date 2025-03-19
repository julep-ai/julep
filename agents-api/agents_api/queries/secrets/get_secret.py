"""Query for retrieving secrets."""

import logging
from typing import Any, cast
from uuid import UUID

from psycopg import AsyncConnection
from psycopg.rows import dict_row

from .create_secret import Secret

logger = logging.getLogger(__name__)


async def get_secret(
    conn: AsyncConnection[dict[str, Any]],
    secret_id: UUID,
    developer_id: UUID,
) -> Secret | None:
    """Get a secret by ID.

    Args:
        conn: The database connection.
        secret_id: ID of the secret to retrieve.
        developer_id: ID of the developer who owns the secret.

    Returns:
        The secret or None if not found.
    """
    try:
        query = """
            SELECT
                secret_id as id,
                name,
                description,
                metadata,
                developer_id,
                agent_id,
                created_at,
                updated_at
            FROM secrets
            WHERE secret_id = $1 AND developer_id = $2
        """

        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, [secret_id, developer_id])
            result = await cur.fetchone()

        if not result:
            return None

        return Secret(**result)

    except Exception as e:
        logger.error(f"Error getting secret: {e}")
        raise


async def get_secret_by_name(
    conn: AsyncConnection[dict[str, Any]],
    name: str,
    developer_id: UUID,
    agent_id: UUID | None = None,
) -> tuple[str, dict[str, Any]] | None:
    """Get a secret value by name.

    Args:
        conn: The database connection.
        name: Name of the secret to retrieve.
        developer_id: ID of the developer who owns the secret.
        agent_id: Optional ID of the agent if it's an agent-specific secret.

    Returns:
        Tuple of the secret value and metadata if found, None otherwise.
    """
    try:
        # If agent_id is provided, first try to get agent-specific secret
        if agent_id:
            query = """
                SELECT value, metadata
                FROM secrets
                WHERE name = $1 AND developer_id = $2 AND agent_id = $3
            """
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, [name, developer_id, agent_id])
                result = await cur.fetchone()

            if result:
                return result["value"], cast(dict[str, Any], result["metadata"])

        # If not found or no agent_id, try to get developer-wide secret
        query = """
            SELECT value, metadata
            FROM secrets
            WHERE name = $1 AND developer_id = $2 AND agent_id IS NULL
        """
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, [name, developer_id])
            result = await cur.fetchone()

        if not result:
            return None

        return result["value"], cast(dict[str, Any], result["metadata"])

    except Exception as e:
        logger.error(f"Error getting secret by name: {e}")
        raise
