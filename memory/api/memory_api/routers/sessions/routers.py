import openai
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import UUID4
from .protocol import Session, ChatRequest
from memory_api.clients.cozo import client
from memory_api.clients.openai import completion
from memory_api.common.db.entries import add_entries
from memory_api.common.protocol.entries import Entry
from .protocol import SessionsRequest
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


@router.get("/sessions/")
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
        session_entries: list[Entry] = [
            Entry(**{**e, "session_id": request.session_id}) 
            for e in resp["entries"][0]
        ]
    except (IndexError, KeyError):
        session_entries = []

    try:
        model_data = resp["model_data"][0]
        character_data = resp["character_data"][0]
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character or model data not found",
        )
    
    tokens_count = 0
    thoughts_count = 0
    max_thoughts = 2
    new_session_entries: list[Entry] = []
    max_tokens_count = model_data["max_length"] * 0.7
    for entry in reversed(session_entries):
            tokens_count += entry.token_count
            if tokens_count > max_tokens_count:
                break

            if entry.role == "system" and entry.name == "thought":
                if thoughts_count >= max_thoughts:
                    continue
                else:
                    thoughts_count += 1

            new_session_entries.insert(0, entry)
    
    # generate response
    default_settings = model_data["default_settings"]

    response = openai.ChatCompletion.create(
        model=model_data["model_name"],
        messages=[
            {"role": e.role, "name": e.name, "content": e.content} 
            for e in new_session_entries
        ],
        max_tokens=default_settings["max_tokens"],
        temperature=default_settings["temperature"],
        repetition_penalty=default_settings["repetition_penalty"],
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
