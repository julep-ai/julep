"""Query functions for creating secrets."""

from typing import Any
from uuid import UUID

from beartype import beartype
from uuid_extensions import uuid7

from agents_api.autogen.openapi_model import Secret

from ...common.utils.db_exceptions import common_db_exceptions
from ...env import secrets_master_key
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

query = """
INSERT INTO secrets (
    secret_id, developer_id, name, description, value_encrypted, metadata
)
VALUES (
    $1, $2, $3, $4,
    (SELECT encrypt_secret($5::text, $6::text)),
    $7
)
RETURNING *;
"""


@rewrap_exceptions(common_db_exceptions("secret", ["create"]))
@wrap_in_class(
    Secret,
    one=True,
    transform=lambda d: {**d, "id": d["secret_id"], "value": "ENCRYPTED"},
)
@query_metrics("create_secret")
@pg_query
@beartype
async def create_secret(
    *,
    developer_id: UUID,
    name: str,
    value: str,
    secret_id: UUID | None = None,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[str, list]:
    """
    Constructs and executes a SQL query to create a new secret in the database.

    Parameters:
        developer_id (UUID): The unique identifier for the developer creating the secret.
        secret_id (UUID | None): The unique identifier for the secret.
        name (str): The name of the secret.
        value (str): The value of the secret.
        description (str | None): The description of the secret.
        metadata (dict[str, Any] | None): Additional metadata for the secret.

    Returns:
        tuple[str, list]: SQL query and parameters for creating the secret.
    """
    secret_id = secret_id or uuid7()

    return (
        query,
        [
            secret_id,
            developer_id,
            name,
            description,
            value,
            secrets_master_key,
            metadata,
        ],
    )
