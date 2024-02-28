from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
import json
from pydantic import UUID4, BaseModel
from starlette.status import HTTP_201_CREATED, HTTP_202_ACCEPTED
from typing import Annotated
from uuid import uuid4

from agents_api.clients.cozo import client
from agents_api.clients.embed import embed
from agents_api.models.agent.create_agent import create_agent_query
from agents_api.models.agent.list_agents import list_agents_query
from agents_api.models.agent.delete_agent import delete_agent_query
from agents_api.models.agent.update_agent import update_agent_query
from agents_api.models.agent.get_agent import get_agent_query
from agents_api.models.agent.create_tools import create_tools_query
from agents_api.models.agent.update_tool import update_tool_by_id_query
from agents_api.models.docs.create_docs import (
    create_docs_query,
)
from agents_api.models.docs.list_docs import (
    list_docs_snippets_by_owner_query,
)
from agents_api.models.docs.delete_docs import (
    delete_docs_by_id_query,
)
from agents_api.models.docs.get_docs import (
    get_docs_snippets_by_id_query,
)
from agents_api.models.docs.embed_docs import (
    embed_docs_snippets_query,
)
from agents_api.models.tools.create_tools import create_function_query
from agents_api.models.tools.embed_tools import embed_functions_query
from agents_api.models.tools.list_tools import list_functions_by_agent_query
from agents_api.models.tools.get_tools import get_function_by_id_query
from agents_api.models.tools.delete_tools import delete_function_by_id_query
from agents_api.models.instructions.create_instructions import create_instructions_query
from agents_api.models.instructions.embed_instructions import embed_instructions_query
from agents_api.models.instructions.delete_instructions import (
    delete_instructions_by_agent_query,
)
from agents_api.dependencies.developer_id import get_developer_id
from agents_api.autogen.openapi_model import (
    Agent,
    CreateAgentRequest,
    UpdateAgentRequest,
    ResourceCreatedResponse,
    ResourceDeletedResponse,
    ResourceUpdatedResponse,
    AgentDefaultSettings,
    CreateDoc,
    Doc,
    CreateToolRequest,
    Tool,
    FunctionDef,
)


class AgentList(BaseModel):
    items: list[Agent]


class DocsList(BaseModel):
    items: list[Doc]


class ToolList(BaseModel):
    items: list[Tool]


router = APIRouter()
snippet_embed_instruction = "Encode this passage for retrieval: "
function_embed_instruction = "Transform this tool description for retrieval: "
instruction_embed_instruction = "Embed this historical text chunk for retrieval: "


@router.delete("/agents/{agent_id}", status_code=HTTP_202_ACCEPTED, tags=["agents"])
async def delete_agent(
    agent_id: UUID4, x_developer_id: Annotated[UUID4, Depends(get_developer_id)]
) -> ResourceDeletedResponse:
    # TODO: add 404 handling
    client.run(delete_agent_query(x_developer_id, agent_id))

    return ResourceDeletedResponse(id=agent_id, deleted_at=datetime.now())


