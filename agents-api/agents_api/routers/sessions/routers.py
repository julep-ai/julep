import json
from json import JSONDecodeError
from typing import Annotated
from uuid import uuid4


from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
import pandas as pd
from pydantic import BaseModel
from pydantic import UUID4
from starlette.status import HTTP_201_CREATED, HTTP_202_ACCEPTED

from pycozo.client import QueryException
from agents_api.common.exceptions.sessions import SessionNotFoundError
from agents_api.common.utils.datetime import utcnow
from agents_api.models.session.get_session import get_session_query
from agents_api.models.session.create_session import create_session_query
from agents_api.models.session.list_sessions import list_sessions_query
from agents_api.models.session.delete_session import delete_session_query
from agents_api.dependencies.developer_id import get_developer_id
from agents_api.models.entry.get_entries import get_entries_query
from agents_api.models.entry.delete_entries import delete_entries_query
from agents_api.models.session.update_session import update_session_query
from agents_api.models.session.patch_session import patch_session_query
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
    Stop,
    PatchSessionRequest,
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
            for _, row in get_session_query(
                developer_id=x_developer_id, session_id=session_id
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


@router.get("/sessions", tags=["sessions"])
async def list_sessions(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    limit: int = 100,
    offset: int = 0,
    metadata_filter: str = "{}",
) -> SessionList:
    try:
        metadata_filter = json.loads(metadata_filter)
    except JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="metadata_filter is not a valid JSON",
        )

    query_results = list_sessions_query(
        x_developer_id, limit, offset, metadata_filter=metadata_filter
    )

    return SessionList(
        items=[Session(**row.to_dict()) for _, row in query_results.iterrows()]
    )


@router.delete(
    "/sessions/{session_id}", status_code=HTTP_202_ACCEPTED, tags=["sessions"]
)
async def delete_session(
    session_id: UUID4, x_developer_id: Annotated[UUID4, Depends(get_developer_id)]
) -> ResourceDeletedResponse:
    try:
        delete_session_query(x_developer_id, session_id)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return ResourceDeletedResponse(id=session_id, deleted_at=utcnow())


@router.put("/sessions/{session_id}", tags=["sessions"])
async def update_session(
    session_id: UUID4,
    request: UpdateSessionRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceUpdatedResponse:
    try:
        resp = update_session_query(
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    except QueryException as e:
        # the code is not so informative now, but it may be a good solution in the future
        if e.code in ("transact::assertion_failure", "eval::assert_some_failure"):
            raise SessionNotFoundError(x_developer_id, session_id)

        raise


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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    except QueryException as e:
        # the code is not so informative now, but it may be a good solution in the future
        if e.code in ("transact::assertion_failure", "eval::assert_some_failure"):
            raise SessionNotFoundError(x_developer_id, session_id)

        raise


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
        for _, row in get_entries_query(
            session_id=session_id, limit=limit, offset=offset
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


@router.delete(
    "/sessions/{session_id}/history", status_code=HTTP_202_ACCEPTED, tags=["sessions"]
)
async def delete_history(
    session_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceDeletedResponse:
    try:
        delete_entries_query(session_id=session_id)
    except QueryException as e:
        if e.code == "transact::assertion_failure":
            raise SessionNotFoundError(
                developer_id=x_developer_id, session_id=session_id
            )

        raise

    return ResourceDeletedResponse(id=session_id, deleted_at=utcnow())


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

    stop = request.stop
    if isinstance(request.stop, Stop):
        stop = request.stop.root

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
        stop=stop,
        stream=request.stream,
        temperature=request.temperature,
        top_p=request.top_p,
        remember=request.remember,
        recall=request.recall,
        min_p=request.min_p,
        preset=request.preset,
    )
    response, new_entry, bg_task, doc_ids = await session.run(
        request.messages, settings
    )

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
        doc_ids=doc_ids,
    )
