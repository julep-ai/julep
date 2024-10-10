"""Defines custom exceptions for agent-related operations in the agents API."""

from uuid import UUID

from . import BaseCommonException


class BaseAgentException(BaseCommonException):
    """Base exception class for all agent-related exceptions."""

    pass


class AgentNotFoundError(BaseAgentException):
    """
    Exception raised when a requested agent cannot be found.
    Attributes:
        developer_id (UUID | str): The ID of the developer attempting the operation.
        agent_id (UUID | str): The ID of the agent that was not found.
    """

    def __init__(self, developer_id: UUID | str, agent_id: UUID | str):
        # Initialize the exception with a message indicating the missing agent and developer ID.
        super().__init__(
            f"Agent {str(agent_id)} not found for developer {str(developer_id)}",
            http_code=404,
        )


class AgentToolNotFoundError(BaseAgentException):
    """
    Exception raised when a requested tool associated with an agent cannot be found.
    Attributes:
        agent_id (UUID | str): The ID of the agent that was not found.
        tool_id (UUID | str): The ID of the tool that was not found.
    """

    def __init__(self, agent_id: UUID | str, tool_id: UUID | str):
        # Initialize the exception with a message indicating the missing tool and agent ID.
        super().__init__(
            f"Tool {str(tool_id)} not found for agent {str(agent_id)}", http_code=404
        )


class AgentDocNotFoundError(BaseAgentException):
    """
    Exception raised when a requested document associated with an agent cannot be found.
    Attributes:
        agent_id (UUID | str): The ID of the agent that was not found.
        doc_id (UUID | str): The ID of the document that was not found.
    """

    def __init__(self, agent_id: UUID | str, doc_id: UUID | str):
        # Initialize the exception with a message indicating the missing document and agent ID.
        super().__init__(
            f"Doc {str(doc_id)} not found for agent {str(agent_id)}", http_code=404
        )


class AgentModelNotValid(BaseAgentException):
    """Exception raised when requested model is not recognized."""

    def __init__(self, model: str, all_models: list[str]):
        super().__init__(
            f"Unknown model: {model}. Please provide a valid model name."
            "Available models: " + ", ".join(all_models),
            http_code=400,
        )


class MissingAgentModelAPIKeyError(BaseAgentException):
    """Exception raised when API key for requested model is missing."""

    def __init__(self, model: str):
        super().__init__(
            f"API key missing for model: {model}. Please provide a valid API key in the configuration",
            http_code=400,
        )
