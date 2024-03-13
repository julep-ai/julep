from uuid import UUID


class BaseAgentException(Exception):
    pass


class AgentNotFoundError(BaseAgentException):
    def __init__(self, developer_id: UUID | str, agent_id: UUID | str):
        super().__init__(
            f"Agent {str(agent_id)} not found for developer {str(developer_id)}"
        )
