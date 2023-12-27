from uuid import UUID

from pydantic import BaseModel

class SessionData(BaseModel):
    agent_id: UUID
    user_id: UUID
    session_id: UUID
    situation: str
    summary: str | None
    user_about: str
    agent_about: str
    updated_at: float
    created_at: float
