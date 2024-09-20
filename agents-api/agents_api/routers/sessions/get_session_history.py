from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import History
from ...dependencies.developer_id import get_developer_id
from ...models.entry.get_history import get_history as get_history_query
from .router import router


@router.get("/sessions/{session_id}/history", tags=["sessions"])
async def get_session_history(
    session_id: UUID, x_developer_id: Annotated[UUID, Depends(get_developer_id)]
) -> History:
    return get_history_query(developer_id=x_developer_id, session_id=session_id)
