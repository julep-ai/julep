from fastapi import APIRouter
from pydantic import UUID4
from .protocol import Entry, EntriesRequest
from memory_api.clients.cozo import client
from memory_api.models.entry.add_entries import add_entries
from memory_api.models.entry.get_entries import get_entries_query


router = APIRouter()


@router.get("/entries/{session_id}")
async def get_entries(
    session_id: UUID4, limit: int = 100, offset: int = 0
) -> list[Entry]:
    return [
        Entry(**row.to_dict())
        for _, row in client.run(
            get_entries_query(
                session_id=session_id,
                limit=limit,
                offset=offset,
            ),
        ).iterrows()
    ]


@router.post("/entries/")
async def create_entries(request: EntriesRequest) -> list[Entry]:
    return add_entries(request.entries, return_result=True)
