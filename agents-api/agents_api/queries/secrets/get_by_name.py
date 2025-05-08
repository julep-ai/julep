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
    decrypt_secret(value_encrypted, $4) as value
FROM secrets
WHERE (
    developer_id = $1 AND
    ($2::UUID IS NULL OR agent_id = $2) AND
    name = $3
)
LIMIT 1;
"""

#TODO: handle HTTPException: 404: No secret found during get_by_name, shouldn't be an error
@wrap_in_class(
    Secret,
    one=True,
    transform=lambda d: {**d, "id": d["secret_id"]},
)
@pg_query
@beartype
async def get_secret_by_name_query(
    *,
    developer_id: UUID | None,
    agent_id: UUID | None = None,
    name: str,
) -> tuple[str, list]:
    return (
        query,
        [
            developer_id,
            agent_id,
            name,
            secrets_master_key,
        ],
    )


get_secret_by_name = rewrap_exceptions(common_db_exceptions("secret", ["get_by_name"]))(get_secret_by_name_query)
