from typing import Annotated

from fastapi import Depends
from pydantic import UUID4

from ...autogen.openapi_model import History
from ...dependencies.developer_id import get_developer_id
from ...models.entry.get_history import get_history as get_history_query
from .router import router


@router.get("/sessions/{session_id}/history", tags=["sessions"])
async def get_session_history(
    session_id: UUID4, x_developer_id: Annotated[UUID4, Depends(get_developer_id)]
) -> History:
    return get_history_query(developer_id=x_developer_id, session_id=session_id)
