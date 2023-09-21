from pydantic import BaseModel
from memory_api.common.protocol.entries import Entry


class Session(BaseModel):
    id: str
    character_id: str
    user_id: str
    updated_at: float
    created_at: float
    situation: str
    summary: str
    metadata: dict


class ChatParams(BaseModel):
    messages: list[Entry]


class ChatRequest(BaseModel):
    session_id: str
    params: ChatParams
    remember: bool = False
    recall: bool = False


class SessionsRequest(BaseModel):
    session_id: str
