from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import (
    ResourceUpdatedResponse,
    UpdateSessionRequest,
)
from ...dependencies.developer_id import get_developer_id
from ...queries.sessions.update_session import update_session as update_session_query
from .router import router


@router.put("/sessions/{session_id}", tags=["sessions"])
async def update_session(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    session_id: UUID,
    data: UpdateSessionRequest,
) -> ResourceUpdatedResponse:
    return await update_session_query(
        developer_id=x_developer_id,
        session_id=session_id,
        data=data,
    )
