from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import PatchSessionRequest, Session
from ...dependencies.developer_id import get_developer_id
from ...queries.sessions.patch_session import patch_session as patch_session_query
from .router import router


@router.patch("/sessions/{session_id}", tags=["sessions"])
async def patch_session(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    session_id: UUID,
    data: PatchSessionRequest,
) -> Session:
    return await patch_session_query(
        developer_id=x_developer_id,
        session_id=session_id,
        data=data,
    )
