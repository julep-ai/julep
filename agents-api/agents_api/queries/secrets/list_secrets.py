"""Query for listing secrets."""

import logging
from typing import Any
from uuid import UUID

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from pydantic import UUID4, BaseModel

logger = logging.getLogger(__name__)


class SecretSummary(BaseModel):
    """Model for a secret summary (without value)."""

    id: UUID4
    name: str
    description: str | None = None
    created_at: str
    updated_at: str
    agent_id: UUID4 | None = None


async def list_secrets(
    conn: AsyncConnection[dict[str, Any]],
    developer_id: UUID,
    agent_id: UUID | None = None,
) -> list[SecretSummary]:
    """List secrets for a developer or agent.

    Args:
        conn: The database connection.
        developer_id: ID of the developer who owns the secrets.
        agent_id: Optional ID of the agent if listing agent-specific secrets.

    Returns:
        List of secret summaries.
    """
    try:
        query = """
            SELECT
                id,
                name,
                description,
                agent_id,
                created_at,
                updated_at
            FROM secrets
            WHERE developer_id = $1
        """
        params: list[Any] = [developer_id]

        if agent_id:
            query += " AND (agent_id = $2 OR agent_id IS NULL)"
            params.append(agent_id)

        query += " ORDER BY name"

        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            results = await cur.fetchall()

        return [SecretSummary(**row) for row in results]

    except Exception as e:
        logger.error(f"Error listing secrets: {e}")
        raise
