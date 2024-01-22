from uuid import UUID
from typing import Optional

from beartype import beartype
from beartype.typing import Awaitable, List, Union

from ..api.types import (
    User,
    CreateAdditionalInfoRequest,
    ResourceCreatedResponse,
    ResourceUpdatedResponse,
    ListUsersResponse,
)

from .base import BaseManager
from .utils import is_valid_uuid4
from .types import DocDict


class BaseUsersManager(BaseManager):
    def _get(self, id: Union[str, UUID]) -> Union[User, Awaitable[User]]:
        assert is_valid_uuid4(id), "id must be a valid UUID v4"
        return self.api_client.get_user(user_id=id)

    def _create(
        self,
        name: str,
        about: str,
        docs: List[DocDict] = [],
    ) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]:
        # Cast docs to a list of CreateAdditionalInfoRequest objects
        docs: List[CreateAdditionalInfoRequest] = [
            CreateAdditionalInfoRequest(**doc) for doc in docs
        ]

        return self.api_client.create_user(
            name=name,
            about=about,
            additional_information=docs,
        )

    def _list_items(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> Union[ListUsersResponse, Awaitable[ListUsersResponse]]:
        return self.api_client.list_users(
            limit=limit,
            offset=offset,
        )

    def _delete(self, user_id: Union[str, UUID]) -> Union[None, Awaitable[None]]:
        assert is_valid_uuid4(user_id), "id must be a valid UUID v4"
        return self.api_client.delete_user(user_id=user_id)

    def _update(
        self,
        user_id: Union[str, UUID],
        about: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Union[ResourceUpdatedResponse, Awaitable[ResourceUpdatedResponse]]:
        assert is_valid_uuid4(user_id), "id must be a valid UUID v4"
        return self.api_client.update_user(
            user_id=user_id,
            about=about,
            name=name,
        )


class UsersManager(BaseUsersManager):
    @beartype
    def get(self, id: Union[str, UUID]) -> User:
        return self._get(id=id)

    @beartype
    def create(
        self,
        *,
        name: str,
        about: str,
        docs: List[DocDict] = [],
    ) -> ResourceCreatedResponse:
        return self._create(
            name,
            about,
            docs,
        )

    @beartype
    def list(
        self,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[User]:
        return self._list_items(
            limit=limit,
            offset=offset,
        ).items

    @beartype
    def delete(
        self,
        *,
        user_id: Union[str, UUID],
    ) -> None:
        return self._delete(
            user_id=user_id,
        )

    @beartype
    def update(
        self,
        *,
        user_id: Union[str, UUID],
        about: Optional[str] = None,
        name: Optional[str] = None,
    ) -> ResourceUpdatedResponse:
        return self._update(
            user_id=user_id,
            about=about,
            name=name,
        )


class AsyncUsersManager(BaseUsersManager):
    @beartype
    async def get(self, id: Union[UUID, str]) -> User:
        return await self._get(id=id)

    @beartype
    async def create(
        self,
        *,
        name: str,
        about: str,
        docs: List[DocDict] = [],
    ) -> ResourceCreatedResponse:
        return await self._create(
            name,
            about,
            docs,
        )

    @beartype
    async def list(
        self,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[User]:
        return (
            await self._list_items(
                limit,
                offset,
            )
        ).items

    @beartype
    async def delete(
        self,
        *,
        user_id: Union[str, UUID],
    ) -> None:
        return await self._delete(
            user_id=user_id,
        )

    @beartype
    async def update(
        self,
        *,
        user_id: Union[str, UUID],
        about: Optional[str] = None,
        name: Optional[str] = None,
    ) -> ResourceUpdatedResponse:
        return await self._update(
            user_id=user_id,
            about=about,
            name=name,
        )
