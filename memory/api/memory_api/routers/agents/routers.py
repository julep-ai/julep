from typing import Any
from fastapi import APIRouter, HTTPException, status
from starlette.status import HTTP_201_CREATED, HTTP_202_ACCEPTED
from pydantic import UUID4
from .protocol import (
    Agent, 
    CreateAgentRequest, 
    UpdateAgentRequest,
)
from memory_api.clients.cozo import client


router = APIRouter()


async def get_agent(agent_id: UUID4) -> Agent:
    query = f"""
    input[character_id] <- [[to_uuid("{agent_id}")]]

    ?[
        character_id,
        name,
        about,
        metadata,
        updated_at,
        created_at,
    ] := input[character_id],
        *agents {{
            character_id,
            name,
            about,
            metadata,
            updated_at: validity,
            created_at,
            @ "NOW"
        }}, updated_at = to_int(validity)"""

    try:
        res = [row.to_dict() for _, row in client.run(query).iterrows()][0]
        return Agent(**res)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )


@router.delete("/agents/{agent_id}", status_code=HTTP_202_ACCEPTED)
async def delete_agent(agent_id: UUID4) -> Agent:
    try:
        client.rm("agents", {"agent_id": agent_id})
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )


@router.put("/agents/{agent_id}")
async def update_agent(agent_id: UUID4, request: UpdateAgentRequest) -> Agent:
    try:
        client.update(
            "agents", 
            {
                "agent_id": agent_id, 
                "about": request.about, 
                # "instructions": request.instructions, 
                # "tools": {
                #     {"type": t.type_, "definition": t.definition} 
                #     for t in request.tools
                # },
            }
        )
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )


@router.post("/agents", status_code=HTTP_201_CREATED)
async def create_agent(agent: CreateAgentRequest) -> Agent:
    query = f"""
    ?[character_id, name, about, metadata] <- [
        ["{agent.id}", "{agent.name}", "{agent.about}", {{}}]
    ]
    
    :put agents {{
        agent_id =>
        name,
        about,
        metadata,
    }}
    """

    client.run(query)

    return await get_agent(agent_id=agent.id)


@router.get("/agents")
async def list_agents(limit: int = 100, offset: int = 0) -> list[Agent]:
    query = f"""
    ?[
        agent_id,
        name,
        about,
        metadata,
        updated_at,
        created_at,
    ] := *agents {{
            agent_id,
            name,
            about,
            metadata,
            updated_at: validity,
            created_at,
            @ "NOW"
        }}, updated_at = to_int(validity)
    
    :limit {limit}
    :offset {offset}
    """

    return [Agent(**row.to_dict()) for _, row in client.run(query).iterrows()]


@router.get("/agents/{agent_id}/memories")
async def list_memories(agent_id: UUID4) -> list[Any]:
    # TODO: implement later
    return []
