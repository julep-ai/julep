from pydantic import BaseModel, Field


class Entry(BaseModel):
    id: str | None = Field(None, alias="entry_id")
    session_id: str
    source: str
    role: str
    name: str | None = None
    content: str
    token_count: int = Field(default=0)
    tokenizer: str  = Field(default="character_count")
    created_at: float | None = None
