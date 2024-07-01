"""
This module defines session-related data structures and settings used across the agents API.
It includes definitions for session settings and session data models.
"""

from uuid import UUID

from pydantic import BaseModel

from .agents import AgentDefaultSettings

from typing import Optional, Dict


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
    user_id: Optional[UUID]
    session_id: UUID
    situation: str
    summary: Optional[str]
    user_name: Optional[str]
    user_about: Optional[str]
    agent_name: Optional[str]
    agent_about: str
    updated_at: float
    created_at: float
    model: str
    default_settings: SessionSettings
    render_templates: bool = False
    metadata: Dict = {}
    user_metadata: Optional[Dict] = None
    agent_metadata: Dict = {}
    token_budget: int | None = None
    context_overflow: str | None = None
