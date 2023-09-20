from pydantic import BaseModel


class Session(BaseModel):
    id: str
    character_id: str
    user_id: str
    updated_at: int
    created_at: int
    situation: str
    summary: str
    metadata: dict


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


class SessionsRequest(BaseModel):
    session_id: str
