from uuid import uuid4
from typing import Any, Annotated
from fastapi import APIRouter, HTTPException, status, Header
from starlette.status import HTTP_201_CREATED, HTTP_202_ACCEPTED
from pydantic import UUID4

from memory_api.clients.cozo import client
from memory_api.models.agent.create_agent import create_agent_query
from memory_api.models.agent.get_agent import get_agent_query
from memory_api.models.agent.list_agents import list_agents_query
from memory_api.models.agent.delete_agent import delete_agent_query
from memory_api.models.agent.update_agent import update_agent_query
from memory_api.autogen.openapi_model import (
    Agent,
    CreateAgentRequest,
    UpdateAgentRequest,
    ResourceCreatedResponse,
    ResourceUpdatedResponse,
    AgentDefaultSettings,
)


router = APIRouter()


@router.delete("/agents/{agent_id}", status_code=HTTP_202_ACCEPTED, tags=["agents"])
async def delete_agent(agent_id: UUID4, x_developer_id: Annotated[UUID4, Header()]):
    try:
        client.run(delete_agent_query(x_developer_id, agent_id))
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )


@router.put("/agents/{agent_id}", tags=["agents"])
async def update_agent(
    agent_id: UUID4,
    request: UpdateAgentRequest,
    x_developer_id: Annotated[UUID4, Header()],
) -> ResourceUpdatedResponse:
    try:
        resp = client.run(
            update_agent_query(
                agent_id,
                x_developer_id,
                request.name,
                request.about,
                request.model or "julep-ai/samantha-1-turbo",
                (request.default_settings or AgentDefaultSettings()).model_dump(),
            )
        )

        return ResourceUpdatedResponse(
            id=resp["agent_id"][0], 
            updated_at=resp["updated_at"][0],
        )
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )


@router.post("/agents", status_code=HTTP_201_CREATED, tags=["agents"])
async def create_agent(
    agent: CreateAgentRequest, x_developer_id: Annotated[UUID4, Header()]
) -> ResourceCreatedResponse:
    agent_id = uuid4()
    resp = client.run(
        create_agent_query(
            agent_id=agent_id,
            developer_id=x_developer_id,
            name=agent.name,
            about=agent.about,
        ),
    )
    
    return ResourceCreatedResponse(
        id=resp["agent_id"][0], 
        created_at=resp["created_at"][0],
    )


@router.get("/agents", tags=["agents"])
async def list_agents(
    x_developer_id: Annotated[UUID4, Header()], limit: int = 100, offset: int = 0
) -> list[Agent]:
    return [
        Agent(**row.to_dict())
        for _, row in client.run(
            list_agents_query(
                developer_id=x_developer_id,
                limit=limit,
                offset=offset,
            )
        ).iterrows()
    ]


@router.get("/agents/{agent_id}/memories", tags=["agents"])
async def list_memories(agent_id: UUID4) -> list[Any]:
    # TODO: implement later
    return []
