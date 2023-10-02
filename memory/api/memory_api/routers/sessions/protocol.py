from uuid import uuid4
from pydantic import BaseModel, Field, UUID4
from memory_api.common.protocol.entries import Entry


class Session(BaseModel):
    id: UUID4 = Field(default_factory=uuid4, alias="session_id")
    character_id: str
    user_id: str
    updated_at: float | None = None
    created_at: float | None = None
    situation: str
    summary: str | None = None
    metadata: dict = Field(default={})


class ChatParams(BaseModel):
    messages: list[Entry]


class ChatRequest(BaseModel):
    session_id: str
    params: ChatParams
    remember: bool = False
    recall: bool = False


class SessionsRequest(BaseModel):
    session_id: str
