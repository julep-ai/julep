from pydantic import BaseModel


class Character(BaseModel):
    id: str
    name: str
    about: str
    metadata: dict
    created_at: int
    updated_at: int


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