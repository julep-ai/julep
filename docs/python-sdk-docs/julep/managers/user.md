# User

[Julep Python SDK Index](../../README.md#julep-python-sdk-index) / [Julep](../index.md#julep) / [Managers](./index.md#managers) / User

> Auto-generated documentation for [julep.managers.user](../../../../../../julep/managers/user.py) module.

- [User](#user)
  - [AsyncUsersManager](#asyncusersmanager)
  - [BaseUsersManager](#baseusersmanager)
  - [UserCreateArgs](#usercreateargs)
  - [UserUpdateArgs](#userupdateargs)
  - [UsersManager](#usersmanager)

## AsyncUsersManager

[Show source in user.py:358](../../../../../../julep/managers/user.py#L358)

A class that provides asynchronous management of users extending BaseUsersManager.

Attributes are inherited from BaseUsersManager.

#### Methods

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

#### Notes

The beartype decorator is used for runtime type checking of the parameters passed to the methods.

#### Signature

```python
class AsyncUsersManager(BaseUsersManager): ...
```

#### See also

- [BaseUsersManager](#baseusersmanager)

### AsyncUsersManager().create

[Show source in user.py:402](../../../../../../julep/managers/user.py#L402)

Asynchronously create a new resource with the provided name, description, and documents.

This function is decorated with `@beartype` to ensure type checking at runtime.

#### Arguments

- `name` *str* - The name of the resource to be created.
- `about` *str* - Brief information about the resource.
- `docs` *List[DocDict], optional* - A list of document dictionaries with structure defined by DocDict type.

#### Returns

- `ResourceCreatedResponse` - An instance representing the response after resource creation.

#### Raises

- `BeartypeException` - If any of the parameters do not match their annotated types.

#### Signature

```python
@beartype
@rewrap_in_class(User)
async def create(self, **kwargs: UserCreateArgs) -> User: ...
```

#### See also

- [UserCreateArgs](#usercreateargs)

### AsyncUsersManager().delete

[Show source in user.py:461](../../../../../../julep/managers/user.py#L461)

Asynchronously deletes a user by their user ID.

#### Arguments

user_id (Union[str, UUID]): The unique identifier of the user to delete, which can be a string or a UUID.

#### Returns

- `None` - This function does not return anything.

#### Notes

- The function is decorated with `@beartype` for runtime type checking.
- This function is a coroutine, it should be called with `await`.

#### Raises

- The raised exceptions depend on the implementation of the underlying `_delete` coroutine.

#### Signature

```python
@beartype
async def delete(self, user_id: Union[str, UUID]) -> None: ...
```

### AsyncUsersManager().get

[Show source in user.py:384](../../../../../../julep/managers/user.py#L384)

Fetch a User object asynchronously by its identifier.

This method retrieves a User object from some data storage asynchronously based on the provided identifier, which can be either a UUID or a string.

#### Arguments

id (Union[UUID, str]): The unique identifier of the User to be retrieved.

#### Returns

- `User` - An instance of the User class corresponding to the given id.

#### Raises

- `Exception` - If the retrieval fails or the user cannot be found.

#### Signature

```python
@beartype
async def get(self, id: Union[UUID, str]) -> User: ...
```

### AsyncUsersManager().list

[Show source in user.py:424](../../../../../../julep/managers/user.py#L424)

Asynchronously lists users with optional limits and offsets.

This function applies the `beartype` decorator for runtime type checking.

#### Arguments

- `limit` *Optional[int], optional* - The maximum number of users to be returned. Defaults to None, which means no limit.
- `offset` *Optional[int], optional* - The number to offset the list of returned users by. Defaults to None, which means no offset.

#### Returns

- `List[User]` - A list of user objects.

#### Raises

- `TypeError` - If any input arguments are not of the expected type.
Any other exception that might be raised during the retrieval of users from the data source.

#### Notes

The actual exception raised by the `beartype` decorator or during the users' retrieval will depend on the implementation detail of the `self._list_items` method and the `beartype` configuration.

#### Signature

```python
@beartype
async def list(
    self,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    metadata_filter: Dict[str, Any] = {},
) -> List[User]: ...
```

### AsyncUsersManager().update

[Show source in user.py:486](../../../../../../julep/managers/user.py#L486)

Asynchronously updates user details.

This function updates user details such as 'about' and 'name'. It uses type annotations to enforce the types of the parameters and an asynchronous call to '_update' method to perform the actual update operation.

#### Arguments

user_id (Union[str, UUID]): The unique identifier of the user, which can be either a string or a UUID.
- `about` *Optional[str], optional* - A description of the user. Default is None, indicating no update.
- `name` *Optional[str], optional* - The name of the user. Default is None, indicating no update.

#### Returns

- `ResourceUpdatedResponse` - An object representing the update status.

#### Notes

This function is decorated with @beartype to perform runtime type checking.

#### Signature

```python
@beartype
@rewrap_in_class(User)
async def update(self, user_id: Union[str, UUID], **kwargs: UserUpdateArgs) -> User: ...
```

#### See also

- [UserUpdateArgs](#userupdateargs)



## BaseUsersManager

[Show source in user.py:36](../../../../../../julep/managers/user.py#L36)

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

#### Signature

```python
class BaseUsersManager(BaseManager): ...
```

### BaseUsersManager()._create

[Show source in user.py:79](../../../../../../julep/managers/user.py#L79)

Create a new resource with the given name and about information, optionally including additional docs.

This internal method allows for creating a new resource with optional docsrmation.

#### Arguments

- `name` *str* - The name of the new resource.
- `about` *str* - A brief description about the new resource.
- `docs` *List[DocDict], optional* - A list of dictionaries with documentation-related information. Each dictionary
    must conform to the structure expected by CreateDoc. Defaults to an empty list.
metadata (Dict[str, Any])

#### Returns

- `Union[ResourceCreatedResponse,` *Awaitable[ResourceCreatedResponse]]* - The response indicating the resource has been
created successfully. It can be either a synchronous ResourceCreatedResponse or an asynchronous Awaitable object
containing a ResourceCreatedResponse.

#### Notes

This method is an internal API implementation detail and should not be used directly outside the defining class
or module.

Side effects:
    Modifies internal state by converting each doc dict to an instance of CreateDoc and uses the
    internal API client to create a new user resource.

#### Signature

```python
def _create(
    self, name: str, about: str, docs: List[DocDict] = [], metadata: Dict[str, Any] = {}
) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]: ...
```

### BaseUsersManager()._delete

[Show source in user.py:144](../../../../../../julep/managers/user.py#L144)

Delete a user given their user ID.

Args:
    user_id (Union[str, UUID]): The identifier of the user. Must be a valid UUID version 4.

Returns:
    Union[None, Awaitable[None]]: None if the deletion is synchronous, or an Awaitable
    that resolves to None if the deletion is asynchronous.

Raises:
    AssertionError: If the user_id is not a valid UUID v4.

#### Signature

```python
def _delete(self, user_id: Union[str, UUID]) -> Union[None, Awaitable[None]]: ...
```

### BaseUsersManager()._get

[Show source in user.py:58](../../../../../../julep/managers/user.py#L58)

Get the user by their ID.

This method is intended to retrieve a User object or an Awaitable User object by the user's unique identifier. The identifier can be a string representation of a UUID or a UUID object itself.

#### Arguments

id (Union[str, UUID]): The unique identifier of the user to retrieve. It must be a valid UUID v4.

#### Returns

- `Union[User,` *Awaitable[User]]* - The retrieved User instance or an Awaitable that resolves to a User instance.

#### Raises

- `AssertionError` - If the `id` is not a valid UUID v4.

#### Notes

The leading underscore in the method name suggests that this method is intended for internal use and should not be a part of the public interface of the class.

#### Signature

```python
def _get(self, id: Union[str, UUID]) -> Union[User, Awaitable[User]]: ...
```

### BaseUsersManager()._list_items

[Show source in user.py:121](../../../../../../julep/managers/user.py#L121)

Fetch a list of users, with optional pagination parameters.

Args:
    limit (Optional[int], optional): The maximum number of users to return. Defaults to None.
    offset (Optional[int], optional): The offset from the start of the list to begin returning users. Defaults to None.

Returns:
    Union[ListUsersResponse, Awaitable[ListUsersResponse]]: An instance of ListUsersResponse,
    or an awaitable that will resolve to it, depending on the API client implementation.

#### Signature

```python
def _list_items(
    self,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    metadata_filter: str = "{}",
) -> Union[ListUsersResponse, Awaitable[ListUsersResponse]]: ...
```

### BaseUsersManager()._update

[Show source in user.py:161](../../../../../../julep/managers/user.py#L161)

Update user details for a given user ID.

This method updates the 'about' and/or 'name' fields for the user identified by user_id.

#### Arguments

user_id (Union[str, UUID]): The ID of the user to be updated. Must be a valid UUID v4.
- `about` *Optional[str], optional* - The new information about the user. Defaults to None.
- `name` *Optional[str], optional* - The new name for the user. Defaults to None.
metadata (Dict[str, Any])
- `overwrite` *bool, optional* - Whether to overwrite the existing user data. Defaults to False.

#### Returns

- `Union[ResourceUpdatedResponse,` *Awaitable[ResourceUpdatedResponse]]* - The response indicating successful update or an Awaitable that resolves to such a response.

#### Raises

- `AssertionError` - If `user_id` is not a valid UUID v4.

#### Signature

```python
def _update(
    self,
    user_id: Union[str, UUID],
    about: Optional[str] = NotSet,
    name: Optional[str] = NotSet,
    metadata: Dict[str, Any] = NotSet,
    overwrite: bool = False,
) -> Union[ResourceUpdatedResponse, Awaitable[ResourceUpdatedResponse]]: ...
```



## UserCreateArgs

[Show source in user.py:22](../../../../../../julep/managers/user.py#L22)

#### Signature

```python
class UserCreateArgs(TypedDict): ...
```



## UserUpdateArgs

[Show source in user.py:29](../../../../../../julep/managers/user.py#L29)

#### Signature

```python
class UserUpdateArgs(TypedDict): ...
```



## UsersManager

[Show source in user.py:208](../../../../../../julep/managers/user.py#L208)

A class responsible for managing users in a system.

This class is a specialized version of the BaseUsersManager and provides
methods for retrieving, creating, listing, deleting, and updating users within
the system.

#### Methods

- `get(id` - Union[str, UUID]) -> User:
    Retrieves a user based on their unique identifier (either a string or UUID).

- `create(*,` *name* - str, about: str, docs: List[DocDict]=[]) -> ResourceCreatedResponse:
    Creates a new user with the specified name, description about the user,
    and an optional list of documents associated with the user.

- `list(*,` *limit* - Optional[int]=None, offset: Optional[int]=None) -> List[User]:
    Lists users in the system, with optional limit and offset for pagination.

- `delete(*,` *user_id* - Union[str, UUID]) -> None:
    Deletes a user from the system based on their unique identifier.

- `update(*,` *user_id* - Union[str, UUID], about: Optional[str]=None, name: Optional[str]=None) -> ResourceUpdatedResponse:
    Updates an existing user's information with optional new about and name
    fields.

#### Signature

```python
class UsersManager(BaseUsersManager): ...
```

#### See also

- [BaseUsersManager](#baseusersmanager)

### UsersManager().create

[Show source in user.py:255](../../../../../../julep/managers/user.py#L255)

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

#### Signature

```python
@beartype
@rewrap_in_class(User)
def create(self, **kwargs: UserCreateArgs) -> User: ...
```

#### See also

- [UserCreateArgs](#usercreateargs)

### UsersManager().delete

[Show source in user.py:311](../../../../../../julep/managers/user.py#L311)

Deletes a user based on the provided user ID.

#### Arguments

user_id (Union[str, UUID]): Unique identifier of the user.

#### Returns

None

#### Notes

This function is type-checked with `beartype` to ensure that the `user_id`
parameter matches either a string or a UUID type.

#### Raises

The specific exceptions raised depend on the implementation of the `_delete`
method this function proxies to.

#### Signature

```python
@beartype
def delete(self, user_id: Union[str, UUID]) -> None: ...
```

### UsersManager().get

[Show source in user.py:235](../../../../../../julep/managers/user.py#L235)

Retrieve a User object by its identifier.

The method supports retrieval by both string representations of a UUID and
UUID objects directly.

#### Arguments

id (Union[str, UUID]): The identifier of the User, can be a string or UUID.

#### Returns

- `User` - The User object associated with the provided id.

#### Raises

- `ValueError` - If 'id' is neither a string nor a UUID.
- `NotFoundError` - If a User with the given 'id' does not exist.

#### Signature

```python
@beartype
def get(self, id: Union[str, UUID]) -> User: ...
```

### UsersManager().list

[Show source in user.py:280](../../../../../../julep/managers/user.py#L280)

Lists the users optionally applying limit and offset.

#### Arguments

- `limit` *Optional[int], optional* - The maximum number of users to return.
    None means no limit. Defaults to None.
- `offset` *Optional[int], optional* - The index of the first user to return.
    None means start from the beginning. Defaults to None.

#### Returns

- `List[User]` - A list of user objects.

#### Raises

- `BeartypeException` - If the type of `limit` or `offset` is not as expected.

#### Signature

```python
@beartype
def list(
    self,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    metadata_filter: Dict[str, Any] = {},
) -> List[User]: ...
```

### UsersManager().update

[Show source in user.py:337](../../../../../../julep/managers/user.py#L337)

Update user information.

This method updates user details such as the `about` text and user's `name` for a given `user_id`.

#### Arguments

user_id (Union[str, UUID]): The unique identifier for the user, which can be a string or a UUID object.
- `about(Optional[str],` *optional)* - The descriptive information about the user. Defaults to None, indicating that `about` should not be updated if not provided.
- `name(Optional[str],` *optional)* - The name of the user. Defaults to None, indicating that `name` should not be updated if not provided.
- `overwrite(bool,` *optional)* - Whether to overwrite the existing user data. Defaults to False.

#### Returns

- `ResourceUpdatedResponse` - An object indicating the outcome of the update operation, which typically includes the status of the operation and possibly the updated resource data.

#### Signature

```python
@beartype
@rewrap_in_class(User)
def update(self, user_id: Union[str, UUID], **kwargs: UserUpdateArgs) -> User: ...
```

#### See also

- [UserUpdateArgs](#userupdateargs)