from uuid import UUID

from typing import Optional
from beartype import beartype
from beartype.typing import Awaitable, List, Union

from ..api.types import (
    ResourceCreatedResponse,
    FunctionDef,
    GetAgentToolsResponse,
    CreateToolRequest,
    ResourceUpdatedResponse,
    Tool,
)

from .base import BaseManager
from .utils import is_valid_uuid4
from .types import ToolDict, FunctionDefDict


class BaseToolsManager(BaseManager):
    def _get(
        self,
        agent_id: Union[str, UUID],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Union[GetAgentToolsResponse, Awaitable[GetAgentToolsResponse]]:
        assert is_valid_uuid4(agent_id), "agent_id must be a valid UUID v4"

        return self.api_client.get_agent_tools(
            agent_id=agent_id, limit=limit, offset=offset
        )

    def _create(
        self,
        agent_id: Union[str, UUID],
        tool: ToolDict,
    ) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]:
        assert is_valid_uuid4(agent_id), "agent_id must be a valid UUID v4"

        tool: CreateToolRequest = CreateToolRequest(**tool)

        return self.api_client.create_agent_tool(
            agent_id=agent_id,
            request=tool,
        )

    def _update(
        self,
        agent_id: Union[str, UUID],
        tool_id: Union[str, UUID],
        definition: FunctionDefDict,
    ) -> Union[ResourceUpdatedResponse, Awaitable[ResourceUpdatedResponse]]:
        assert is_valid_uuid4(agent_id) and is_valid_uuid4(
            tool_id
        ), "agent_id and tool_id must be a valid UUID v4"

        definition: FunctionDef = FunctionDef(**definition)

        return self.api_client.update_agent_tool(
            agent_id=agent_id,
            tool_id=tool_id,
            definition=definition,
        )

    def _delete(
        self,
        agent_id: Union[str, UUID],
        tool_id: Union[str, UUID],
    ):
        assert is_valid_uuid4(agent_id) and is_valid_uuid4(
            tool_id
        ), "agent_id and tool_id must be a valid UUID v4"

        return self.api_client.delete_agent_tool(
            agent_id=agent_id,
            tool_id=tool_id,
        )


class ToolsManager(BaseToolsManager):
    @beartype
    def get(
        self,
        *,
        agent_id: Union[str, UUID],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Tool]:
        return self._get(
            agent_id=agent_id,
            limit=limit,
            offset=offset,
        ).items

    @beartype
    def create(
        self,
        *,
        agent_id: Union[str, UUID],
        tool: ToolDict,
    ) -> ResourceCreatedResponse:
        return self._create(
            agent_id=agent_id,
            tool=tool,
        )

    @beartype
    def delete(
        self,
        *,
        agent_id: Union[str, UUID],
        tool_id: Union[str, UUID],
    ):
        return self._delete(
            agent_id=agent_id,
            tool_id=tool_id,
        )

    @beartype
    def update(
        self,
        *,
        agent_id: Union[str, UUID],
        tool_id: Union[str, UUID],
        definition: FunctionDefDict,
    ) -> ResourceUpdatedResponse:
        return self._update(
            agent_id=agent_id,
            tool_id=tool_id,
            definition=definition,
        )


class AsyncToolsManager(BaseToolsManager):
    @beartype
    async def get(
        self,
        *,
        agent_id: Union[str, UUID],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Tool]:
        return (
            await self._get(
                agent_id=agent_id,
                limit=limit,
                offset=offset,
            )
        ).items

    @beartype
    async def create(
        self,
        *,
        agent_id: Union[str, UUID],
        tool: ToolDict,
    ) -> ResourceCreatedResponse:
        return await self._create(
            agent_id=agent_id,
            tool=tool,
        )

    @beartype
    async def delete(
        self,
        *,
        agent_id: Union[str, UUID],
        tool_id: Union[str, UUID],
    ):
        return await self._delete(
            agent_id=agent_id,
            tool_id=tool_id,
        )

    @beartype
    async def update(
        self,
        *,
        agent_id: Union[str, UUID],
        tool_id: Union[str, UUID],
        definition: FunctionDefDict,
    ) -> ResourceUpdatedResponse:
        return await self._update(
            agent_id=agent_id,
            tool_id=tool_id,
            definition=definition,
        )
