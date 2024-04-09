from uuid import UUID
from . import BaseCommonException
from agents_api.model_registry import ALL_AVAILABLE_MODELS

class BaseAgentException(BaseCommonException):
    pass


class AgentNotFoundError(BaseAgentException):
    def __init__(self, developer_id: UUID | str, agent_id: UUID | str):
        super().__init__(
            f"Agent {str(agent_id)} not found for developer {str(developer_id)}",
            http_code=404,
        )


class AgentToolNotFoundError(BaseAgentException):
    def __init__(self, agent_id: UUID | str, tool_id: UUID | str):
        super().__init__(
            f"Tool {str(tool_id)} not found for agent {str(agent_id)}", http_code=404
        )


class AgentDocNotFoundError(BaseAgentException):
    def __init__(self, agent_id: UUID | str, doc_id: UUID | str):
        super().__init__(
            f"Doc {str(doc_id)} not found for agent {str(agent_id)}", http_code=404
        )

class AgentModelNotValid(BaseAgentException):
    def __init__(self, model: str):
        super().__init__(
             f"Unknown model: {model}. Please provide a valid model name."
            "Known models are: " + ", ".join(ALL_AVAILABLE_MODELS.keys()), http_code=400
        )