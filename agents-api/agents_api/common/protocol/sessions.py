from uuid import UUID

from pydantic import BaseModel, validator

from .agents import AgentDefaultSettings

from model_registry import ALL_AVAILABLE_MODELS

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
    model: str
    default_settings: SessionSettings

    @validator('model')
    def validate_model_type(cls, model):
        if model not in ALL_AVAILABLE_MODELS.keys():
            raise ValueError(
            f"Unknown model: {model}. Please provide a valid model name."
            "Known models are: " + ", ".join(ALL_AVAILABLE_MODELS.keys())
        )

        return model
