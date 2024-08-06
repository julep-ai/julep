from typing import Annotated
from uuid import UUID

from fastapi import Depends
from pydantic import UUID4
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import (
    CreateOrUpdateSessionRequest,
    ResourceCreatedResponse,
)
from ...dependencies.developer_id import get_developer_id
from ...models.session.create_or_update_session import (
    create_or_update_session as create_session_query,
)
from .router import router


@router.post("/sessions/{session_id}", status_code=HTTP_201_CREATED, tags=["sessions"])
async def create_or_update_session(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    session_id: UUID,
    data: CreateOrUpdateSessionRequest,
) -> ResourceCreatedResponse:
    session = create_session_query(
        developer_id=x_developer_id,
        session_id=session_id,
        data=data,
    )

    return ResourceCreatedResponse(
        id=session.id,
        created_at=session.created_at,
    )
