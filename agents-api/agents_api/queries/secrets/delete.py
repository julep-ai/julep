"""Query functions for deleting secrets."""

from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import ResourceDeletedResponse
from ...common.utils.datetime import utcnow
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

query = """
    DELETE FROM secrets
    WHERE secret_id = $1
    AND (
        ($2 IS NOT NULL AND developer_id = $2) OR
        ($3 IS NOT NULL AND agent_id = $3)
    )
    RETURNING *;
"""


@rewrap_exceptions(common_db_exceptions("secret", ["delete"]))
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {
        "id": d["secret_id"],
        "deleted_at": utcnow(),
    },
)
@pg_query
@beartype
async def delete_secret(
    *, secret_id: UUID, developer_id: UUID | None = None, agent_id: UUID | None = None
) -> tuple[str, list]:
    """Delete a secret.

    Args:
        secret_id: ID of the secret to delete
        developer_id: ID of the developer who owns the secret (optional)
        agent_id: ID of the agent associated with the secret (optional)

    Returns:
        ResourceDeletedResponse: Information about the deleted secret

    Raises:
        NotFoundError: If the secret does not exist
    """

    return (
        query,
        [
            secret_id,
            developer_id,
            agent_id,
        ],
    )
