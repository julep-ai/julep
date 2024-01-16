from typing import Annotated
from uuid import uuid4
from starlette.status import HTTP_201_CREATED, HTTP_202_ACCEPTED
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Header
from fastapi.responses import JSONResponse
from pydantic import UUID4
from memory_api.clients.cozo import client
from memory_api.models.session.get_session import get_session_query
from memory_api.models.session.create_session import create_session_query
from memory_api.models.session.list_sessions import list_sessions_query
from memory_api.models.session.delete_session import delete_session_query
from memory_api.autogen.openapi_model import (
    CreateSessionRequest,
    UpdateSessionRequest,
    Session,
    ChatInput,
    Suggestion,
    ChatMLMessage,
    ResourceCreatedResponse,
    ResourceUpdatedResponse,
)
from .protocol import Settings
from .session import PlainCompletionSession


router = APIRouter()


@router.get("/sessions/{session_id}", tags=["sessions"])
async def get_session(
    session_id: UUID4, x_developer_id: Annotated[UUID4, Header()]
) -> Session:
    try:
        res = [
            row.to_dict()
            for _, row in client.run(
                get_session_query(developer_id=x_developer_id, session_id=session_id),
            ).iterrows()
        ][0]
        return Session(**res)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )


@router.post("/sessions/", status_code=HTTP_201_CREATED, tags=["sessions"])
async def create_session(
    request: CreateSessionRequest, x_developer_id: Annotated[UUID4, Header()]
) -> ResourceCreatedResponse:
    session_id = uuid4()
    resp = client.run(
        create_session_query(
            session_id=session_id,
            developer_id=x_developer_id,
            agent_id=request.agent_id,
            user_id=request.user_id,
            situation=request.situation,
        ),
    )

    return ResourceCreatedResponse(
        id=resp["session_id"][0],
        created_at=resp["created_at"][0],
    )


@router.get("/sessions/", tags=["sessions"])
async def list_sessions(
    x_developer_id: Annotated[UUID4, Header()], limit: int = 100, offset: int = 0
) -> list[Session]:
    return [
        Session(**row.to_dict())
        for _, row in client.run(
            list_sessions_query(x_developer_id, limit, offset),
        ).iterrows()
    ]


@router.delete(
    "/sessions/{session_id}", status_code=HTTP_202_ACCEPTED, tags=["sessions"]
)
async def delete_session(session_id: UUID4, x_developer_id: Annotated[UUID4, Header()]):
    try:
        client.run(delete_session_query(x_developer_id, session_id))
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )


@router.put("/sessions/{session_id}", tags=["sessions"])
async def update_session(
    session_id: UUID4,
    request: UpdateSessionRequest,
    x_developer_id: Annotated[UUID4, Header()],
) -> ResourceUpdatedResponse:
    try:
        resp = client.update(
            "sessions",
            {
                "developer_id": str(x_developer_id),
                "session_id": str(session_id),
                "situation": request.situation,
            },
        )

        return ResourceUpdatedResponse(
            id=resp["session_id"][0],
            updated_at=resp["updated_at"][0],
        )
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )


@router.get("/sessions/{session_id}/suggestions", tags=["sessions"])
async def get_suggestions(
    session_id: UUID4,
    x_developer_id: Annotated[UUID4, Header()],
    limit: int = 100,
    offset: int = 0,
) -> list[Suggestion]:
    return []


@router.get("/sessions/{session_id}/history", tags=["sessions"])
async def get_history(
    session_id: UUID4,
    x_developer_id: Annotated[UUID4, Header()],
    limit: int = 100,
    offset: int = 0,
) -> list[ChatMLMessage]:
    return []


@router.post("/sessions/{session_id}/chat", tags=["sessions"])
async def session_chat(
    session_id: UUID4,
    request: ChatInput,
    background_tasks: BackgroundTasks,
    x_developer_id: Annotated[UUID4, Header()],
):
    async def run_task(task):
        await task

    session = PlainCompletionSession(
        developer_id=x_developer_id,
        session_id=session_id,
    )
    settings = Settings(
        model="",
        frequency_penalty=request.frequency_penalty,
        length_penalty=request.length_penalty,
        logit_bias=request.logit_bias,
        max_tokens=request.max_tokens,
        presence_penalty=request.presence_penalty,
        repetition_penalty=request.repetition_penalty,
        response_format=request.response_format,
        seed=request.seed,
        stop=request.stop,
        stream=request.stream,
        temperature=request.temperature,
        top_p=request.top_p,
    )
    response, bg_task = await session.run(request.messages, settings)

    background_tasks.add_task(run_task, bg_task)

    return JSONResponse(response)
