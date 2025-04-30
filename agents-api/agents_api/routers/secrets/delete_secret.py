"""Delete secret endpoint."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette.status import HTTP_202_ACCEPTED

from agents_api.autogen.openapi_model import ResourceDeletedResponse

from ...dependencies.developer_id import get_developer_id
from ...queries.secrets import delete_secret as delete_secret_query
from .router import router


@router.delete(
    "/secrets/{secret_id}",
    response_model=ResourceDeletedResponse,
    status_code=HTTP_202_ACCEPTED,
    tags=["secrets"],
)
async def delete_developer_secret(
    *,
    secret_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
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
    return await delete_secret_query(secret_id=secret_id, developer_id=x_developer_id)


# @router.delete("/agents/{agent_id}/secrets/{secret_id}", response_model=ResourceDeletedResponse)
# async def delete_agent_secret(
#     agent_id: UUID,
#     secret_id: UUID,
# ) -> ResourceDeletedResponse:
#     """Delete a secret.

#     Args:
#         secret_id: ID of the secret to delete
#         conn: Database connection
#         developer_id: ID of the developer who owns the secret

#     Returns:
#         The deleted secret

#     Raises:
#         HTTPException: If the secret doesn't exist
#     """
#     return await delete_secret_query(secret_id=secret_id, agent_id=agent_id)
