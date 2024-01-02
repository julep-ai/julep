from starlette.status import HTTP_201_CREATED, HTTP_202_ACCEPTED
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import UUID4
from .protocol import (
    CreateSessionRequest,
    UpdateSessionRequest,
    Session,
    ChatRequest,
    Suggestion,
    ChatMessage,
)
from memory_api.clients.cozo import client
from memory_api.models.session.get_session import get_session_query
from memory_api.models.session.create_session import create_session_query
from memory_api.models.session.list_sessions import list_sessions_query
from .session import PlainCompletionSession


router = APIRouter()


@router.get("/sessions/{session_id}", tags=["sessions"])
async def get_session(session_id: UUID4) -> Session:
    try:
        res = [
            row.to_dict()
            for _, row in client.run(
                get_session_query(session_id=session_id),
            ).iterrows()
        ][0]
        return Session(**res)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )


@router.post("/sessions/", status_code=HTTP_201_CREATED, tags=["sessions"])
async def create_session(request: CreateSessionRequest) -> Session:
    client.run(
        create_session_query(
            session_id=request.id,
            agent_id=request.agent_id,
            user_id=request.user_id,
            situation=request.situation,
        ),
    )

    return await get_session(request.id)


@router.get("/sessions/", tags=["sessions"])
async def list_sessions(limit: int = 100, offset: int = 0) -> list[Session]:
    return [
        Session(**row.to_dict())
        for _, row in client.run(
            list_sessions_query(limit, offset),
        ).iterrows()
    ]


@router.delete(
    "/sessions/{session_id}", status_code=HTTP_202_ACCEPTED, tags=["sessions"]
)
async def delete_session(session_id: UUID4):
    try:
        client.rm("sessions", {"session_id": str(session_id)})
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )


@router.put("/sessions/{session_id}", tags=["sessions"])
async def update_session(session_id: UUID4, request: UpdateSessionRequest) -> Session:
    try:
        client.update(
            "sessions",
            {
                "session_id": str(session_id),
                "situation": request.situation,
            },
        )
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return await get_session(session_id)


@router.get("/sessions/{session_id}/suggestions", tags=["sessions"])
async def get_suggestions(
    session_id: UUID4, limit: int = 100, offset: int = 0
) -> list[Suggestion]:
    return []


@router.get("/sessions/{session_id}/history", tags=["sessions"])
async def get_history(
    session_id: UUID4, limit: int = 100, offset: int = 0
) -> list[ChatMessage]:
    return []


@router.post("/sessions/{session_id}/chat", tags=["sessions"])
async def session_chat(
    session_id: UUID4, request: ChatRequest, background_tasks: BackgroundTasks
):
    session = PlainCompletionSession(session_id)
    response, bg_task = await session.run(request.messages, request.settings)

    background_tasks.add_task(bg_task)

    return JSONResponse(response)
