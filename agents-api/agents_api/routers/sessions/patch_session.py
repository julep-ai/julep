from typing import Annotated

from fastapi import Depends, HTTPException
from pydantic import UUID4
from starlette.status import HTTP_404_NOT_FOUND

from ...autogen.openapi_model import (
    PatchSessionRequest,
    ResourceUpdatedResponse,
)
from ...common.exceptions.sessions import SessionNotFoundError
from ...dependencies.developer_id import get_developer_id
from ...models.session.patch_session import patch_session as patch_session_query
from .router import router


@router.patch("/sessions/{session_id}", tags=["sessions"])
async def patch_session(
    session_id: UUID4,
    request: PatchSessionRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceUpdatedResponse:
    try:
        resp = patch_session_query(
            session_id=session_id,
            developer_id=x_developer_id,
            situation=request.situation,
            metadata=request.metadata,
            token_budget=request.token_budget,
            context_overflow=request.context_overflow,
        )

        return ResourceUpdatedResponse(
            id=resp["session_id"][0],
            updated_at=resp["updated_at"][0][0],
        )
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=str(e),
        )
