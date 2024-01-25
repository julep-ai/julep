from uuid import UUID

from typing import Optional
from beartype import beartype
from beartype.typing import Awaitable, List, Literal, Union

from ..api.types import (
    Agent,
    AgentDefaultSettings,
    CreateAdditionalInfoRequest,
    CreateToolRequest,
    Instruction,
    ResourceCreatedResponse,
    ListAgentsResponse,
    ResourceUpdatedResponse,
)

from .base import BaseManager
from .utils import is_valid_uuid4
from .types import (
    ToolDict,
    FunctionDefDict,
    DefaultSettingsDict,
    DocDict,
    InstructionDict,
)


###########
## TYPES ##
###########

ModelName = Literal[
    "julep-ai/samantha-1",
    "julep-ai/samantha-1-turbo",
]


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
        *,
        agent_id: Union[str, UUID],
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
        *,
        agent_id: Union[str, UUID],
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
