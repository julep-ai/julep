from fastapi import APIRouter
from pydantic import UUID4
from .protocol import EntriesRequest
from agents_api.clients.cozo import client
from agents_api.common.protocol.entries import Entry
from agents_api.models.entry.add_entries import add_entries_query
from agents_api.models.entry.get_entries import get_entries_query


router = APIRouter()


@router.get("/entries/{session_id}", tags=["entries"])
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


@router.post("/entries/", tags=["entries"])
async def create_entries(request: EntriesRequest):
    return client.run(
        add_entries_query(request.entries, return_result=True),
    )
