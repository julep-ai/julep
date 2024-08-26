from typing import Annotated

from fastapi import Depends
from pydantic import UUID4

from ...autogen.openapi_model import (
    PatchSessionRequest,
    ResourceUpdatedResponse,
)
from ...dependencies.developer_id import get_developer_id
from ...models.session.patch_session import patch_session as patch_session_query
from .router import router


@router.patch("/sessions/{session_id}", tags=["sessions"])
async def patch_session(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    session_id: UUID4,
    data: PatchSessionRequest,
) -> ResourceUpdatedResponse:
    return patch_session_query(
        developer_id=x_developer_id,
        session_id=session_id,
        data=data,
    )
