from uuid import UUID

from ...autogen.openapi_model import CreateAgentRequest, CreateResponse, CreateSessionRequest
from ...queries.agents.create_agent import create_agent
from ...queries.sessions.create_session import create_session
async def create_responses_user(developer_id: UUID, create_response_data: CreateResponse) -> UUID:
    data = CreateAgentRequest(
        developer_id=developer_id,
        model=create_response_data.model,
        instructions=create_response_data.instructions,
        metadata=create_response_data.metadata,
    )
    agent = await create_agent(data)
    return agent

async def create_responses_session(developer_id: UUID, create_response_data: CreateResponse, agent_id: UUID) -> UUID:
    data = CreateSessionRequest(
        developer_id=developer_id,
        agent=agent_id,
        metadata=create_response_data.metadata, # Should this be in CreateSessionRequest or CreateAgentRequest?
    )
    session = await create_session(data)
    return session