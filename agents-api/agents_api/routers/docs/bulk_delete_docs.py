from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette.status import HTTP_202_ACCEPTED

from ...autogen.openapi_model import (
    BulkDeleteDocsRequest,
    ListResponse,
    ResourceDeletedResponse,
)
from ...dependencies.developer_id import get_developer_id
from ...queries.docs.bulk_delete_docs import bulk_delete_docs as bulk_delete_docs_query
from .router import router


@router.delete(
    "/agents/{agent_id}/docs",
    status_code=HTTP_202_ACCEPTED,
    tags=["docs"],
    description="Bulk delete documents owned by an agent based on metadata filter",
)
async def bulk_delete_agent_docs(
    agent_id: UUID,
    data: BulkDeleteDocsRequest,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> ListResponse[ResourceDeletedResponse]:
    deleted_docs = await bulk_delete_docs_query(
        developer_id=x_developer_id,
        owner_id=agent_id,
        owner_type="agent",
        data=data,
    )

    return ListResponse[ResourceDeletedResponse](items=deleted_docs)


@router.delete(
    "/users/{user_id}/docs",
    status_code=HTTP_202_ACCEPTED,
    tags=["docs"],
    description="Bulk delete documents owned by a user based on metadata filter",
)
async def bulk_delete_user_docs(
    user_id: UUID,
    data: BulkDeleteDocsRequest,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> ListResponse[ResourceDeletedResponse]:
    deleted_docs = await bulk_delete_docs_query(
        developer_id=x_developer_id,
        owner_id=user_id,
        owner_type="user",
        data=data,
    )

    return ListResponse[ResourceDeletedResponse](items=deleted_docs)
