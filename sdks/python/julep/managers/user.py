import json
from uuid import UUID
from typing import Optional, TypedDict
from beartype import beartype
from beartype.typing import Any, Awaitable, Dict, List, Union

from .utils import rewrap_in_class, NotSet

from ..api.types import (
    User,
    CreateDoc,
    ResourceCreatedResponse,
    ResourceUpdatedResponse,
    ListUsersResponse,
)

from .base import BaseManager
from .utils import is_valid_uuid4
from .types import DocDict


class UserCreateArgs(TypedDict):
    name: str
    about: str
    docs: List[str] = []
    metadata: Dict[str, Any] = {}


class UserUpdateArgs(TypedDict):
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    about: Optional[str] = None
    overwrite: bool = False


class BaseUsersManager(BaseManager):
    """
    A manager class for handling user-related operations through an API client.

        This class provides high-level methods to interact with user records,
        such as retrieving a user by ID, creating a new user, listing all users,
        deleting a user, and updating a user's details.

        Attributes:
            api_client: The API client instance to communicate with the user service.

        Methods:
            _get: Retrieve a user by a unique UUID.
            _create: Create a new user with the specified name and about fields, and optionally additional documents.
            _list_items: List users with optional pagination through limit and offset parameters.
            _delete: Delete a user by UUID.
            _update: Update user details such as the 'about' description and name by UUID.

        Raises:
            AssertionError: If the provided ID for the user operations is not a valid UUID v4.
    """

    def _get(self, id: Union[str, UUID]) -> Union[User, Awaitable[User]]:
        """
        Get the user by their ID.

        This method is intended to retrieve a User object or an Awaitable User object by the user's unique identifier. The identifier can be a string representation of a UUID or a UUID object itself.

        Args:
            id (Union[str, UUID]): The unique identifier of the user to retrieve. It must be a valid UUID v4.

        Returns:
            Union[User, Awaitable[User]]: The retrieved User instance or an Awaitable that resolves to a User instance.

        Raises:
            AssertionError: If the `id` is not a valid UUID v4.

        Note:
            The leading underscore in the method name suggests that this method is intended for internal use and should not be a part of the public interface of the class.
        """
        assert is_valid_uuid4(id), "id must be a valid UUID v4"
        return self.api_client.get_user(user_id=id)

    def _create(
        self,
        name: str,
        about: str,
        docs: List[DocDict] = [],
        metadata: Dict[str, Any] = {},
    ) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]:
        # Cast docs to a list of CreateDoc objects
        """
        Create a new resource with the given name and about information, optionally including additional docs.

        This internal method allows for creating a new resource with optional docsrmation.

        Args:
            name (str): The name of the new resource.
            about (str): A brief description about the new resource.
            docs (List[DocDict], optional): A list of dictionaries with documentation-related information. Each dictionary
                must conform to the structure expected by CreateDoc. Defaults to an empty list.
            metadata (Dict[str, Any])

        Returns:
            Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]: The response indicating the resource has been
            created successfully. It can be either a synchronous ResourceCreatedResponse or an asynchronous Awaitable object
            containing a ResourceCreatedResponse.

        Note:
            This method is an internal API implementation detail and should not be used directly outside the defining class
            or module.

        Side effects:
            Modifies internal state by converting each doc dict to an instance of CreateDoc and uses the
            internal API client to create a new user resource.
        """
        docs: List[CreateDoc] = [CreateDoc(**doc) for doc in docs]

        return self.api_client.create_user(
            name=name,
            about=about,
            docs=docs,
            metadata=metadata,
        )

    def _list_items(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        metadata_filter: str = "{}",
    ) -> Union[ListUsersResponse, Awaitable[ListUsersResponse]]:
        """
        Fetch a list of users, with optional pagination parameters.

            Args:
                limit (Optional[int], optional): The maximum number of users to return. Defaults to None.
                offset (Optional[int], optional): The offset from the start of the list to begin returning users. Defaults to None.

            Returns:
                Union[ListUsersResponse, Awaitable[ListUsersResponse]]: An instance of ListUsersResponse,
                or an awaitable that will resolve to it, depending on the API client implementation.
        """
        return self.api_client.list_users(
            limit=limit,
            offset=offset,
            metadata_filter=metadata_filter,
        )

    def _delete(self, user_id: Union[str, UUID]) -> Union[None, Awaitable[None]]:
        """
        Delete a user given their user ID.

            Args:
                user_id (Union[str, UUID]): The identifier of the user. Must be a valid UUID version 4.

            Returns:
                Union[None, Awaitable[None]]: None if the deletion is synchronous, or an Awaitable
                that resolves to None if the deletion is asynchronous.

            Raises:
                AssertionError: If the user_id is not a valid UUID v4.
        """
        assert is_valid_uuid4(user_id), "id must be a valid UUID v4"
        return self.api_client.delete_user(user_id=user_id)

    def _update(
        self,
        user_id: Union[str, UUID],
        about: Optional[str] = NotSet,
        name: Optional[str] = NotSet,
        metadata: Dict[str, Any] = NotSet,
        overwrite: bool = False,
    ) -> Union[ResourceUpdatedResponse, Awaitable[ResourceUpdatedResponse]]:
        """
        Update user details for a given user ID.

        This method updates the 'about' and/or 'name' fields for the user identified by user_id.

        Args:
            user_id (Union[str, UUID]): The ID of the user to be updated. Must be a valid UUID v4.
            about (Optional[str], optional): The new information about the user. Defaults to None.
            name (Optional[str], optional): The new name for the user. Defaults to None.
            metadata (Dict[str, Any])
            overwrite (bool, optional): Whether to overwrite the existing user data. Defaults to False.

        Returns:
            Union[ResourceUpdatedResponse, Awaitable[ResourceUpdatedResponse]]: The response indicating successful update or an Awaitable that resolves to such a response.

        Raises:
            AssertionError: If `user_id` is not a valid UUID v4.
        """
        assert is_valid_uuid4(user_id), "id must be a valid UUID v4"

        updateFn = (
            self.api_client.update_user if overwrite else self.api_client.patch_user
        )

        update_data = dict(
            user_id=user_id,
            about=about,
            name=name,
            metadata=metadata,
        )

        update_data = {k: v for k, v in update_data.items() if v is not NotSet}

        if not update_data:
            raise ValueError("No fields to update")

        return updateFn(**update_data)


