from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, computed_field

EntrySource = Literal["api_request", "api_response"]
Role = Literal["user", "assistant", "system"]
Tokenizer = Literal["character_count"]


class Entry(BaseModel):
    id: UUID = Field(alias="entry_id", default_factory=uuid4)
    session_id: UUID
    source: EntrySource = Field(default="api_request")
    role: Role
    name: str | None = None
    content: str
    tokenizer: str = Field(default="character_count")
    created_at: float = Field(default_factory=lambda: datetime.utcnow().timestamp())

    @computed_field
    @property
    def token_count(self) -> int:
        if self.tokenizer == "character_count":
            return int(len(self.content) // 3.5)

        raise NotImplementedError(f"Unknown tokenizer: {self.tokenizer}")

    class Config:
        use_enum_values = True  # <--
