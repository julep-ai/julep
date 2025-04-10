"""Create secret endpoint."""

from agents_api.autogen.openapi_model import CreateSecretRequest, Secret

from ...queries.secrets import create_secret as create_secret_query
from .router import router


@router.post("/developers/{developer_id}/secrets", response_model=Secret)
async def create_developer_secret(
    secret: CreateSecretRequest,
) -> Secret:
    """Create a new secret for a developer.

    Args:
        developer_id: ID of the developer creating the secret
        secret: Secret to create

    Returns:
        The created secret

    Raises:
        HTTPException: If a secret with this name already exists (409 Conflict)
    """
    return await create_secret_query(data=secret)


@router.post("/agents/{agent_id}/secrets", response_model=Secret)
async def create_agent_secret(
    secret: CreateSecretRequest,
) -> Secret:
    """Create a new secret for an agent.

    Args:
        agent_id: ID of the agent creating the secret
        secret: Secret to create

    Returns:
        The created secret

    Raises:
        HTTPException: If a secret with this name already exists (409 Conflict)
    """
    return await create_secret_query(data=secret)
