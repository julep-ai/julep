import openai
from operator import itemgetter
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import UUID4
from .protocol import Session, ChatRequest
from memory_api.clients.cozo import client
from memory_api.common.db.entries import add_entries
from memory_api.common.protocol.entries import Entry
from memory_api.env import summarization_ratio_threshold
from memory_api.clients.worker.types import MemoryManagementTaskArgs, ChatML
from memory_api.clients.worker.worker import add_summarization_task
from .queries import context_window_query


router = APIRouter()


@router.post("/sessions/")
async def create_session(request: Session) -> Session:
    query = f"""
        ?[session_id, character_id, user_id, situation, metadata] <- [[
        to_uuid("{request.id}"),
        to_uuid("{request.character_id}"),
        to_uuid("{request.user_id}"),
        "{request.situation}",
        {request.metadata},
    ]]

    :put sessions {{
        character_id,
        user_id,
        session_id,
        situation,
        metadata,
    }}
    """

    client.run(query)

    return await get_sessions(request.id)


@router.get("/sessions/{session_id}")
async def get_sessions(session_id: UUID4) -> Session:
    query = f"""
        input[session_id] <- [[
        to_uuid("{session_id}"),
    ]]

    ?[
        character_id,
        user_id,
        session_id,
        updated_at,
        situation,
        summary,
        metadata,
        created_at,
    ] := input[session_id],
        *sessions{{
            character_id,
            user_id,
            session_id,
            situation,
            summary,
            metadata,
            updated_at: validity,
            created_at,
            @ "NOW"
        }}, updated_at = to_int(validity)
    """

    try:
        res = [row.to_dict() for _, row in client.run(query).iterrows()][0]
        return Session(**res)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )


@router.post("/sessions/chat")
async def session_chat(request: ChatRequest):
    entries: list[Entry] = []
    for m in request.params.messages:
        m.session_id = request.session_id
        entries.append(m)
    
    add_entries(entries)

    resp = client.run(context_window_query.replace("{session_id}", request.session_id))

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
                session_id=request.session_id, 
                model=model_data["model_name"], 
                dialog=[
                    ChatML(**{**e, "session_id": request.session_id}) 
                    for e in entries
                ],
            ),
        )

    # generate response
    default_settings = model_data["default_settings"]
    messages = [
        {
            "role": e.get("role"), 
            "name": e.get("name"), 
            "content": e.get("content"),
        } 
        for e in entries
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
                session_id=request.session_id, 
                role="assistant", 
                name=character_data["name"], 
                content=response["choices"][0]["text"], 
                token_count=response["usage"]["total_tokens"],
            )
        ]
    )

    return JSONResponse(response)
