from pydantic import BaseModel


class Entry(BaseModel):
    id: str
    session_id: str
    timestamp: int
    role: str
    name: str
    content: str
    token_count: int
    processed: bool
    parent_id: str | None


class EntryRequest(BaseModel):
    session_id: str
