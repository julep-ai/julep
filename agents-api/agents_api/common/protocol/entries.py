from datetime import datetime
from typing import Literal, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, computed_field, validator
from agents_api.autogen.openapi_model import Role

EntrySource = Literal["api_request", "api_response", "internal", "summarizer"]
Tokenizer = Literal["character_count"]


class Entry(BaseModel):
    id: UUID = Field(alias="entry_id", default_factory=uuid4)
    session_id: UUID
    source: EntrySource = Field(default="api_request")
    role: Role
    name: str | None = None
    content: Any
    tokenizer: str = Field(default="character_count")
    created_at: float = Field(default_factory=lambda: datetime.utcnow().timestamp())
    timestamp: float = Field(default_factory=lambda: datetime.utcnow().timestamp())

    @validator('content')
    def validate_content(cls, content):
        if not isinstance(content, (str)):
            raise ValueError("CompletionResponse not in expected format. Must be a str")
        return content

    @computed_field
    @property
    def token_count(self) -> int:
        if self.tokenizer == "character_count":
            return int(len(self.content) // 3.5)

        raise NotImplementedError(f"Unknown tokenizer: {self.tokenizer}")

    class Config:
        use_enum_values = True  # <--
