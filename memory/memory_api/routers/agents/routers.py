from uuid import uuid4
from typing import Any, Annotated
from fastapi import APIRouter, HTTPException, status, Header
from starlette.status import HTTP_201_CREATED, HTTP_202_ACCEPTED
from pydantic import UUID4

from memory_api.clients.cozo import client
from memory_api.models.agent.create_agent import create_agent_query
from memory_api.models.agent.list_agents import list_agents_query
from memory_api.models.agent.delete_agent import delete_agent_query
from memory_api.models.agent.update_agent import update_agent_query
from memory_api.models.additional_info.create_additional_info import (
    create_additional_info_query,
)
from memory_api.models.additional_info.list_additional_info import (
    list_additional_info_snippets_by_owner_query,
)
from memory_api.models.additional_info.delete_additional_info import (
    delete_additional_info_by_id_query,
)
from memory_api.models.additional_info.get_additional_info import (
    get_additional_info_snippets_by_id_query,
)
from memory_api.autogen.openapi_model import (
    Agent,
    CreateAgentRequest,
    UpdateAgentRequest,
    ResourceCreatedResponse,
    ResourceUpdatedResponse,
    AgentDefaultSettings,
    CreateAdditionalInfoRequest,
    AdditionalInfo,
)


router = APIRouter()


@router.delete("/agents/{agent_id}", status_code=HTTP_202_ACCEPTED, tags=["agents"])
async def delete_agent(agent_id: UUID4, x_developer_id: Annotated[UUID4, Header()]):
    # TODO: add 404 handling
    client.run(delete_agent_query(x_developer_id, agent_id))


@router.put("/agents/{agent_id}", tags=["agents"])
async def update_agent(
    agent_id: UUID4,
    request: UpdateAgentRequest,
    x_developer_id: Annotated[UUID4, Header()],
) -> ResourceUpdatedResponse:
    try:
        resp = client.run(
            update_agent_query(
                agent_id=agent_id,
                developer_id=x_developer_id,
                default_settings=(
                    request.default_settings or AgentDefaultSettings()
                ).model_dump(),
                name=request.name,
                about=request.about,
                model=request.model or "julep-ai/samantha-1-turbo",
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
    request: CreateAgentRequest, x_developer_id: Annotated[UUID4, Header()]
) -> ResourceCreatedResponse:
    resp = client.run(
        create_agent_query(
            agent_id=uuid4(),
            developer_id=x_developer_id,
            name=request.name,
            about=request.about,
            instructions=request.instructions,
            model=request.model,
            default_settings=request.default_settings.model_dump(),
        ),
    )

    new_agent_id = resp["agent_id"][0]
    res = ResourceCreatedResponse(
        id=new_agent_id,
        created_at=resp["created_at"][0],
    )

    if request.additional_info:
        client.run(
            "\n".join(
                [
                    create_additional_info_query(
                        owner_type="agent",
                        owner_id=new_agent_id,
                        id=uuid4(),
                        title=info.title,
                        content=info.content,
                    )
                    for info in request.additional_info
                ]
            )
        )

    return res


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


@router.post("/agents/{agent_id}/additional_info", tags=["agents"])
async def create_additional_info(
    agent_id: UUID4, request: CreateAdditionalInfoRequest
) -> ResourceCreatedResponse:
    additional_info_id = uuid4()
    resp = client.run(
        create_additional_info_query(
            owner_type="agent",
            owner_id=agent_id,
            id=additional_info_id,
            title=request.title,
            content=request.content,
        )
    )

    return ResourceCreatedResponse(
        id=resp["additional_info_id"][0],
        created_at=resp["created_at"][0],
    )


@router.get("/agents/{agent_id}/additional_info", tags=["agents"])
async def list_additional_info(
    agent_id: UUID4, limit: int = 100, offset: int = 0
) -> list[AdditionalInfo]:
    resp = client.run(
        list_additional_info_snippets_by_owner_query(
            owner_type="agent",
            owner_id=agent_id,
        )
    )

    return [
        AdditionalInfo(
            id=row["additional_info_id"],
            title=row["title"],
            content=row["snippet"],
        )
        for _, row in resp.iterrows()
    ]


@router.delete(
    "/agents/{agent_id}/additional_info/{additional_info_id}", tags=["agents"]
)
async def delete_additional_info(agent_id: UUID4, additional_info_id: UUID4):
    resp = client.run(
        get_additional_info_snippets_by_id_query(
            owner_type="agent",
            additional_info_id=additional_info_id,
        )
    )
    if not resp.size:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Additional info not found",
        )

    client.run(
        delete_additional_info_by_id_query(
            owner_type="agent",
            owner_id=agent_id,
            additional_info_id=additional_info_id,
        )
    )


@router.get("/agents/{agent_id}/memories", tags=["agents"])
async def list_memories(agent_id: UUID4) -> list[Any]:
    # TODO: implement later
    return []
