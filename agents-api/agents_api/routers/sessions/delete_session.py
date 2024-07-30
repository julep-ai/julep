from typing import Annotated

from fastapi import Depends, HTTPException
from pydantic import UUID4
from starlette.status import HTTP_202_ACCEPTED, HTTP_404_NOT_FOUND

from ...autogen.openapi_model import ResourceDeletedResponse
from ...common.exceptions.sessions import SessionNotFoundError
from ...common.utils.datetime import utcnow
from ...dependencies.developer_id import get_developer_id
from ...models.session.delete_session import delete_session as delete_session_query
from .router import router


@router.delete(
    "/sessions/{session_id}", status_code=HTTP_202_ACCEPTED, tags=["sessions"]
)
async def delete_session(
    session_id: UUID4, x_developer_id: Annotated[UUID4, Depends(get_developer_id)]
) -> ResourceDeletedResponse:
    try:
        delete_session_query(x_developer_id, session_id)
    except SessionNotFoundError as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))

    return ResourceDeletedResponse(id=session_id, deleted_at=utcnow())
