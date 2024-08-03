"""
This module defines session-related data structures and settings used across the agents API.
It includes definitions for session settings and session data models.
"""

from typing import Optional

from pydantic import BaseModel

from ...autogen.openapi_model import (
    Agent,
    Entry,
    GenerationPresetSettings,
    OpenAISettings,
    Session,
    Tool,
    User,
    VLLMSettings,
)
from .agents import AgentDefaultSettings


class SessionSettings(AgentDefaultSettings):
    """
    A placeholder for session-specific settings, inheriting from AgentDefaultSettings.
    Currently, it does not extend the base class with additional properties.
    """

    pass


class SessionData(BaseModel):
    """
    Represents the data associated with a session, including for agents, and users.
    """

    session: Session
    agents: list[Agent]
    users: list[User] = []
    settings: Optional[GenerationPresetSettings | OpenAISettings | VLLMSettings] = None


class ChatContext(SessionData):
    """
    Represents the data associated with a context, including for agents, and users.
    """

    entries: list[Entry]
    tools: list[Tool]
