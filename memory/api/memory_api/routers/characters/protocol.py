from pydantic import BaseModel


class Character(BaseModel):
    id: str
    name: str
    about: str
    metadata: dict
    created_at: float
    updated_at: float
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
