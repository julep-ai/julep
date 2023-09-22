import time
from pydantic import BaseModel, Field


class Entry(BaseModel):
    id: str | None = Field(None, alias="entry_id")
    session_id: str
    timestamp: float = Field(default_factory=time.time)
    role: str
    name: str | None = None
    content: str
    token_count: int = Field(default=0)
    processed: bool = Field(default=False)
    parent_id: str | None = None
