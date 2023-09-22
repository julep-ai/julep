from fastapi import APIRouter
from pydantic import UUID4
from .protocol import Entry, EntriesRequest
from memory_api.clients.cozo import client
from memory_api.common.db.entries import add_entries


router = APIRouter()


@router.get("/entries/{session_id}")
async def get_entries(session_id: UUID4) -> list[Entry]:
    query = f"""
    input[session_id] <- [[
        to_uuid("{session_id}"),
    ]]

    ?[
        session_id,
        entry_id,
        timestamp,
        role,
        name,
        content,
        token_count,
        processed,
        parent_id,
    ] := input[session_id],
        *entries{{
            session_id,
            entry_id,
            timestamp,
            role,
            name,
            content,
            token_count,
            processed,
            parent_id,
        }}
    """

    return [Entry(**row.to_dict()) for _, row in client.run(query).iterrows()]


@router.post("/entries/")
async def create_entries(request: EntriesRequest) -> list[Entry]:
    return add_entries(request.entries, return_result=True)
