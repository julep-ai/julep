from uuid import UUID

from typing import Optional
from beartype import beartype
from beartype.typing import Awaitable, List, Union

from ..api.types import (
    Memory,
    GetAgentMemoriesResponse,
)

from .base import BaseManager
from .utils import is_valid_uuid4


class BaseMemoriesManager(BaseManager):
    def _list(
        self,
        agent_id: str,
        query: str,
        types: Optional[Union[str, List[str]]] = None,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Union[GetAgentMemoriesResponse, Awaitable[GetAgentMemoriesResponse]]:
        assert is_valid_uuid4(agent_id), "agent_id must be a valid UUID v4"

        return self.api_client.get_agent_memories(
            agent_id=agent_id,
            query=query,
            types=types,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )


class MemoriesManager(BaseMemoriesManager):
    @beartype
    def list(
        self,
        *,
        agent_id: Union[str, UUID],
        query: str,
        types: Optional[Union[str, List[str]]] = None,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Memory]:
        return self._list(
            agent_id=agent_id,
            query=query,
            types=types,
            user_id=user_id,
            limit=limit,
            offset=offset,
        ).items


class AsyncMemoriesManager(BaseMemoriesManager):
    @beartype
    async def list(
        self,
        *,
        agent_id: Union[str, UUID],
        query: str,
        types: Optional[Union[str, List[str]]] = None,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Memory]:
        return (
            await self._list(
                agent_id=agent_id,
                query=query,
                types=types,
                user_id=user_id,
                limit=limit,
                offset=offset,
            )
        ).items
