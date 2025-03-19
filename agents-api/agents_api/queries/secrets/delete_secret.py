"""Query for deleting a secret."""

import logging
from typing import Any
from uuid import UUID

from psycopg import AsyncConnection
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)


async def delete_secret(
    conn: AsyncConnection[dict[str, Any]],
    secret_id: UUID,
    developer_id: UUID,
) -> bool:
    """Delete a secret.

    Args:
        conn: The database connection.
        secret_id: ID of the secret to delete.
        developer_id: ID of the developer who owns the secret.

    Returns:
        True if secret was deleted, False if it wasn't found.
    """
    try:
        query = """
            DELETE FROM secrets
            WHERE secret_id = $1 AND developer_id = $2
            RETURNING secret_id as id
        """

        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, [secret_id, developer_id])
            result = await cur.fetchone()

        return result is not None

    except Exception as e:
        logger.error(f"Error deleting secret: {e}")
        raise
