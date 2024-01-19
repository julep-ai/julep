from uuid import UUID

from typing import Optional
from beartype import beartype
from beartype.typing import Awaitable, List, Literal, TypedDict, Union

from ..api.types import (
    Agent,
    AgentDefaultSettings,
    CreateAdditionalInfoRequest,
    CreateToolRequest,
    FunctionDef,
    Instruction,
    ResourceCreatedResponse,
    ListAgentsResponse,
    ResourceUpdatedResponse,
    GetAgentAdditionalInfoResponse,
    GetAgentToolsResponse,
    CreateToolRequest,
    AdditionalInfo,
    Tool,
    GetAgentMemoriesResponse,
    Memory,
)

from .base import BaseManager
from .utils import is_valid_uuid4


###########
## TYPES ##
###########

ModelName = Literal[
    "julep-ai/samantha-1",
    "julep-ai/samantha-1-turbo",
]

DocDict = TypedDict(
    "DocDict",
    **{k: v.outer_type_ for k, v in CreateAdditionalInfoRequest.__fields__.items()},
)
DefaultSettingsDict = TypedDict(
    "DefaultSettingsDict",
    **{k: v.outer_type_ for k, v in AgentDefaultSettings.__fields__.items()},
)
FunctionDefDict = TypedDict(
    "FunctionDefDict", **{k: v.outer_type_ for k, v in FunctionDef.__fields__.items()}
)
ToolDict = TypedDict(
    "ToolDict", **{k: v.outer_type_ for k, v in CreateToolRequest.__fields__.items()}
)
InstructionDict = TypedDict(
    "InstructionDict", **{k: v.outer_type_ for k, v in Instruction.__fields__.items()}
)


