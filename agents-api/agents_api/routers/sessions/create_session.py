from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, UUID4
from typing import Annotated
from uuid import uuid4

from agents_api.dependencies.developer_id import get_developer_id
from agents_api.models.session.create_session import create_session_query
from agents_api.autogen.openapi_model import CreateSessionRequest, ResourceCreatedResponse

router = APIRouter()

@router.post("/sessions", status_code=HTTP_201_CREATED, tags=["sessions"])
async def create_session(
    request: CreateSessionRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    session_id = uuid4()
    resp: pd.DataFrame = create_session_query(
        session_id=session_id,
        developer_id=x_developer_id,
        agent_id=request.agent_id,
        user_id=request.user_id,
        situation=request.situation,
        metadata=request.metadata or {},
        render_templates=request.render_templates or False,
        token_budget=request.token_budget,
        context_overflow=request.context_overflow,
    )

    return ResourceCreatedResponse(
        id=resp["session_id"][0],
        created_at=resp["created_at"][0],
    )
