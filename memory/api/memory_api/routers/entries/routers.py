from fastapi import APIRouter, HTTPException, status
from .protocol import Entry, EntryRequest
from memory_api.clients.cozo import client


router = APIRouter()


@router.get("/entries/")
def get_entries(request: EntryRequest) -> list[Entry]:
    query = f"""
    input[session_id] <- [[
        to_uuid("53d9d19f-3118-4365-b07d-aae0a28f0659"),
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
def create_entries(entry: Entry):
    query = f"""
    ?[session_id, role, name, content, token_count] <- [[
        to_uuid("{entry.session_id}"),
        "{entry.role}",
        "{entry.name}",
        "{entry.content}",
        {entry.token_count},
    ]]

    :put entries {{
        session_id,
        role,
        name,
        content,
        token_count,
    }}
    """

    client.run(query)
