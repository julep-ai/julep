"""Query functions for updating secrets."""

from typing import Any
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import Secret
from ...common.utils.db_exceptions import common_db_exceptions
from ...env import secrets_master_key
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

query = """
    UPDATE secrets
    SET updated_at = NOW(),
        name = COALESCE($4, name),
        description = COALESCE($5, description),
        metadata = COALESCE($6, metadata),
        value_encrypted = CASE
            WHEN $7::text IS NOT NULL THEN encrypt_secret($7::text, $8)
            ELSE value_encrypted
        END
    WHERE secret_id = $1
    AND (
        (developer_id = $2 AND $2 IS NOT NULL) OR
        (agent_id = $3 AND $3 IS NOT NULL)
    )
    RETURNING *;
"""


@rewrap_exceptions(common_db_exceptions("secret", ["update"]))
@wrap_in_class(
    Secret,
    one=True,
    transform=lambda d: {**d, "id": d["secret_id"], "value": "ENCRYPTED"},
)
@query_metrics("update_secret")
@pg_query
@beartype
async def update_secret(
    *,
    secret_id: UUID,
    developer_id: UUID | None = None,
    agent_id: UUID | None = None,
    name: str | None = None,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
    value: str | None = None,
) -> tuple[str, list]:
    return (
        query,
        [
            secret_id,
            developer_id,
            agent_id,
            name,
            description,
            metadata,
            value,
            secrets_master_key,
        ],
    )
