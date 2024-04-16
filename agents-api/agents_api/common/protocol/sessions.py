"""
This module defines session-related data structures and settings used across the agents API.
It includes definitions for session settings and session data models.
"""

from uuid import UUID

from pydantic import BaseModel, validator

from .agents import AgentDefaultSettings

from agents_api.model_registry import ALL_AVAILABLE_MODELS


class SessionSettings(AgentDefaultSettings):
    """
    A placeholder for session-specific settings, inheriting from AgentDefaultSettings.
    Currently, it does not extend the base class with additional properties.
    """

    pass


class SessionData(BaseModel):
    """
    Represents the data associated with a session, including identifiers for the agent, user, and session itself,
    along with session-specific information such as situation, summary, and timestamps.
    """

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

    @validator("model")
    def validate_model_type(cls, model):
        if model not in ALL_AVAILABLE_MODELS.keys():
            raise ValueError(
                f"Unknown model: {model}. Please provide a valid model name."
                "Known models are: " + ", ".join(ALL_AVAILABLE_MODELS.keys())
            )

        return model
