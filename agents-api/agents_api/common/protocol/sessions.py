"""
This module defines session-related data structures and settings used across the agents API.
It includes definitions for session settings and session data models.
"""

from uuid import UUID

from pydantic import BaseModel

from ...autogen.openapi_model import (
    Agent,
    ChatInput,
    ChatSettings,
    MultiAgentMultiUserSession,
    Session,
    SingleAgentMultiUserSession,
    SingleAgentNoUserSession,
    SingleAgentSingleUserSession,
    Tool,
    User,
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
    settings: ChatSettings | None = None


class Toolset(BaseModel):
    agent_id: UUID
    tools: list[Tool]


class ChatContext(SessionData):
    """
    Represents the data associated with a context, including for agents, and users.
    """

    toolsets: list[Toolset]

    def get_active_agent(self) -> Agent:
        """
        Get the active agent from the session data.
        """
        requested_agent: UUID | None = self.settings and self.settings.agent

        if requested_agent:
            assert requested_agent in [agent.id for agent in self.agents], (
                f"Agent {requested_agent} not found in session agents: "
                f"{[agent.id for agent in self.agents]}"
            )

            return next(agent for agent in self.agents if agent.id == requested_agent)

        return self.agents[0]

    def merge_settings(self, chat_input: ChatInput) -> ChatSettings:
        request_settings = chat_input.model_dump(exclude_unset=True)
        active_agent = self.get_active_agent()

        default_settings: AgentDefaultSettings | None = active_agent.default_settings
        default_settings: dict = (
            default_settings and default_settings.model_dump() or {}
        )

        self.settings = settings = ChatSettings(
            **{
                "model": active_agent.model,
                **default_settings,
                **request_settings,
            }
        )

        return settings

    def get_active_tools(self) -> list[Tool]:
        """
        Get the active toolset from the session data.
        """
        if len(self.toolsets) == 0:
            return []

        active_agent = self.get_active_agent()
        active_toolset = next(
            toolset for toolset in self.toolsets if toolset.agent_id == active_agent.id
        )

        return active_toolset.tools

    def get_chat_environment(self) -> dict[str, dict | list[dict]]:
        """
        Get the chat environment from the session data.
        """
        current_agent = self.get_active_agent()
        tools = self.get_active_tools()
        settings: ChatSettings | None = self.settings
        settings: dict = settings and settings.model_dump() or {}

        return {
            "session": self.session.model_dump(),
            "agents": [agent.model_dump() for agent in self.agents],
            "current_agent": current_agent.model_dump(),
            "agent": current_agent.model_dump(),
            "users": [user.model_dump() for user in self.users],
            "settings": settings,
            "tools": [tool.model_dump() for tool in tools],
        }


def make_session(
    *,
    agents: list[UUID],
    users: list[UUID],
    **data: dict,
) -> Session:
    """
    Create a new session object.
    """
    cls, participants = None, {}

    match (len(agents), len(users)):
        case (0, _):
            raise ValueError("At least one agent must be provided.")
        case (1, 0):
            cls = SingleAgentNoUserSession
            participants = {"agent": agents[0]}
        case (1, 1):
            cls = SingleAgentSingleUserSession
            participants = {"agent": agents[0], "user": users[0]}
        case (1, u) if u > 1:
            cls = SingleAgentMultiUserSession
            participants = {"agent": agents[0], "users": users}
        case _:
            cls = MultiAgentMultiUserSession
            participants = {"agents": agents, "users": users}

    return cls(**{**data, **participants})
