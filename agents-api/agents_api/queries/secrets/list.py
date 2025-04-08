"""Query functions for listing secrets."""

from typing import Any
from uuid import UUID

from asyncpg import Connection

from ...autogen.openapi_model import Secret
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, wrap_in_class, rewrap_exceptions
from beartype import beartype


query = """
SELECT
    secret_id, developer_id, name, description,
    encryption_key_id, created_at, updated_at, metadata
FROM secrets
WHERE developer_id = $1
"""


@rewrap_exceptions(common_db_exceptions("secret", ["list"]))
@wrap_in_class(
    Secret,
    transform=lambda d: {**d, "id": d["secret_id"]},
)
@pg_query
@beartype
async def list_secrets(
    conn: Connection,
    developer_id: UUID,
    *,
    limit: int = 100,
    offset: int = 0,
    name_prefix: str | None = None,
    metadata_filter: dict[str, Any] | None = None,
) -> tuple[str, list]:
    return []
