import uuid
import openai
from operator import itemgetter
from starlette.status import HTTP_201_CREATED, HTTP_202_ACCEPTED
from fastapi import APIRouter, HTTPException, status
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
from memory_api.common.db.entries import add_entries
from memory_api.common.protocol.entries import Entry
from memory_api.env import summarization_ratio_threshold
from memory_api.clients.worker.types import MemoryManagementTaskArgs, ChatML
from memory_api.clients.worker.worker import add_summarization_task
from memory_api.models.session.get_session import get_session_query
from memory_api.models.session.create_session import create_session_query
from memory_api.models.session.list_sessions import list_sessions_query
from memory_api.models.session.context_window import context_window_query_beliefs


models_map = {
    "samantha-1-alpha": "julep-ai/samantha-1-alpha",
}


router = APIRouter()


@router.get("/sessions/{session_id}")
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


@router.post("/sessions/", status_code=HTTP_201_CREATED)
async def create_session(request: CreateSessionRequest) -> Session:
    client.run(
        create_session_query(
            id=request.id,
            agent_id=request.agent_id,
            user_id=request.user_id,
            situation=request.situation,
        ),
    )

    return await get_session(request.id)


@router.get("/sessions/")
async def list_sessions(limit: int = 100, offset: int = 0) -> list[Session]:
    return [
        Session(**row.to_dict())
        for _, row in client.run(
            list_sessions_query(limit, offset),
        ).iterrows()
    ]


@router.delete("/sessions/{session_id}", status_code=HTTP_202_ACCEPTED)
async def delete_session(session_id: UUID4):
    try:
        client.rm("sessions", {"session_id": session_id})
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )


@router.put("/sessions/{session_id}")
async def update_session(session_id: UUID4, request: UpdateSessionRequest) -> Session:
    client.update(
        "sessions",
        {
            "session_id": session_id,
            "situation": request.situation,
        },
    )

    return await get_session(session_id)


@router.get("/sessions/{session_id}/suggestions")
async def get_suggestions(
    session_id: UUID4, limit: int = 100, offset: int = 0
) -> list[Suggestion]:
    pass


@router.get("/sessions/{session_id}/history")
async def get_history(
    session_id: UUID4, limit: int = 100, offset: int = 0
) -> list[ChatMessage]:
    pass


@router.post("/sessions/{session_id}/chat")
async def session_chat(session_id: UUID4, request: ChatRequest):
    entries: list[Entry] = []
    for m in request.params.messages:
        m.session_id = session_id
        entries.append(m)

    add_entries(entries)

    resp = client.run(context_window_query_beliefs.format(session_id=session_id))

    try:
        model_data = resp["model_data"][0]
        character_data = resp["character_data"][0]
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character or model data not found",
        )

    entries = sorted(resp["entries"][0], key=itemgetter("timestamp"))
    summarization_threshold = model_data["max_length"] * summarization_ratio_threshold

    if resp["total_tokens"][0] >= summarization_threshold:
        await add_summarization_task(
            MemoryManagementTaskArgs(
                session_id=session_id,
                model=models_map.get(
                    model_data["model_name"], model_data["model_name"]
                ),
                dialog=[
                    ChatML(
                        **{
                            **e,
                            "session_id": session_id,
                            "entry_id": uuid.UUID(bytes=bytes(e.get("entry_id"))),
                        },
                    )
                    for e in entries
                    if e.get("role") != "system"
                ],
            ),
        )

    # generate response
    default_settings = model_data["default_settings"]
    messages = [
        {
            "role": e.get("role"),
            "name": e.get("name"),
            "content": e["content"]
            if not isinstance(e["content"], list)
            else "\n".join(e["content"]),
        }
        for e in entries
        if e.get("content")
    ]

    response = openai.ChatCompletion.create(
        model=model_data["model_name"],
        messages=messages,
        max_tokens=default_settings["max_tokens"],
        temperature=default_settings["temperature"],
        repetition_penalty=default_settings["repetition_penalty"],
        frequency_penalty=default_settings["frequency_penalty"],
    )

    # add response as an entry
    add_entries(
        [
            Entry(
                session_id=session_id,
                role="assistant",
                name=character_data["name"],
                content=response["choices"][0]["text"],
                token_count=response["usage"]["total_tokens"],
            )
        ]
    )

    return JSONResponse(response)
