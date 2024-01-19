from uuid import UUID

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
