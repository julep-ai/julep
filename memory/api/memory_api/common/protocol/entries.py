from pydantic import BaseModel, Field


class Entry(BaseModel):
    id: str = Field(..., alias="entry_id")
    session_id: str | None
    timestamp: float | None
    role: str
    name: str | None
    content: str
    token_count: int | None
    processed: bool | None
    parent_id: str | None
