"""Query functions for updating secrets."""

from typing import Any
from uuid import UUID

from asyncpg import Connection

from ...autogen.openapi_model import Secret
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, wrap_in_class, rewrap_exceptions
from beartype import beartype


query = f"""
    UPDATE secrets
    SET {", ".join(updates)}, updated_at = NOW()
    WHERE secret_id = $1 AND developer_id = $2
    RETURNING
        secret_id, developer_id, name, description,
        encryption_key_id, created_at, updated_at, metadata
"""


@rewrap_exceptions(common_db_exceptions("secret", ["update"]))
@wrap_in_class(
    Secret,
    one=True,
    transform=lambda d: {**d, "id": d["secret_id"]},
)
@query_metrics("update_secret")
@pg_query
@beartype
async def update_secret(
    conn: Connection,
    secret_id: UUID,
    developer_id: UUID,
    *,
    name: str | None = None,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[str, list]:
    return []
