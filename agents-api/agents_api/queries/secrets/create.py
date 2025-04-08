"""Query functions for creating secrets."""

from typing import Any
from uuid import UUID

from agents_api.autogen.openapi_model import Secret
from beartype import beartype
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, wrap_in_class, rewrap_exceptions

query = """
INSERT INTO secrets (
    developer_id, secret_id, name, description, value_encrypted, metadata
)
VALUES (
    $1, $2, $3, $4, encrypt_secret($5, $6), $7
)
RETURNING *;
"""


@rewrap_exceptions(common_db_exceptions("secret", ["create"]))
@wrap_in_class(
    Secret,
    one=True,
    transform=lambda d: {**d, "id": d["secret_id"]},
)
@query_metrics("create_secret")
@pg_query
@beartype
async def create_secret(
    developer_id: UUID,
    secret_id: UUID,
    name: str,
    description: str,
    value: str,
    metadata: dict[str, Any],
) -> tuple[str, list]:
    return []
