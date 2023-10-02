from pydantic import BaseModel
from memory_api.common.protocol.entries import Entry


class EntryRequest(BaseModel):
    session_id: str


class EntriesRequest(BaseModel):
    entries: list[Entry]
