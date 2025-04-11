"""Delete secret endpoint."""

from uuid import UUID

from agents_api.autogen.openapi_model import ResourceDeletedResponse

from ...queries.secrets import delete_secret as delete_secret_query
from .router import router


@router.delete(
    "/developers/{developer_id}/secrets/{secret_id}", response_model=ResourceDeletedResponse
)
async def delete_developer_secret(
    developer_id: UUID,
    secret_id: UUID,
) -> ResourceDeletedResponse:
    """Delete a secret.

    Args:
        secret_id: ID of the secret to delete
        conn: Database connection
        developer_id: ID of the developer who owns the secret

    Returns:
        The deleted secret

    Raises:
        HTTPException: If the secret doesn't exist
    """
    return await delete_secret_query(secret_id=secret_id, developer_id=developer_id)


@router.delete("/agents/{agent_id}/secrets/{secret_id}", response_model=ResourceDeletedResponse)
async def delete_agent_secret(
    agent_id: UUID,
    secret_id: UUID,
) -> ResourceDeletedResponse:
    """Delete a secret.

    Args:
        secret_id: ID of the secret to delete
        conn: Database connection
        developer_id: ID of the developer who owns the secret

    Returns:
        The deleted secret

    Raises:
        HTTPException: If the secret doesn't exist
    """
    return await delete_secret_query(secret_id=secret_id, agent_id=agent_id)
