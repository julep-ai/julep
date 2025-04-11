"""Query functions for getting secrets."""

from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import GetSecretRequest, Secret
from ...common.utils.db_exceptions import common_db_exceptions
from ...env import secrets_master_key
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

query = """
SELECT
    secret_id,
    created_at,
    updated_at,
    metadata,
    developer_id,
    agent_id,
    name,
    description,
    decrypt_secret(value, $4) as value
FROM secrets
WHERE name = $1 AND (
    (developer_id = $2 AND $2 IS NOT NULL) OR
    (agent_id = $3 AND $3 IS NOT NULL)
)
"""


@wrap_in_class(
    Secret,
    one=True,
    transform=lambda d: {**d, "id": d["secret_id"]},
)
@pg_query
@beartype
async def get_secret_query(
    *,
    developer_id: UUID | None,
    agent_id: UUID | None,
    data: GetSecretRequest,
) -> tuple[str, list]:
    return (
        query,
        [
            data.name,
            developer_id,
            agent_id,
            secrets_master_key,
        ],
    )


get_secret = rewrap_exceptions(common_db_exceptions("secret", ["get"]))(get_secret_query)
