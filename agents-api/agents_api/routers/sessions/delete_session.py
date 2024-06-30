from fastapi import APIRouter, Depends, HTTPException
from pydantic import UUID4
from starlette.status import HTTP_202_ACCEPTED

from agents_api.dependencies.developer_id import get_developer_id
from agents_api.models.session.delete_session import delete_session_query
from agents_api.common.exceptions.sessions import SessionNotFoundError
from agents_api.autogen.openapi_model import ResourceDeletedResponse
from agents_api.common.utils.datetime import utcnow

router = APIRouter()

@router.delete("/sessions/{session_id}", status_code=HTTP_202_ACCEPTED, tags=["sessions"])
async def delete_session(
    session_id: UUID4, x_developer_id: Annotated[UUID4, Depends(get_developer_id)]
) -> ResourceDeletedResponse:
    try:
        delete_session_query(x_developer_id, session_id)
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    return ResourceDeletedResponse(id=session_id, deleted_at=utcnow())
