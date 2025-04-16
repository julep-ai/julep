"""Update secret endpoint."""

from uuid import UUID

from ...autogen.openapi_model import Secret, UpdateSecretRequest
from ...queries.secrets import update_secret as update_secret_query
from .router import router


@router.put("/developers/{developer_id}/secrets/{secret_id}", response_model=Secret)
async def update_developer_secret(
    developer_id: UUID,
    secret_id: UUID,
    data: UpdateSecretRequest,
) -> Secret:
    """Update a developer secret.

    Args:
        developer_id: ID of the developer who owns the secret
        secret_id: ID of the secret to update
        data: New secret data

    Returns:
        The updated secret

    Raises:
        HTTPException: If the secret doesn't exist or doesn't belong to the developer
    """
    return await update_secret_query(
        secret_id=secret_id,
        developer_id=developer_id,
        name=data.name,
        description=data.description,
        metadata=data.metadata,
        value=data.value,
    )


@router.put("/agents/{agent_id}/secrets/{secret_id}", response_model=Secret)
async def update_agent_secret(
    agent_id: UUID,
    secret_id: UUID,
    data: UpdateSecretRequest,
) -> Secret:
    """Update an agent secret.

    Args:
        agent_id: ID of the agent who owns the secret
        secret_id: ID of the secret to update
        data: New secret data

    Returns:
        The updated secret

    Raises:
        HTTPException: If the secret doesn't exist or doesn't belong to the agent
    """
    return await update_secret_query(
        secret_id=secret_id,
        agent_id=agent_id,
        name=data.name,
        description=data.description,
        metadata=data.metadata,
        value=data.value,
    )