class UsersManager(BaseUsersManager):
    """
    A class responsible for managing users in a system.

    This class is a specialized version of the BaseUsersManager and provides
    methods for retrieving, creating, listing, deleting, and updating users within
    the system.

    Methods:
        get(id: Union[str, UUID]) -> User:
            Retrieves a user based on their unique identifier (either a string or UUID).

        create(*, name: str, about: str, docs: List[DocDict]=[]) -> ResourceCreatedResponse:
            Creates a new user with the specified name, description about the user,
            and an optional list of documents associated with the user.

        list(*, limit: Optional[int]=None, offset: Optional[int]=None) -> List[User]:
            Lists users in the system, with optional limit and offset for pagination.

        delete(*, user_id: Union[str, UUID]) -> None:
            Deletes a user from the system based on their unique identifier.

        update(*, user_id: Union[str, UUID], about: Optional[str]=None, name: Optional[str]=None) -> ResourceUpdatedResponse:
            Updates an existing user's information with optional new about and name
            fields.
    """

    @beartype
    def get(self, id: Union[str, UUID]) -> User:
        """
        Retrieve a User object by its identifier.

        The method supports retrieval by both string representations of a UUID and
        UUID objects directly.

        Args:
            id (Union[str, UUID]): The identifier of the User, can be a string or UUID.

        Returns:
            User: The User object associated with the provided id.

        Raises:
            ValueError: If 'id' is neither a string nor a UUID.
            NotFoundError: If a User with the given 'id' does not exist.
        """
        return self._get(id=id)

    @beartype
    @rewrap_in_class(User)
    def create(self, **kwargs: UserCreateArgs) -> User:
        """
        Create a new resource with the specified name, about text, and associated docs.

            Args:
                name (str): The name of the resource to create.
                about (str): A brief description of the resource.
                docs (List[DocDict], optional): A list of dictionaries representing the documents associated with the resource. Defaults to an empty list.

            Returns:
                ResourceCreatedResponse: An object representing the response received upon the successful creation of the resource.

            Note:
                Using mutable types like list as default argument values in Python is risky because if the list is modified,
                those changes will persist across subsequent calls to the function which use the default value. It is
                generally safer to use `None` as a default value and then set the default inside the function if needed.

            Raises:
                BeartypeException: If the input types do not match the specified function annotations.
        """
        result = self._create(**kwargs)
        return result

    @beartype
    def list(
        self,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        metadata_filter: Dict[str, Any] = {},
    ) -> List[User]:
        """
        Lists the users optionally applying limit and offset.

        Args:
            limit (Optional[int], optional): The maximum number of users to return.
                None means no limit. Defaults to None.
            offset (Optional[int], optional): The index of the first user to return.
                None means start from the beginning. Defaults to None.

        Returns:
            List[User]: A list of user objects.

        Raises:
            BeartypeException: If the type of `limit` or `offset` is not as expected.
        """
        metadata_filter_string = json.dumps(metadata_filter)

        return self._list_items(
            limit=limit,
            offset=offset,
            metadata_filter=metadata_filter_string,
        ).items

    @beartype
    def delete(
        self,
        user_id: Union[str, UUID],
    ) -> None:
        """
        Deletes a user based on the provided user ID.

        Args:
            user_id (Union[str, UUID]): Unique identifier of the user.

        Returns:
            None

        Note:
            This function is type-checked with `beartype` to ensure that the `user_id`
            parameter matches either a string or a UUID type.

        Raises:
            The specific exceptions raised depend on the implementation of the `_delete`
            method this function proxies to.
        """
        return self._delete(
            user_id=user_id,
        )

    @beartype
    @rewrap_in_class(User)
    def update(self, *, user_id: Union[str, UUID], **kwargs: UserUpdateArgs) -> User:
        """
        Update user information.

        This method updates user details such as the `about` text and user's `name` for a given `user_id`.

        Args:
            user_id (Union[str, UUID]): The unique identifier for the user, which can be a string or a UUID object.
            about(Optional[str], optional): The descriptive information about the user. Defaults to None, indicating that `about` should not be updated if not provided.
            name(Optional[str], optional): The name of the user. Defaults to None, indicating that `name` should not be updated if not provided.
            overwrite(bool, optional): Whether to overwrite the existing user data. Defaults to False.

        Returns:
            ResourceUpdatedResponse: An object indicating the outcome of the update operation, which typically includes the status of the operation and possibly the updated resource data.
        """
        result = self._update(user_id=user_id, **kwargs)
        return result


