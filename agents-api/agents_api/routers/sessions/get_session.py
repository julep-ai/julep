from typing import Annotated

from fastapi import Depends
from pydantic import UUID4

from ...autogen.openapi_model import Session
from ...dependencies.developer_id import get_developer_id
from ...models.session.get_session import get_session as get_session_query
from .router import router


@router.get("/sessions/{session_id}", tags=["sessions"])
async def get_session(
    session_id: UUID4, x_developer_id: Annotated[UUID4, Depends(get_developer_id)]
) -> Session:
    return get_session_query(developer_id=x_developer_id, session_id=session_id)
