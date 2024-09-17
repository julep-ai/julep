from typing import Annotated

from fastapi import Depends
from pydantic import UUID4
from starlette.status import HTTP_202_ACCEPTED

from ...autogen.openapi_model import ResourceDeletedResponse
from ...dependencies.developer_id import get_developer_id
from ...models.session.delete_session import delete_session as delete_session_query
from .router import router


@router.delete(
    "/sessions/{session_id}", status_code=HTTP_202_ACCEPTED, tags=["sessions"]
)
async def delete_session(
    session_id: UUID4, x_developer_id: Annotated[UUID4, Depends(get_developer_id)]
) -> ResourceDeletedResponse:
    return delete_session_query(developer_id=x_developer_id, session_id=session_id)
