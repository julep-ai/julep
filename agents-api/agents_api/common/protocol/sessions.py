"""
This module defines session-related data structures and settings used across the agents API.
It includes definitions for session settings and session data models.
"""

from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel

from ...autogen.openapi_model import Agent, Session, Settings, User, make_session
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
    settings: Optional[Settings] = None
