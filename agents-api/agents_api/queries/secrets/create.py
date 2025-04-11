"""Query functions for creating secrets."""

from uuid import UUID

from beartype import beartype
from uuid_extensions import uuid7

from agents_api.autogen.openapi_model import CreateSecretRequest, Secret

from ...common.utils.db_exceptions import common_db_exceptions
from ...env import secrets_master_key
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

query = """
INSERT INTO secrets (
    id, developer_id, agent_id, name, description, value_encrypted, metadata
)
VALUES (
    $1, $2, $3, $4, $5, encrypt_secret($6, $7), $8
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
    *,
    secret_id: UUID | None = None,
    data: CreateSecretRequest,
) -> tuple[str, list]:
    """
    Constructs and executes a SQL query to create a new secret in the database.

    Parameters:
        developer_id (UUID): The unique identifier for the developer creating the secret.
        agent_id (UUID): The unique identifier for the agent creating the secret.
        secret_id (UUID | None): The unique identifier for the secret.
        data (CreateSecretRequest): The data for the new secret.

    Returns:
        tuple[str, list]: SQL query and parameters for creating the secret.
    """
    secret_id = secret_id or uuid7()

    return (
        query,
        [
            secret_id,
            data.developer_id,
            data.agent_id,
            data.name,
            data.description,
            data.value,
            secrets_master_key,
            data.metadata,
        ],
    )