class BaseAgentsManager(BaseManager):
    def _get(self, id: Union[str, UUID]) -> Union[Agent, Awaitable[Agent]]:
        assert is_valid_uuid4(id), "id must be a valid UUID v4"
        return self.api_client.get_agent(agent_id=id)

    def _create(
        self,
        name: str,
        about: str,
        instructions: Union[List[str], List[InstructionDict]],
        tools: List[ToolDict] = [],
        functions: List[FunctionDefDict] = [],
        default_settings: DefaultSettingsDict = {},
        model: ModelName = "julep-ai/samantha-1-turbo",
        docs: List[DocDict] = [],
    ) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]:
        # Cast instructions to a list of Instruction objects
        instructions: List[Instruction] = [
            Instruction(content=content, important=False)
            if isinstance(content, str)
            else Instruction(**content)
            for content in instructions
        ]

        # Ensure that only functions or tools are provided
        assert not (functions and tools), "Only functions or tools can be provided"

        # Cast functions/tools to a list of CreateToolRequest objects
        tools: List[CreateToolRequest] = (
            [
                CreateToolRequest(type="function", definition=function)
                for function in functions
            ]
            if functions
            else [CreateToolRequest(**tool) for tool in tools]
        )

        # Cast default_settings to AgentDefaultSettings
        default_settings: AgentDefaultSettings = AgentDefaultSettings(
            **default_settings
        )

        # Cast docs to a list of CreateAdditionalInfoRequest objects
        docs: List[CreateAdditionalInfoRequest] = [
            CreateAdditionalInfoRequest(**doc) for doc in docs
        ]

        return self.api_client.create_agent(
            name=name,
            about=about,
            instructions=instructions,
            tools=tools,
            default_settings=default_settings,
            model=model,
            additional_info=docs,
        )

    def _list_items(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> Union[ListAgentsResponse, Awaitable[ListAgentsResponse]]:
        return self.api_client.list_agents(
            limit=limit,
            offset=offset,
        )

    def _delete(self, agent_id: Union[str, UUID]) -> Union[None, Awaitable[None]]:
        assert is_valid_uuid4(agent_id), "id must be a valid UUID v4"
        return self.api_client.delete_agent(agent_id=agent_id)

    def _update(
        self,
        agent_id: Union[str, UUID],
        about: Optional[str] = None,
        instructions: Optional[Union[List[str], List[InstructionDict]]] = None,
        name: Optional[str] = None,
        model: Optional[str] = None,
        default_settings: Optional[DefaultSettingsDict] = None,
    ) -> Union[ResourceUpdatedResponse, Awaitable[ResourceUpdatedResponse]]:
        assert is_valid_uuid4(agent_id), "id must be a valid UUID v4"

        if instructions is not None:
            instructions: List[Instruction] = [
                Instruction(content=content, important=False)
                if isinstance(content, str)
                else Instruction(**content)
                for content in instructions
            ]

        if default_settings is not None:
            default_settings: AgentDefaultSettings = AgentDefaultSettings(
                **default_settings
            )

        return self.api_client.update_agent(
            agent_id=agent_id,
            about=about,
            instructions=instructions,
            name=name,
            model=model,
            default_settings=default_settings,
        )

    def _get_additional_info(
        self,
        agent_id: Union[str, UUID],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Union[
        GetAgentAdditionalInfoResponse, Awaitable[GetAgentAdditionalInfoResponse]
    ]:
        return self.api_client.get_agent_additional_info(
            agent_id=agent_id,
            limit=limit,
            offset=offset,
        )

    def _create_additional_info(
        self,
        agent_id: Union[str, UUID],
        doc: DocDict,
    ) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]:
        doc: CreateAdditionalInfoRequest = CreateAdditionalInfoRequest(**doc)

        return self.api_client.create_agent_additional_info(
            agent_id=agent_id,
            request=doc,
        )

    def _delete_additional_info(
        self, agent_id: Union[str, UUID], additional_info_id: Union[str, UUID]
    ):
        return self.api_client.delete_agent_additional_info(
            agent_id=agent_id,
            additional_info_id=additional_info_id,
        )

    def _get_tools(
        self,
        agent_id: Union[str, UUID],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Union[GetAgentToolsResponse, Awaitable[GetAgentToolsResponse]]:
        return self.api_client.get_agent_tools(
            agent_id=agent_id, limit=limit, offset=offset
        )

    def _create_tool(
        self, agent_id: Union[str, UUID], tool: ToolDict
    ) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]:
        tool: CreateToolRequest = CreateToolRequest(**tool)

        return self.api_client.create_agent_tool(
            agent_id=agent_id,
            request=tool,
        )

    def _update_tool(
        self,
        agent_id: Union[str, UUID],
        tool_id: Union[str, UUID],
        definition: FunctionDefDict,
    ) -> Union[ResourceUpdatedResponse, Awaitable[ResourceUpdatedResponse]]:
        definition: FunctionDef = FunctionDef(**definition)

        return self.api_client.update_agent_tool(
            agent_id=agent_id,
            tool_id=tool_id,
            definition=definition,
        )

    def _delete_tool(
        self,
        agent_id: Union[str, UUID],
        tool_id: Union[str, UUID],
    ):
        return self.api_client.delete_agent_tool(
            agent_id=agent_id,
            tool_id=tool_id,
        )

    def _get_memories(
        self,
        agent_id: str,
        query: str,
        types: Optional[Union[str, List[str]]] = None,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Union[GetAgentMemoriesResponse, Awaitable[GetAgentMemoriesResponse]]:
        return self.api_client.get_agent_memories(
            agent_id=agent_id,
            query=query,
            types=types,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )


class AgentsManager(BaseAgentsManager):
    @beartype
    def get(self, id: Union[str, UUID]) -> Agent:
        return self._get(id=id)

    @beartype
    def create(
        self,
        *,
        name: str,
        about: str,
        instructions: Union[List[str], List[InstructionDict]],
        tools: List[ToolDict] = [],
        functions: List[FunctionDefDict] = [],
        default_settings: DefaultSettingsDict = {},
        model: ModelName = "julep-ai/samantha-1-turbo",
        docs: List[DocDict] = [],
    ) -> ResourceCreatedResponse:
        return self._create(
            name,
            about,
            instructions,
            tools,
            functions,
            default_settings,
            model,
            docs,
        )

    @beartype
    def list(
        self,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Agent]:
        return self._list_items(
            limit=limit,
            offset=offset,
        ).items

    @beartype
    def delete(self, agent_id: Union[str, UUID]):
        return self._delete(agent_id=agent_id)

    @beartype
    def update(
        self,
        agent_id: Union[str, UUID],
        *,
        about: Optional[str] = None,
        instructions: Optional[Union[List[str], List[InstructionDict]]] = None,
        name: Optional[str] = None,
        model: Optional[str] = None,
        default_settings: Optional[DefaultSettingsDict] = None,
    ) -> ResourceUpdatedResponse:
        return self._update(
            agent_id=agent_id,
            about=about,
            instructions=instructions,
            name=name,
            model=model,
            default_settings=default_settings,
        )

    @beartype
    def get_additional_info(
        self,
        agent_id: Union[str, UUID],
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[AdditionalInfo]:
        return self._get_additional_info(
            agent_id=agent_id,
            limit=limit,
            offset=offset,
        ).items

    @beartype
    def create_additional_info(
        self,
        agent_id: Union[str, UUID],
        *,
        doc: DocDict,
    ) -> ResourceCreatedResponse:
        return self._create_additional_info(
            agent_id=agent_id,
            doc=doc,
        )

    @beartype
    def delete_additional_info(
        self, agent_id: Union[str, UUID], additional_info_id: Union[str, UUID]
    ):
        return self._delete_additional_info(
            agent_id=agent_id,
            additional_info_id=additional_info_id,
        )

    @beartype
    def get_tools(
        self,
        agent_id: Union[str, UUID],
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Tool]:
        return self._get_tools(
            agent_id=agent_id,
            limit=limit,
            offset=offset,
        ).items

    @beartype
    def create_tool(
        self,
        agent_id: Union[str, UUID],
        *,
        tool: ToolDict,
    ) -> ResourceCreatedResponse:
        return self._create_tool(
            agent_id=agent_id,
            tool=tool,
        )

    @beartype
    def update_tool(
        self,
        agent_id: Union[str, UUID],
        tool_id: Union[str, UUID],
        *,
        definition: FunctionDefDict,
    ) -> ResourceUpdatedResponse:
        return self._update_tool(
            agent_id=agent_id,
            tool_id=tool_id,
            definition=definition,
        )

    @beartype
    def delete_tool(
        self,
        agent_id: Union[str, UUID],
        tool_id: Union[str, UUID],
    ):
        return self._delete_tool(
            agent_id=agent_id,
            tool_id=tool_id,
        )

    @beartype
    def get_memories(
        self,
        agent_id: str,
        *,
        query: str,
        types: Optional[Union[str, List[str]]] = None,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Memory]:
        return self._get_memories(
            agent_id=agent_id,
            query=query,
            types=types,
            user_id=user_id,
            limit=limit,
            offset=offset,
        ).items


class AsyncAgentsManager(BaseAgentsManager):
    @beartype
    async def get(self, id: Union[UUID, str]) -> Agent:
        return await self._get(id=id)

    @beartype
    async def create(
        self,
        *,
        name: str,
        about: str,
        instructions: Union[List[str], List[InstructionDict]],
        tools: List[ToolDict] = [],
        functions: List[FunctionDefDict] = [],
        default_settings: DefaultSettingsDict = {},
        model: ModelName = "julep-ai/samantha-1-turbo",
        docs: List[DocDict] = [],
    ) -> ResourceCreatedResponse:
        return await self._create(
            name,
            about,
            instructions,
            tools,
            functions,
            default_settings,
            model,
            docs,
        )

    @beartype
    async def list(
        self,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Agent]:
        return (
            await self._list_items(
                limit=limit,
                offset=offset,
            )
        ).items

    @beartype
    async def delete(self, agent_id: Union[str, UUID]):
        return await self._delete(agent_id=agent_id)

    @beartype
    async def update(
        self,
        agent_id: Union[str, UUID],
        *,
        about: Optional[str] = None,
        instructions: Optional[Union[List[str], List[InstructionDict]]] = None,
        name: Optional[str] = None,
        model: Optional[str] = None,
        default_settings: Optional[DefaultSettingsDict] = None,
    ) -> ResourceUpdatedResponse:
        return await self._update(
            agent_id=agent_id,
            about=about,
            instructions=instructions,
            name=name,
            model=model,
            default_settings=default_settings,
        )

    @beartype
    async def get_additional_info(
        self,
        agent_id: Union[str, UUID],
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[AdditionalInfo]:
        return (
            await self._get_additional_info(
                agent_id=agent_id,
                limit=limit,
                offset=offset,
            )
        ).items

    @beartype
    async def create_additional_info(
        self,
        agent_id: Union[str, UUID],
        *,
        doc: DocDict,
    ) -> ResourceCreatedResponse:
        return await self._create_additional_info(
            agent_id=agent_id,
            doc=doc,
        )

    @beartype
    async def delete_additional_info(
        self, agent_id: Union[str, UUID], additional_info_id: Union[str, UUID]
    ):
        return await self._delete_additional_info(
            agent_id=agent_id,
            additional_info_id=additional_info_id,
        )

    @beartype
    async def get_tools(
        self,
        agent_id: Union[str, UUID],
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Tool]:
        return (
            await self._get_tools(
                agent_id=agent_id,
                limit=limit,
                offset=offset,
            )
        ).items

    @beartype
    async def create_tool(
        self,
        agent_id: Union[str, UUID],
        *,
        tool: ToolDict,
    ) -> ResourceCreatedResponse:
        return await self._create_tool(
            agent_id=agent_id,
            tool=tool,
        )

    @beartype
    async def update_tool(
        self,
        agent_id: Union[str, UUID],
        tool_id: Union[str, UUID],
        *,
        definition: FunctionDefDict,
    ) -> ResourceUpdatedResponse:
        return await self._update_tool(
            agent_id=agent_id,
            tool_id=tool_id,
            definition=definition,
        )

    @beartype
    async def delete_tool(
        self,
        agent_id: Union[str, UUID],
        tool_id: Union[str, UUID],
    ):
        return await self._delete_tool(
            agent_id=agent_id,
            tool_id=tool_id,
        )

    @beartype
    async def get_memories(
        self,
        agent_id: str,
        *,
        query: str,
        types: Optional[Union[str, List[str]]] = None,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Memory]:
        return (
            await self._get_memories(
                agent_id=agent_id,
                query=query,
                types=types,
                user_id=user_id,
                limit=limit,
                offset=offset,
            )
        ).items
