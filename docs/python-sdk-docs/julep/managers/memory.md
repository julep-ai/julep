# Memory

[Julep Python SDK Index](../../README.md#julep-python-sdk-index) / [Julep](../index.md#julep) / [Managers](./index.md#managers) / Memory

> Auto-generated documentation for [julep.managers.memory](../../../../../../julep/managers/memory.py) module.

- [Memory](#memory)
  - [AsyncMemoriesManager](#asyncmemoriesmanager)
  - [BaseMemoriesManager](#basememoriesmanager)
  - [MemoriesManager](#memoriesmanager)

## AsyncMemoriesManager

[Show source in memory.py:134](../../../../../../julep/managers/memory.py#L134)

Asynchronously lists memories based on various filter parameters.

Args:
    agent_id (Union[str, UUID]): The unique identifier of the agent.
    query (str): The search query string to filter memories.
    types (Optional[Union[str, List[str]]], optional): The types of memories to filter by. Defaults to None.
    user_id (Optional[str], optional): The unique identifier of the user. Defaults to None.
    limit (Optional[int], optional): The maximum number of memories to return. Defaults to None.
    offset (Optional[int], optional): The number of memories to skip before starting to collect the result set. Defaults to None.

Returns:
    List[Memory]: A list of Memory objects that match the given filters.

Raises:
    ValidationError: If the input validation fails.
    DatabaseError: If there is a problem accessing the database.

#### Signature

```python
class AsyncMemoriesManager(BaseMemoriesManager): ...
```

#### See also

- [BaseMemoriesManager](#basememoriesmanager)

### AsyncMemoriesManager().list

[Show source in memory.py:154](../../../../../../julep/managers/memory.py#L154)

Asynchronously list memories based on query parameters.

#### Arguments

agent_id (Union[str, UUID]): The ID of the agent to list memories for.
- `query` *str* - The query string to filter memories.
types (Optional[Union[str, List[str]]], optional): The types of memories to retrieve. Defaults to None.
- `user_id` *Optional[str], optional* - The ID of the user to list memories for. Defaults to None.
- `limit` *Optional[int], optional* - The maximum number of memories to return. Defaults to None.
- `offset` *Optional[int], optional* - The offset to start listing memories from. Defaults to None.

#### Returns

- `List[Memory]` - A list of Memory objects that match the query.

#### Notes

`@beartype` decorator is used for runtime type checking.

#### Signature

```python
@beartype
async def list(
    self,
    agent_id: Union[str, UUID],
    query: str,
    types: Optional[Union[str, List[str]]] = None,
    user_id: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Memory]: ...
```



## BaseMemoriesManager

[Show source in memory.py:16](../../../../../../julep/managers/memory.py#L16)

A base manager class for handling agent memories.

This manager provides an interface to interact with agent memories, facilitating
operations such as listing and retrieving memories based on various criteria.

Methods:
    _list(agent_id, query, types=None, user_id=None, limit=None, offset=None):
        Retrieves a list of memories for a given agent.

Args:
    agent_id (str): A valid UUID v4 string identifying the agent.
    query (str): The query string to search memories.
    types (Optional[Union[str, List[str]]]): The type(s) of memories to retrieve.
    user_id (Optional[str]): The user identifier associated with the memories.
    limit (Optional[int]): The maximum number of memories to retrieve.
    offset (Optional[int]): The number of initial memories to skip in the result set.

Returns:
    Union[GetAgentMemoriesResponse, Awaitable[GetAgentMemoriesResponse]]:
        A synchronous or asynchronous response object containing the list of agent memories.

Raises:
    AssertionError: If `agent_id` is not a valid UUID v4.

#### Signature

```python
class BaseMemoriesManager(BaseManager): ...
```

### BaseMemoriesManager()._list

[Show source in memory.py:43](../../../../../../julep/managers/memory.py#L43)

List memories from a given agent based on a query and further filtering options.

#### Arguments

- `agent_id` *str* - A valid UUID v4 representing the agent ID.
- `query` *str* - Query string to filter memories.
types (Optional[Union[str, List[str]]], optional): The types of memories to filter.
- `user_id` *Optional[str], optional* - The user ID to filter memories.
- `limit` *Optional[int], optional* - The maximum number of memories to return.
- `offset` *Optional[int], optional* - The number of memories to skip before starting to collect the result set.

#### Returns

- `Union[GetAgentMemoriesResponse,` *Awaitable[GetAgentMemoriesResponse]]* - Returns a synchronous or asynchronous response with the agent memories.

#### Raises

- `AssertionError` - If `agent_id` is not a valid UUID v4.

#### Signature

```python
def _list(
    self,
    agent_id: str,
    query: str,
    types: Optional[Union[str, List[str]]] = None,
    user_id: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Union[GetAgentMemoriesResponse, Awaitable[GetAgentMemoriesResponse]]: ...
```



## MemoriesManager

[Show source in memory.py:80](../../../../../../julep/managers/memory.py#L80)

A class for managing memory entities associated with agents.

Inherits from [BaseMemoriesManager](#basememoriesmanager) and extends its functionality to specifically
manage and retrieve memory entities for agents based on query parameters.

Attributes:
    Inherited from [BaseMemoriesManager](#basememoriesmanager).

Methods:
    list: Retrieves a list of memory entities based on query parameters.

#### Signature

```python
class MemoriesManager(BaseMemoriesManager): ...
```

#### See also

- [BaseMemoriesManager](#basememoriesmanager)

### MemoriesManager().list

[Show source in memory.py:94](../../../../../../julep/managers/memory.py#L94)

List memories meeting specified criteria.

This function fetches a list of Memory objects based on various filters and parameters such as agent_id, query, types, user_id, limit, and offset.

#### Arguments

agent_id (Union[str, UUID]): The unique identifier for the agent.
- `query` *str* - The search term used to filter memories.
types (Optional[Union[str, List[str]]], optional): The types of memories to retrieve. Can be a single type as a string or a list of types. Default is None, which does not filter by type.
- `user_id` *Optional[str], optional* - The unique identifier for the user. If provided, only memories associated with this user will be retrieved. Default is None.
- `limit` *Optional[int], optional* - The maximum number of memories to return. Default is None, which means no limit.
- `offset` *Optional[int], optional* - The number of memories to skip before starting to return the results. Default is None.

#### Returns

- `List[Memory]` - A list of Memory objects that match the given criteria.

#### Notes

The `@beartype` decorator is used to ensure that arguments conform to the expected types at runtime.

#### Signature

```python
@beartype
def list(
    self,
    agent_id: Union[str, UUID],
    query: str,
    types: Optional[Union[str, List[str]]] = None,
    user_id: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Memory]: ...
```