@router.put("/agents/{agent_id}", tags=["agents"])
async def update_agent(
    agent_id: UUID4,
    request: UpdateAgentRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
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


@router.get("/agents/{agent_id}", tags=["agents"])
async def get_agent_details(
    agent_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> Agent:
    try:
        resp = [
            row.to_dict()
            for _, row in client.run(
                get_agent_query(
                    developer_id=x_developer_id,
                    agent_id=agent_id,
                )
            ).iterrows()
        ][0]

        return Agent(**resp)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )


@router.post("/agents", status_code=HTTP_201_CREATED, tags=["agents"])
async def create_agent(
    request: CreateAgentRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
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

    if request.docs:
        client.run(
            "\n".join(
                [
                    create_docs_query(
                        owner_type="agent",
                        owner_id=new_agent_id,
                        id=uuid4(),
                        title=info.title,
                        content=info.content,
                    )
                    for info in request.docs
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

    if request.tools:
        functions = [t.function for t in request.tools]
        embeddings = await embed(
            [
                function_embed_instruction
                + f"{function.name}, {function.description}, "
                + "required_params:"
                + function.parameters.model_dump_json()
                for function in functions
            ]
        )
        client.run(
            create_tools_query(
                new_agent_id,
                functions,
                embeddings,
            )
        )

    return res


@router.get("/agents", tags=["agents"])
async def list_agents(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    limit: int = 100,
    offset: int = 0,
) -> AgentList:
    return AgentList(
        items=[
            Agent(**row.to_dict())
            for _, row in client.run(
                list_agents_query(
                    developer_id=x_developer_id,
                    limit=limit,
                    offset=offset,
                )
            ).iterrows()
        ]
    )


@router.post("/agents/{agent_id}/docs", tags=["agents"])
async def create_docs(agent_id: UUID4, request: CreateDoc) -> ResourceCreatedResponse:
    doc_id = uuid4()
    resp = client.run(
        create_docs_query(
            owner_type="agent",
            owner_id=agent_id,
            id=doc_id,
            title=request.title,
            content=request.content,
        )
    )

    doc_id = resp["doc_id"][0]
    res = ResourceCreatedResponse(
        id=doc_id,
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
        embed_docs_snippets_query(
            doc_id=doc_id,
            snippet_indices=indices,
            embeddings=embeddings,
        )
    )

    return res


@router.get("/agents/{agent_id}/docs", tags=["agents"])
async def list_docs(agent_id: UUID4, limit: int = 100, offset: int = 0) -> DocsList:
    resp = client.run(
        list_docs_snippets_by_owner_query(
            owner_type="agent",
            owner_id=agent_id,
        )
    )

    return DocsList(
        items=[
            Doc(
                # TODO: Need to return created_at here
                # created_at= ...
                id=row["doc_id"],
                title=row["title"],
                content=row["snippet"],
            )
            for _, row in resp.iterrows()
        ]
    )


@router.delete("/agents/{agent_id}/docs/{doc_id}", tags=["agents"])
async def delete_docs(agent_id: UUID4, doc_id: UUID4) -> ResourceDeletedResponse:
    resp = client.run(
        get_docs_snippets_by_id_query(
            owner_type="agent",
            doc_id=doc_id,
        )
    )
    if not resp.size:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docs not found",
        )

    client.run(
        delete_docs_by_id_query(
            owner_type="agent",
            owner_id=agent_id,
            doc_id=doc_id,
        )
    )

    return ResourceDeletedResponse(id=doc_id, deleted_at=datetime.now())


@router.post("/agents/{agent_id}/tools", tags=["agents"])
async def create_tool(
    agent_id: UUID4, request: CreateToolRequest
) -> ResourceCreatedResponse:
    resp = client.run(
        create_function_query(
            agent_id=agent_id,
            id=uuid4(),
            function=request.function,
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
            + request.function.description
            + "\nParameters: "
            + json.dumps(request.function.parameters.model_dump())
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
async def list_tools(agent_id: UUID4, limit: int = 100, offset: int = 0) -> ToolList:
    resp = client.run(
        list_functions_by_agent_query(
            agent_id=agent_id,
            limit=limit,
            offset=offset,
        )
    )

    return ToolList(
        items=[
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
    )


@router.delete("/agents/{agent_id}/tools/{tool_id}", tags=["agents"])
async def delete_tool(agent_id: UUID4, tool_id: UUID4) -> ResourceDeletedResponse:
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

    return ResourceDeletedResponse(id=tool_id, deleted_at=datetime.now())


@router.put("/agents/{agent_id}/tools/{tool_id}", tags=["agents"])
async def update_tool(
    agent_id: UUID4, tool_id: UUID4, request: FunctionDef
) -> ResourceUpdatedResponse:
    embedding = await embed(
        [
            function_embed_instruction
            + request.description
            + "\nParameters: "
            + json.dumps(request.parameters.model_dump())
        ],
        join_inputs=True,
    )

    try:
        return client.run(
            update_tool_by_id_query(
                agent_id=agent_id,
                tool_id=tool_id,
                function=request,
                embedding=embedding,
            )
        )
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent or tool not found",
        )


@router.delete("/agents/{agent_id}/memories/{memory_id}", tags=["agents"])
async def delete_memories(agent_id: UUID4, memory_id: UUID4) -> ResourceDeletedResponse:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
    )

    return ResourceDeletedResponse(id=memory_id, deleted_at=datetime.now())


# @router.get("/agents/{agent_id}/memories", tags=["agents"])
# async def list_memories(agent_id: UUID4) -> list[Any]:
#     # TODO: implement later
#     return []
