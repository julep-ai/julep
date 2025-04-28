"""Create secret endpoint."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends

from agents_api.autogen.openapi_model import CreateSecretRequest, Secret

from ...dependencies.developer_id import get_developer_id
from ...queries.secrets import create_secret as create_secret_query
from .router import router


@router.post("/secrets", response_model=Secret)
async def create_developer_secret(
    *,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
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
    return await create_secret_query(
        developer_id=x_developer_id,
        name=secret.name,
        description=secret.description,
        value=secret.value,
        metadata=secret.metadata,
    )


# @router.post("/agents/{agent_id}/secrets", response_model=Secret)
# async def create_agent_secret(
#     agent_id: UUID,
#     secret: CreateSecretRequest,
# ) -> Secret:
#     """Create a new secret for an agent.

#     Args:
#         agent_id: ID of the agent creating the secret
#         secret: Secret to create

#     Returns:
#         The created secret

#     Raises:
#         HTTPException: If a secret with this name already exists (409 Conflict)
#     """
#     return await create_secret_query(
#         agent_id=agent_id,
#         name=secret.name,
#         description=secret.description,
#         value=secret.value,
#         metadata=secret.metadata,
#     )
