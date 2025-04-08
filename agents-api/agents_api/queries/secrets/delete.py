"""Query functions for deleting secrets."""

from uuid import UUID

from asyncpg import Connection
from beartype import beartype
from ...autogen.openapi_model import Secret, ResourceDeletedResponse
from ...common.utils.db_exceptions import common_db_exceptions
from ...common.utils.datetime import utcnow
from ...metrics.counters import query_metrics
from ..utils import pg_query, wrap_in_class, rewrap_exceptions


query = """
    DELETE FROM secrets
    WHERE secret_id = $1 AND developer_id = $2
    RETURNING
        secret_id, developer_id, name, description,
        encryption_key_id, created_at, updated_at, metadata
"""


@rewrap_exceptions(common_db_exceptions("secret", ["delete"]))
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {**d, "id": d["secret_id"], "deleted_at": utcnow()},
)
@pg_query
@beartype
async def delete_secret(conn: Connection, secret_id: UUID, developer_id: UUID) -> tuple[str, list]:
    """Delete a secret.

    Args:
        conn: Database connection
        secret_id: ID of the secret to delete
        developer_id: ID of the developer who owns the secret

    Returns:
        Deleted secret

    Raises:
        NotFoundError: If the secret does not exist
    """

    return []
