"""Query functions for listing secrets."""

from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import Secret
from ...common.utils.db_exceptions import common_db_exceptions
from ...env import secrets_master_key
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

query = """
SELECT
    secret_id, developer_id, agent_id, name, description,
    created_at, updated_at, metadata,
    decrypt_secret(value_encrypted, $5) as value
FROM secrets
WHERE (
    (developer_id = $1 AND $1 IS NOT NULL) OR
    (agent_id = $2 AND $2 IS NOT NULL)
)
ORDER BY created_at DESC
LIMIT $3
OFFSET $4
"""


@wrap_in_class(
    Secret,
    transform=lambda d: {**d, "id": d["secret_id"]},
)
@pg_query
@beartype
async def list_secrets_query(
    *,
    developer_id: UUID | None,
    agent_id: UUID | None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[str, list]:
    return (
        query,
        [
            developer_id,
            agent_id,
            limit,
            offset,
            secrets_master_key,
        ],
    )


list_secrets = rewrap_exceptions(common_db_exceptions("secret", ["list"]))(list_secrets_query)