class AsyncUsersManager(BaseUsersManager):
    """
    A class that provides asynchronous management of users extending BaseUsersManager.

    Attributes are inherited from BaseUsersManager.

    Methods:
        get (Union[UUID, str]) -> User:
            Asynchronously retrieves a user by their unique identifier (either a UUID or a string).

        create (*, name: str, about: str, docs: List[DocDict]=[]) -> ResourceCreatedResponse:
            Asynchronously creates a new user with the given name, about description, and optional list of documents.

        list (*, limit: Optional[int]=None, offset: Optional[int]=None) -> List[User]:
            Asynchronously retrieves a list of users with an optional limit and offset for pagination.

        delete (*, user_id: Union[str, UUID]) -> None:
            Asynchronously deletes a user identified by their unique ID (either a string or a UUID).

        update (*, user_id: Union[str, UUID], about: Optional[str]=None, name: Optional[str]=None) -> ResourceUpdatedResponse:
            Asynchronously updates a user's information identified by their unique ID with optional new about description and name.

    Note:
        The beartype decorator is used for runtime type checking of the parameters passed to the methods.
    """

    @beartype
    async def get(self, id: Union[UUID, str]) -> User:
        """
        Fetch a User object asynchronously by its identifier.

        This method retrieves a User object from some data storage asynchronously based on the provided identifier, which can be either a UUID or a string.

        Args:
            id (Union[UUID, str]): The unique identifier of the User to be retrieved.

        Returns:
            User: An instance of the User class corresponding to the given id.

        Raises:
            Exception: If the retrieval fails or the user cannot be found.
        """
        return await self._get(id=id)

    @beartype
    @rewrap_in_class(User)
    async def create(self, **kwargs: UserCreateArgs) -> User:
        """
        Asynchronously create a new resource with the provided name, description, and documents.

        This function is decorated with `@beartype` to ensure type checking at runtime.

        Args:
            name (str): The name of the resource to be created.
            about (str): Brief information about the resource.
            docs (List[DocDict], optional): A list of document dictionaries with structure defined by DocDict type.

        Returns:
            ResourceCreatedResponse: An instance representing the response after resource creation.

        Raises:
            BeartypeException: If any of the parameters do not match their annotated types.
        """
        result = await self._create(**kwargs)
        return result

    @beartype
    async def list(
        self,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        metadata_filter: Dict[str, Any] = {},
    ) -> List[User]:
        """
        Asynchronously lists users with optional limits and offsets.

        This function applies the `beartype` decorator for runtime type checking.

        Args:
            limit (Optional[int], optional): The maximum number of users to be returned. Defaults to None, which means no limit.
            offset (Optional[int], optional): The number to offset the list of returned users by. Defaults to None, which means no offset.

        Returns:
            List[User]: A list of user objects.

        Raises:
            TypeError: If any input arguments are not of the expected type.
            Any other exception that might be raised during the retrieval of users from the data source.

        Note:
            The actual exception raised by the `beartype` decorator or during the users' retrieval will depend on the implementation detail of the `self._list_items` method and the `beartype` configuration.
        """
        metadata_filter_string = json.dumps(metadata_filter)

        return (
            await self._list_items(
                limit,
                offset,
                metadata_filter=metadata_filter_string,
            )
        ).items

    @beartype
    async def delete(
        self,
        user_id: Union[str, UUID],
    ) -> None:
        """
        Asynchronously deletes a user by their user ID.

        Args:
            user_id (Union[str, UUID]): The unique identifier of the user to delete, which can be a string or a UUID.

        Returns:
            None: This function does not return anything.

        Notes:
            - The function is decorated with `@beartype` for runtime type checking.
            - This function is a coroutine, it should be called with `await`.

        Raises:
            - The raised exceptions depend on the implementation of the underlying `_delete` coroutine.
        """
        return await self._delete(
            user_id=user_id,
        )

    @beartype
    @rewrap_in_class(User)
    async def update(
        self, *, user_id: Union[str, UUID], **kwargs: UserUpdateArgs
    ) -> User:
        """
        Asynchronously updates user details.

        This function updates user details such as 'about' and 'name'. It uses type annotations to enforce the types of the parameters and an asynchronous call to '_update' method to perform the actual update operation.

        Args:
            user_id (Union[str, UUID]): The unique identifier of the user, which can be either a string or a UUID.
            about (Optional[str], optional): A description of the user. Default is None, indicating no update.
            name (Optional[str], optional): The name of the user. Default is None, indicating no update.

        Returns:
            ResourceUpdatedResponse: An object representing the update status.

        Note:
            This function is decorated with @beartype to perform runtime type checking.
        """
        result = await self._update(user_id=user_id, **kwargs)
        return result
