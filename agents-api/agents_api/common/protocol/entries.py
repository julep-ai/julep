from datetime import datetime
import json
from typing import Literal, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, computed_field
from agents_api.autogen.openapi_model import Role

EntrySource = Literal["api_request", "api_response", "internal", "summarizer"]
Tokenizer = Literal["character_count"]
Content = Union[str, dict]


class Entry(BaseModel):
    id: UUID = Field(alias="entry_id", default_factory=uuid4)
    session_id: UUID
    source: EntrySource = Field(default="api_request")
    role: Role
    name: str | None = None
    content: Content
    tokenizer: str = Field(default="character_count")
    created_at: float = Field(default_factory=lambda: datetime.utcnow().timestamp())
    timestamp: float = Field(default_factory=lambda: datetime.utcnow().timestamp())

    @computed_field
    @property
    def token_count(self) -> int:
        if self.tokenizer == "character_count":
            content_length = (
                len(self.content)
                if isinstance(self.content, str)
                else len(json.dumps(self.content))
            )
            return int(content_length // 3.5)

        raise NotImplementedError(f"Unknown tokenizer: {self.tokenizer}")

    class Config:
        use_enum_values = True
        use_enum_values = True  # <--
