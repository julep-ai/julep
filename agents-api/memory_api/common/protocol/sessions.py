from uuid import UUID

from pydantic import BaseModel

from .agents import ModelType, AgentDefaultSettings


class SessionSettings(AgentDefaultSettings):
    pass


class SessionData(BaseModel):
    agent_id: UUID
    user_id: UUID
    session_id: UUID
    situation: str
    summary: str | None
    user_name: str | None
    user_about: str
    agent_name: str | None
    agent_about: str
    updated_at: float
    created_at: float
    model: ModelType
    default_settings: SessionSettings
