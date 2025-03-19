"""Query for patching a secret."""

import logging
from typing import Any
from uuid import UUID

import bcrypt
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from pydantic import UUID4, BaseModel

from .create_secret import Secret

logger = logging.getLogger(__name__)


class PatchSecretInput(BaseModel):
    """Input model for patching a secret."""

    name: str | None = None
    value: str | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None
    agent_id: UUID4 | None = None


async def patch_secret(
    conn: AsyncConnection[dict[str, Any]],
    secret_id: UUID,
    developer_id: UUID,
    input: PatchSecretInput,
) -> Secret | None:
    """Patch a secret.

    Args:
        conn: The database connection.
        secret_id: ID of the secret to patch.
        developer_id: ID of the developer who owns the secret.
        input: The partial secret data to update.

    Returns:
        The patched secret or None if not found.
    """
    try:
        # Build the SET clause and params dynamically based on provided fields
        set_clauses = []
        params: list[Any] = []

        if input.name is not None:
            set_clauses.append(f"name = ${len(params) + 1}")
            params.append(input.name)

        if input.value is not None:
            salt = bcrypt.gensalt()
            hashed_value = bcrypt.hashpw(input.value.encode(), salt).decode()
            set_clauses.append(f"value = ${len(params) + 1}")
            params.append(hashed_value)

        if input.description is not None:
            set_clauses.append(f"description = ${len(params) + 1}")
            params.append(input.description)

        if input.metadata is not None:
            set_clauses.append(f"metadata = ${len(params) + 1}")
            params.append(input.metadata)

        if input.agent_id is not None:
            set_clauses.append(f"agent_id = ${len(params) + 1}")
            params.append(input.agent_id)

        # Always update updated_at timestamp
        set_clauses.append("updated_at = NOW()")

        if not set_clauses:
            # Nothing to update
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT
                        id,
                        name,
                        description,
                        metadata,
                        developer_id,
                        agent_id,
                        created_at,
                        updated_at
                    FROM secrets
                    WHERE id = $1 AND developer_id = $2
                    """,
                    [secret_id, developer_id],
                )
                result = await cur.fetchone()

            if not result:
                return None

            return Secret(**result)

        # Build and execute the query
        query = f"""
            UPDATE secrets
            SET {", ".join(set_clauses)}
            WHERE id = ${len(params) + 1} AND developer_id = ${len(params) + 2}
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

        params.extend([secret_id, developer_id])

        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            result = await cur.fetchone()

        if not result:
            return None

        return Secret(**result)

    except Exception as e:
        logger.error(f"Error patching secret: {e}")
        raise
