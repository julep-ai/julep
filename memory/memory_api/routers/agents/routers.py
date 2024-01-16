import json
from uuid import uuid4
from typing import Any, Annotated
from fastapi import APIRouter, HTTPException, status, Header
from starlette.status import HTTP_201_CREATED, HTTP_202_ACCEPTED
from pydantic import UUID4

from memory_api.clients.cozo import client
from memory_api.clients.embed import embed
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
from memory_api.models.additional_info.embed_additional_info import (
    embed_additional_info_snippets_query,
)
from memory_api.models.tools.create_tools import create_function_query
from memory_api.models.tools.embed_tools import embed_functions_query
from memory_api.models.tools.list_tools import list_functions_by_agent_query
from memory_api.models.tools.get_tools import get_function_by_id_query
from memory_api.models.tools.delete_tools import delete_function_by_id_query
from memory_api.models.instructions.create_instructions import create_instructions_query
from memory_api.models.instructions.embed_instructions import embed_instructions_query
from memory_api.models.instructions.delete_instructions import (
    delete_instructions_by_agent_query,
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
    CreateToolRequest,
    Tool,
    FunctionDef,
)


router = APIRouter()
snippet_embed_instruction = "Encode this passage for retrieval: "
function_embed_instruction = "Transform this tool description for retrieval: "
instruction_embed_instruction = "Embed this historical text chunk for retrieval: "


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

        updated_agent_id = resp["agent_id"][0]
        res = ResourceUpdatedResponse(
            id=updated_agent_id,
            updated_at=resp["updated_at"][0],
        )

        if request.instructions:
            indices, instructions = list(zip(*enumerate(request.instructions)))
            embeddings = await embed(
                [
                    instruction_embed_instruction + instruction.content
                    for instruction in instructions
                ]
            )
            query = "\n".join(
                [
                    delete_instructions_by_agent_query(agent_id=updated_agent_id),
                    create_instructions_query(
                        agent_id=updated_agent_id,
                        instructions=request.instructions,
                    ),
                    embed_instructions_query(
                        agent_id=updated_agent_id,
                        instruction_indices=indices,
                        embeddings=embeddings,
                    ),
                ]
            )
            client.run(query)

        return res
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
            default_settings=(
                request.default_settings or AgentDefaultSettings()
            ).model_dump(),
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

    if request.instructions:
        indices, instructions = list(zip(*enumerate(request.instructions)))
        embeddings = await embed(
            [
                instruction_embed_instruction + instruction.content
                for instruction in instructions
            ]
        )
        client.run(
            embed_instructions_query(
                agent_id=new_agent_id,
                instruction_indices=indices,
                embeddings=embeddings,
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

    additional_info_id = resp["additional_info_id"][0]
    res = ResourceCreatedResponse(
        id=additional_info_id,
        created_at=resp["created_at"][0],
    )

    indices, snippets = list(zip(*enumerate(request.content.split("\n\n"))))
    embeddings = await embed(
        [
            snippet_embed_instruction + request.title + "\n\n" + snippet
            for snippet in snippets
        ]
    )

    client.run(
        embed_additional_info_snippets_query(
            additional_info_id=additional_info_id,
            snippet_indices=indices,
            embeddings=embeddings,
        )
    )

    return res


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


@router.post("/agents/{agent_id}/tools", tags=["agents"])
async def create_tool(
    agent_id: UUID4, request: CreateToolRequest
) -> ResourceCreatedResponse:
    resp = client.run(
        create_function_query(
            agent_id=agent_id,
            id=uuid4(),
            function=request.definition,
        )
    )

    tool_id = resp["tool_id"][0]
    res = ResourceCreatedResponse(
        id=tool_id,
        created_at=resp["created_at"][0],
    )

    embeddings = await embed(
        [
            function_embed_instruction
            + request.definition.description
            + "\nParameters: "
            + json.dumps(request.definition.parameters.model_dump())
        ]
    )

    client.run(
        embed_functions_query(
            agent_id=agent_id,
            tool_ids=[tool_id],
            embeddings=embeddings,
        )
    )

    return res


@router.get("/agents/{agent_id}/tools", tags=["agents"])
async def list_tools(agent_id: UUID4, limit: int = 100, offset: int = 0) -> list[Tool]:
    resp = client.run(
        list_functions_by_agent_query(
            agent_id=agent_id,
        )
    )

    return [
        Tool(
            type="function",
            definition=FunctionDef(
                description=row.get("description"),
                name=row["name"],
                parameters=row["parameters"],
            ),
            id=row["tool_id"],
        )
        for _, row in resp.iterrows()
    ]


@router.delete("/agents/{agent_id}/tools/{tool_id}", tags=["agents"])
async def delete_tool(agent_id: UUID4, tool_id: UUID4):
    resp = client.run(
        get_function_by_id_query(
            agent_id=agent_id,
            tool_id=tool_id,
        )
    )
    if not resp.size:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found",
        )

    client.run(
        delete_function_by_id_query(
            agent_id=agent_id,
            tool_id=tool_id,
        )
    )


@router.get("/agents/{agent_id}/memories", tags=["agents"])
async def list_memories(agent_id: UUID4) -> list[Any]:
    # TODO: implement later
    return []
