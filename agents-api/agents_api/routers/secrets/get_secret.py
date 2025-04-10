"""Get secret endpoints."""

from uuid import UUID

from agents_api.autogen.openapi_model import GetSecretRequest, Secret

from ...queries.secrets import get_secret as get_secret_query
from .router import router


@router.get("/developers/{developer_id}/secret", response_model=Secret)
async def get_developer_secret(
    developer_id: UUID,
    data: GetSecretRequest,
) -> Secret:
    """Get a secret by name.

    Args:
        developer_id: ID of the developer who owns the secret
        data: Request containing the secret name to retrieve

    Returns:
        The secret with its decrypted value

    Raises:
        HTTPException: If the secret doesn't exist
    """
    return await get_secret_query(developer_id=developer_id, data=data)


@router.get("/agents/{agent_id}/secret", response_model=Secret)
async def get_agent_secret(
    agent_id: UUID,
    data: GetSecretRequest,
) -> Secret:
    """Get a secret by name.

    Args:
        agent_id: ID of the agent associated with the secret
        data: Request containing the secret name to retrieve

    Returns:
        The secret with its decrypted value

    Raises:
        HTTPException: If the secret doesn't exist
    """
    return await get_secret_query(agent_id=agent_id, data=data)
