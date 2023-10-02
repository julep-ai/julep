from uuid import uuid4
from pydantic import BaseModel, UUID4, Field


class Character(BaseModel):
    id: UUID4 = Field(default_factory=uuid4, alias="character_id")
    name: str
    about: str
    metadata: dict = Field(default={})
    created_at: float | None = None
    updated_at: float | None = None
    model: str


class ChatMessage(BaseModel):
    name: str
    role: str
    content: str


class ChatParams(BaseModel):
    messages: ChatMessage


class ChatRequest(BaseModel):
    params: ChatParams
    remember: bool = False
    recall: bool = False


class CharacterRequest(BaseModel):
    character_id: str
