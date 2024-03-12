from datetime import datetime
from typing import Annotated
from uuid import uuid4


from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
from pydantic import BaseModel
from pydantic import UUID4
from starlette.status import HTTP_201_CREATED, HTTP_202_ACCEPTED

from agents_api.clients.cozo import client
from agents_api.models.session.get_session import get_session_query
from agents_api.models.session.create_session import create_session_query
from agents_api.models.session.list_sessions import list_sessions_query
from agents_api.models.session.delete_session import delete_session_query
from agents_api.dependencies.developer_id import get_developer_id
from agents_api.models.entry.get_entries import get_entries_query
from agents_api.models.session.update_session import update_session_query
from agents_api.autogen.openapi_model import (
    CreateSessionRequest,
    UpdateSessionRequest,
    Session,
    ChatInput,
    Suggestion,
    ChatMLMessage,
    ResourceCreatedResponse,
    ResourceDeletedResponse,
    ResourceUpdatedResponse,
    ChatResponse,
    FinishReason,
    CompletionUsage,
)
from .protocol import Settings
from .session import RecursiveSummarizationSession


router = APIRouter()


class SessionList(BaseModel):
    items: list[Session]


class SuggestionList(BaseModel):
    items: list[Suggestion]


class ChatMLMessageList(BaseModel):
    items: list[ChatMLMessage]


@router.get("/sessions/{session_id}", tags=["sessions"])
async def get_session(
    session_id: UUID4, x_developer_id: Annotated[UUID4, Depends(get_developer_id)]
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


@router.post("/sessions", status_code=HTTP_201_CREATED, tags=["sessions"])
async def create_session(
    request: CreateSessionRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    session_id = uuid4()
    resp = client.run(
        create_session_query(
            session_id=session_id,
            developer_id=x_developer_id,
            agent_id=request.agent_id,
            user_id=request.user_id,
            situation=request.situation,
            metadata=request.metadata or {},
        ),
    )

    return ResourceCreatedResponse(
        id=resp["session_id"][0],
        created_at=resp["created_at"][0],
    )


@router.get("/sessions", tags=["sessions"])
async def list_sessions(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    limit: int = 100,
    offset: int = 0,
) -> SessionList:
    return SessionList(
        items=[
            Session(**row.to_dict())
            for _, row in client.run(
                list_sessions_query(x_developer_id, limit, offset),
            ).iterrows()
        ]
    )


@router.delete(
    "/sessions/{session_id}", status_code=HTTP_202_ACCEPTED, tags=["sessions"]
)
async def delete_session(
    session_id: UUID4, x_developer_id: Annotated[UUID4, Depends(get_developer_id)]
) -> ResourceDeletedResponse:
    try:
        client.run(delete_session_query(x_developer_id, session_id))
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return ResourceDeletedResponse(id=session_id, deleted_at=datetime.now())


@router.put("/sessions/{session_id}", tags=["sessions"])
async def update_session(
    session_id: UUID4,
    request: UpdateSessionRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceUpdatedResponse:
    try:
        resp = client.run(
            update_session_query(
                session_id=session_id,
                developer_id=x_developer_id,
                situation=request.situation,
                metadata=request.metadata,
            )
        )

        return ResourceUpdatedResponse(
            id=resp["session_id"][0],
            updated_at=resp["updated_at"][0][0],
        )
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )


@router.get("/sessions/{session_id}/suggestions", tags=["sessions"])
async def get_suggestions(
    session_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    limit: int = 100,
    offset: int = 0,
) -> SuggestionList:
    return SuggestionList(items=[])


@router.get("/sessions/{session_id}/history", tags=["sessions"])
async def get_history(
    session_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    limit: int = 100,
    offset: int = 0,
) -> ChatMLMessageList:
    try:
        items = []
        for _, row in client.run(
            get_entries_query(session_id=session_id, limit=limit, offset=offset),
        ).iterrows():
            row_dict = row.to_dict()
            row_dict["id"] = row_dict["entry_id"]
            items.append(ChatMLMessage(**row_dict))

        return ChatMLMessageList(
            items=items,
        )
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )


@router.post("/sessions/{session_id}/chat", tags=["sessions"])
async def session_chat(
    session_id: UUID4,
    request: ChatInput,
    background_tasks: BackgroundTasks,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ChatResponse:
    session = RecursiveSummarizationSession(
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
        remember=request.remember,
        recall=request.recall,
        min_p=request.min_p,
        preset=request.preset,
    )
    response, new_entry, bg_task = await session.run(request.messages, settings)

    jobs = None
    if bg_task:
        job_id = uuid4()
        jobs = {job_id}
        background_tasks.add_task(bg_task, session_id, job_id)

    resp = [ChatMLMessage(**new_entry.model_dump())]

    return ChatResponse(
        id=uuid4(),
        finish_reason=FinishReason[response.choices[0].finish_reason],
        response=[resp],
        usage=CompletionUsage(**response.usage.model_dump()),
        jobs=jobs,
    )
