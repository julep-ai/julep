# Memories

[Julep Python SDK Index](./#julep-python-sdk-index) / [Julep](../../python-sdk-docs/julep/index.md#julep) / [Managers](../../python-sdk-docs/julep/managers/index.md#managers) / Memory

> Auto-generated documentation for [julep.managers.memory](../../../julep/managers/memory.py) module.

* [Memory](memory.md#memory)
  * [AsyncMemoriesManager](memory.md#asyncmemoriesmanager)
  * [BaseMemoriesManager](memory.md#basememoriesmanager)
  * [MemoriesManager](memory.md#memoriesmanager)

## AsyncMemoriesManager

[Show source in memory.py:135](../../../julep/managers/memory.py#L135)

Asynchronously lists memories based on various filter parameters.

Args: agent\_id (Union\[str, UUID]): The unique identifier of the agent. query (str): The search query string to filter memories. types (Optional\[Union\[str, List\[str]]], optional): The types of memories to filter by. Defaults to None. user\_id (Optional\[str], optional): The unique identifier of the user. Defaults to None. limit (Optional\[int], optional): The maximum number of memories to return. Defaults to None. offset (Optional\[int], optional): The number of memories to skip before starting to collect the result set. Defaults to None.

Returns: List\[Memory]: A list of Memory objects that match the given filters.

Raises: ValidationError: If the input validation fails. DatabaseError: If there is a problem accessing the database.

#### Signature

```python
class AsyncMemoriesManager(BaseMemoriesManager): ...
```

#### See also

* [BaseMemoriesManager](memory.md#basememoriesmanager)

### AsyncMemoriesManager().list

[Show source in memory.py:155](../../../julep/managers/memory.py#L155)

Asynchronously list memories based on query parameters.

#### Arguments

agent\_id (Union\[str, UUID]): The ID of the agent to list memories for.

* `query` _str_ - The query string to filter memories. types (Optional\[Union\[str, List\[str]]], optional): The types of memories to retrieve. Defaults to None.
* `user_id` _Optional\[str], optional_ - The ID of the user to list memories for. Defaults to None.
* `limit` _Optional\[int], optional_ - The maximum number of memories to return. Defaults to None.
* `offset` _Optional\[int], optional_ - The offset to start listing memories from. Defaults to None.

#### Returns

* `List[Memory]` - A list of Memory objects that match the query.

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

[Show source in memory.py:16](../../../julep/managers/memory.py#L16)

A base manager class for handling agent memories.

This manager provides an interface to interact with agent memories, allowing for listing and other operations to manage an agent's memories.

Methods: \_list(agent\_id, query, types=None, user\_id=None, limit=None, offset=None): Retrieves a list of memories for a given agent.

Args: agent\_id (str): A valid UUID v4 string identifying the agent. query (str): The query string to search memories. types (Optional\[Union\[str, List\[str]]]): The type(s) of memories to retrieve. user\_id (Optional\[str]): The user identifier associated with the memories. limit (Optional\[int]): The maximum number of memories to retrieve. offset (Optional\[int]): The number of initial memories to skip in the result set.

Returns: Union\[GetAgentMemoriesResponse, Awaitable\[GetAgentMemoriesResponse]]: A synchronous or asynchronous response object containing the list of agent memories.

Raises: AssertionError: If `agent_id` is not a valid UUID v4.

#### Signature

```python
class BaseMemoriesManager(BaseManager): ...
```

### BaseMemoriesManager().\_list

[Show source in memory.py:43](../../../julep/managers/memory.py#L43)

List memories from a given agent based on a query and further filtering options.

#### Arguments

* `agent_id` _str_ - A valid UUID v4 representing the agent ID.
* `query` _str_ - Query string to filter memories. types (Optional\[Union\[str, List\[str]]], optional): The types of memories to filter.
* `user_id` _Optional\[str], optional_ - The user ID to filter memories.
* `limit` _Optional\[int], optional_ - The maximum number of memories to return.
* `offset` _Optional\[int], optional_ - The number of memories to skip before starting to collect the result set.

#### Returns

* `Union[GetAgentMemoriesResponse,` _Awaitable\[GetAgentMemoriesResponse]]_ - Returns a synchronous or asynchronous response with the agent memories.

#### Raises

* `AssertionError` - If `agent_id` is not a valid UUID v4.

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

[Show source in memory.py:81](../../../julep/managers/memory.py#L81)

A class for managing memory entities associated with agents.

This class inherits from [BaseMemoriesManager](memory.md#basememoriesmanager) and provides an interface to list memory entities for a given agent.

Attributes: Inherited from [BaseMemoriesManager](memory.md#basememoriesmanager).

Methods: list: Retrieves a list of memory entities based on query parameters.

#### Signature

```python
class MemoriesManager(BaseMemoriesManager): ...
```

#### See also

* [BaseMemoriesManager](memory.md#basememoriesmanager)

### MemoriesManager().list

[Show source in memory.py:95](../../../julep/managers/memory.py#L95)

List memories meeting specified criteria.

This function fetches a list of Memory objects based on various filters and parameters such as agent\_id, query, types, user\_id, limit, and offset.

#### Arguments

agent\_id (Union\[str, UUID]): The unique identifier for the agent.

* `query` _str_ - The search term used to filter memories. types (Optional\[Union\[str, List\[str]]], optional): The types of memories to retrieve. Can be a single type as a string or a list of types. Default is None, which does not filter by type.
* `user_id` _Optional\[str], optional_ - The unique identifier for the user. If provided, only memories associated with this user will be retrieved. Default is None.
* `limit` _Optional\[int], optional_ - The maximum number of memories to return. Default is None, which means no limit.
* `offset` _Optional\[int], optional_ - The number of memories to skip before starting to return the results. Default is None.

#### Returns

* `List[Memory]` - A list of Memory objects that match the given criteria.

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
