"""
This module defines session-related data structures and settings used across the agents API.
It includes definitions for session settings and session data models.
"""

from uuid import UUID

from pydantic import AwareDatetime, BaseModel, EmailStr


class Developer(BaseModel):
    """
    Represents the data associated with a developer
    """

    id: UUID
    email: EmailStr
    active: bool
    tags: list[str]
    settings: dict
    created_at: AwareDatetime
    created_at: AwareDatetime
