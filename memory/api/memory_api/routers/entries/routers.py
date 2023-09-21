from fastapi import APIRouter
from .protocol import Entry, EntryRequest, EntriesRequest
from memory_api.clients.cozo import client
from memory_api.common.db.entries import add_entries


router = APIRouter()


@router.get("/entries/")
def get_entries(request: EntryRequest) -> list[Entry]:
    query = f"""
    input[session_id] <- [[
        to_uuid("{request.session_id}"),
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
def create_entries(request: EntriesRequest):
    add_entries(request.entries)
