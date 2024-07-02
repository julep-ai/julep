from typing import Annotated

from fastapi import Depends, HTTPException
from pydantic import UUID4

from ...dependencies.developer_id import get_developer_id
from ...models.session.get_session import get_session_query
from ...autogen.openapi_model import Session

from .router import router


@router.get("/sessions/{session_id}", tags=["sessions"])
async def get_session(
    session_id: UUID4, x_developer_id: Annotated[UUID4, Depends(get_developer_id)]
) -> Session:
    try:
        res = [
            row.to_dict()
            for _, row in get_session_query(
                developer_id=x_developer_id, session_id=session_id
            ).iterrows()
        ][0]
        return Session(**res)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )
