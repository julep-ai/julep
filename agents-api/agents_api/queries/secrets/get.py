"""Query functions for getting secrets."""

from typing import Any
from uuid import UUID

from asyncpg import Connection

from ...autogen.openapi_model import Secret
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, wrap_in_class, rewrap_exceptions
from beartype import beartype


query = """
SELECT
    secret_id, developer_id, name, description,
    encryption_key_id, created_at, updated_at, metadata
FROM secrets
WHERE secret_id = $1 AND developer_id = $2
"""


@rewrap_exceptions(common_db_exceptions("secret", ["get"]))
@wrap_in_class(
    Secret,
    one=True,
    transform=lambda d: {**d, "id": d["secret_id"]},
)
@pg_query
@beartype
async def get_secret(
    conn: Connection,
    developer_id: UUID,
    secret_id: UUID,
) -> tuple[str, list]:
    return []
