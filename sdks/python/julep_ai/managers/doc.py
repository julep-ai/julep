from uuid import UUID

from typing import Optional
from beartype import beartype
from beartype.typing import Awaitable, List, Union

from ..api.types import (
    CreateAdditionalInfoRequest,
    ResourceCreatedResponse,
    GetAgentAdditionalInfoResponse,
    AdditionalInfo as Doc,
)

from .base import BaseManager
from .utils import is_valid_uuid4
from .types import DocDict


class BaseDocsManager(BaseManager):
    def _get(
        self,
        agent_id: Optional[Union[str, UUID]],
        user_id: Optional[Union[str, UUID]],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Union[
        GetAgentAdditionalInfoResponse, Awaitable[GetAgentAdditionalInfoResponse]
    ]:
        assert (
            (agent_id and is_valid_uuid4(agent_id))
            or (user_id and is_valid_uuid4(user_id))
            and not (agent_id and user_id)
        ), "One and only one of user_id or agent_id must be given and must be valid UUID v4"

        if agent_id is not None:
            return self.api_client.get_agent_additional_info(
                agent_id=agent_id,
                limit=limit,
                offset=offset,
            )

        if user_id is not None:
            return self.api_client.get_user_additional_info(
                user_id=user_id,
                limit=limit,
                offset=offset,
            )

    def _create(
        self,
        agent_id: Optional[Union[str, UUID]],
        user_id: Optional[Union[str, UUID]],
        doc: DocDict,
    ) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]:
        assert (
            (agent_id and is_valid_uuid4(agent_id))
            or (user_id and is_valid_uuid4(user_id))
            and not (agent_id and user_id)
        ), "One and only one of user_id or agent_id must be given and must be valid UUID v4"

        doc: CreateAdditionalInfoRequest = CreateAdditionalInfoRequest(**doc)

        if agent_id is not None:
            return self.api_client.create_agent_additional_info(
                agent_id=agent_id,
                request=doc,
            )

        if user_id is not None:
            return self.api_client.create_user_additional_info(
                user_id=user_id,
                request=doc,
            )

    def _delete(
        self,
        agent_id: Optional[Union[str, UUID]],
        user_id: Optional[Union[str, UUID]],
        doc_id: Union[str, UUID],
    ):
        assert (
            (agent_id and is_valid_uuid4(agent_id))
            or (user_id and is_valid_uuid4(user_id))
            and not (agent_id and user_id)
        ), "One and only one of user_id or agent_id must be given and must be valid UUID v4"

        if agent_id is not None:
            return self.api_client.delete_agent_additional_info(
                agent_id=agent_id,
                additional_info_id=doc_id,
            )

        if user_id is not None:
            return self.api_client.delete_user_additional_info(
                user_id=user_id,
                additional_info_id=doc_id,
            )


class DocsManager(BaseDocsManager):
    @beartype
    def get(
        self,
        *,
        agent_id: Optional[Union[str, UUID]] = None,
        user_id: Optional[Union[str, UUID]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Doc]:
        return self._get(
            agent_id=agent_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
        ).items

    @beartype
    def create(
        self,
        *,
        agent_id: Optional[Union[str, UUID]] = None,
        user_id: Optional[Union[str, UUID]] = None,
        doc: DocDict,
    ) -> ResourceCreatedResponse:
        return self._create(
            agent_id=agent_id,
            user_id=user_id,
            doc=doc,
        )

    @beartype
    def delete(
        self,
        *,
        doc_id: Union[str, UUID],
        agent_id: Optional[Union[str, UUID]] = None,
        user_id: Optional[Union[str, UUID]] = None,
    ):
        return self._delete(
            agent_id=agent_id,
            user_id=user_id,
            doc_id=doc_id,
        )


class AsyncDocsManager(BaseDocsManager):
    @beartype
    async def get(
        self,
        *,
        agent_id: Optional[Union[str, UUID]] = None,
        user_id: Optional[Union[str, UUID]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Doc]:
        return (
            await self._get(
                agent_id=agent_id,
                user_id=user_id,
                limit=limit,
                offset=offset,
            )
        ).items

    @beartype
    async def create(
        self,
        *,
        agent_id: Optional[Union[str, UUID]] = None,
        user_id: Optional[Union[str, UUID]] = None,
        doc: DocDict,
    ) -> ResourceCreatedResponse:
        return await self._create(
            agent_id=agent_id,
            user_id=user_id,
            doc=doc,
        )

    @beartype
    async def delete(
        self,
        *,
        doc_id: Union[str, UUID],
        agent_id: Optional[Union[str, UUID]] = None,
        user_id: Optional[Union[str, UUID]] = None,
    ):
        return await self._delete(
            agent_id=agent_id,
            user_id=user_id,
            doc_id=doc_id,
        )
