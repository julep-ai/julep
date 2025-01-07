from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import CreateDocRequest, Doc, ResourceCreatedResponse
from ...dependencies.developer_id import get_developer_id
from ...queries.docs.create_doc import create_doc as create_doc_query
from .router import router


@router.post("/users/{user_id}/docs", status_code=HTTP_201_CREATED, tags=["docs"])
async def create_user_doc(
    user_id: UUID,
    data: CreateDocRequest,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    """
    Creates a new document for a user.

    Parameters:
        user_id (UUID): The unique identifier of the user associated with the document.
        data (CreateDocRequest): The data to create the document with.
        x_developer_id (UUID): The unique identifier of the developer associated with the document.

    Returns:
        ResourceCreatedResponse: The created document.
    """

    doc: Doc = await create_doc_query(
        developer_id=x_developer_id,
        owner_type="user",
        owner_id=user_id,
        data=data,
    )

    return ResourceCreatedResponse(id=doc.id, created_at=doc.created_at, jobs=[])


@router.post("/agents/{agent_id}/docs", status_code=HTTP_201_CREATED, tags=["docs"])
async def create_agent_doc(
    agent_id: UUID,
    data: CreateDocRequest,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    doc: Doc = await create_doc_query(
        developer_id=x_developer_id,
        owner_type="agent",
        owner_id=agent_id,
        data=data,
    )

    return ResourceCreatedResponse(id=doc.id, created_at=doc.created_at, jobs=[])
