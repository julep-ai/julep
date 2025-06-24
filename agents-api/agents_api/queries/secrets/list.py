"""Query functions for listing secrets."""

from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import Secret
from ...common.utils.db_exceptions import common_db_exceptions
from ...env import secrets_master_key
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

query = """
SELECT
    secret_id, developer_id, name, description,
    created_at, updated_at, metadata,
    CASE WHEN $5 = True THEN decrypt_secret(value_encrypted, $4) ELSE 'ENCRYPTED' END as value
FROM secrets
WHERE (
    developer_id = $1
)
ORDER BY created_at DESC
LIMIT $2
OFFSET $3
"""


@wrap_in_class(
    Secret,
    transform=lambda d: {**d, "id": d["secret_id"]},
)
@pg_query
@beartype
async def list_secrets_query(
    *,
    developer_id: UUID,
    limit: int = 100,
    offset: int = 0,
    decrypt: bool = False,
) -> tuple[str, list]:
    return (
        query,
        [
            developer_id,
            limit,
            offset,
            secrets_master_key,
            decrypt,
        ],
    )


list_secrets = rewrap_exceptions(common_db_exceptions("secret", ["list"]))(
    list_secrets_query
)
