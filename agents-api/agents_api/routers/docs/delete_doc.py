from typing import Annotated

from fastapi import Depends
from uuid import UUID
from starlette.status import HTTP_202_ACCEPTED

from ...autogen.openapi_model import ResourceDeletedResponse
from ...dependencies.developer_id import get_developer_id
from ...models.docs.delete_doc import delete_doc as delete_doc_query
from .router import router


@router.delete(
    "/agents/{agent_id}/docs/{doc_id}", status_code=HTTP_202_ACCEPTED, tags=["docs"]
)
async def delete_agent_doc(
    doc_id: UUID,
    agent_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> ResourceDeletedResponse:
    return delete_doc_query(
        developer_id=x_developer_id,
        owner_id=agent_id,
        owner_type="agent",
        doc_id=doc_id,
    )


@router.delete(
    "/users/{user_id}/docs/{doc_id}", status_code=HTTP_202_ACCEPTED, tags=["docs"]
)
async def delete_user_doc(
    doc_id: UUID,
    user_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> ResourceDeletedResponse:
    return delete_doc_query(
        developer_id=x_developer_id,
        owner_id=user_id,
        owner_type="user",
        doc_id=doc_id,
    )
