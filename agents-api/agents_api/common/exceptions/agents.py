from uuid import UUID
from . import BaseCommonException


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
