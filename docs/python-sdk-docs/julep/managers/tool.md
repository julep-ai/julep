# Tool

[Julep Python SDK Index](../../README.md#julep-python-sdk-index) / [Julep](../index.md#julep) / [Managers](./index.md#managers) / Tool

> Auto-generated documentation for [julep.managers.tool](../../../../../../julep/managers/tool.py) module.

- [Tool](#tool)
  - [AsyncToolsManager](#asynctoolsmanager)
  - [BaseToolsManager](#basetoolsmanager)
  - [ToolsManager](#toolsmanager)

## AsyncToolsManager

[Show source in tool.py:351](../../../../../../julep/managers/tool.py#L351)

A manager for asynchronous tools handling.

This class provides async methods to manage tools, allowing create, retrieve, update, and delete operations.

Methods:
    get: Asynchronously retrieves tools associated with an agent.
    create: Asynchronously creates a new tool associated with an agent.
    delete: Asynchronously deletes a tool associated with an agent.
    update: Asynchronously updates a tool associated with an agent.

Attributes:
    Inherited from BaseToolsManager.

#### Signature

```python
class AsyncToolsManager(BaseToolsManager): ...
```

#### See also

- [BaseToolsManager](#basetoolsmanager)

### AsyncToolsManager().create

[Show source in tool.py:402](../../../../../../julep/managers/tool.py#L402)

Create a new resource asynchronously.

This method creates a new resource using the provided `agent_id` and `tool` information.

#### Arguments

agent_id (Union[str, UUID]): The identifier of the agent, which can be a string or a UUID object.
- `tool` *ToolDict* - A dictionary containing tool-specific data.

#### Returns

- `ResourceCreatedResponse` - An object representing the response received after creating the resource.

#### Raises

- `BeartypeException` - If the type of any argument does not match the expected type.

#### Signature

```python
@beartype
async def create(
    self, agent_id: Union[str, UUID], tool: ToolDict
) -> ResourceCreatedResponse: ...
```

### AsyncToolsManager().delete

[Show source in tool.py:429](../../../../../../julep/managers/tool.py#L429)

Asynchronously delete a specified agent-tool association.

This function is a high-level asynchronous API that delegates to a
private coroutinal method `_delete` to perform the actual deletion based on
the provided `agent_id` and `tool_id`.

Args:
    agent_id (Union[str, UUID]): The unique identifier of the agent.
    tool_id (Union[str, UUID]): The unique identifier of the tool.

Returns:
    The return type is not explicitly stated in the function signature.
    Typically, the returned value would be documented here, but you may need
    to investigate the implementation of `_delete` to determine what it
    returns.

Raises:
    The exceptions that this function might raise are not stated in the
    snippet provided. If the private method `_delete` raises any exceptions,
    they should be documented here. Depending on the implementation, common
    exceptions might include `ValueError` if identifiers are invalid or
    `RuntimeError` if deletion fails.

#### Signature

```python
@beartype
async def delete(self, agent_id: Union[str, UUID], tool_id: Union[str, UUID]): ...
```

### AsyncToolsManager().get

[Show source in tool.py:367](../../../../../../julep/managers/tool.py#L367)

Asynchronously get a list of Tool objects based on provided filters.

This method fetches Tool objects with the option to limit the results and
offset them, to allow for pagination.

#### Arguments

agent_id (Union[str, UUID]): The unique identifier of the agent for which to fetch tools.
- `limit` *Optional[int], optional* - The maximum number of tools to return. Defaults to None, which implies no limit.
- `offset` *Optional[int], optional* - The number of tools to skip before starting to return the tools. Defaults to None, which means start from the beginning.

#### Returns

- `List[Tool]` - A list of Tool objects that match the criteria.

#### Notes

This function is decorated with beartype, which assures that the input
arguments adhere to the specified types at runtime. It is an asynchronous
function and should be called with `await`.

#### Signature

```python
@beartype
async def get(
    self,
    agent_id: Union[str, UUID],
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Tool]: ...
```

### AsyncToolsManager().update

[Show source in tool.py:465](../../../../../../julep/managers/tool.py#L465)

Asynchronously updates a resource identified by the agent_id and tool_id with a new definition.

This function is type-enforced using the `beartype` decorator.

#### Arguments

agent_id (Union[str, UUID]): The unique identifier for the agent.
tool_id (Union[str, UUID]): The unique identifier for the tool.
- `function` *FunctionDefDict* - A dictionary containing the function definition which needs to be updated.

#### Returns

- `ResourceUpdatedResponse` - An object representing the response received after updating the resource.

#### Raises

This will depend on the implementation of the `_update` method and any exceptions that it raises.

#### Signature

```python
@beartype
async def update(
    self,
    agent_id: Union[str, UUID],
    tool_id: Union[str, UUID],
    function: FunctionDefDict,
) -> ResourceUpdatedResponse: ...
```



## BaseToolsManager

[Show source in tool.py:21](../../../../../../julep/managers/tool.py#L21)

A class to manage tools by interacting with an API client.

This class provides methods for creating, reading, updating, and deleting tools associated with agents. It ensures the validity of UUIDs for agent_id and tool_id where applicable and handles both synchronous and asynchronous operations.

#### Attributes

- `api_client` - The API client used to send requests to the service.

#### Methods

- `_get(self,` *agent_id* - Union[str, UUID], limit: Optional[int]=None, offset: Optional[int]=None) -> Union[GetAgentToolsResponse, Awaitable[GetAgentToolsResponse]]:
    Retrieves a list of tools associated with the specified agent. Supports pagination through limit and offset parameters.

- `_create(self,` *agent_id* - Union[str, UUID], tool: ToolDict) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]:
    Creates a new tool associated with the specified agent.

- `_update(self,` *agent_id* - Union[str, UUID], tool_id: Union[str, UUID], function: FunctionDefDict) -> Union[ResourceUpdatedResponse, Awaitable[ResourceUpdatedResponse]]:
    Updates the definition of an existing tool associated with the specified agent.

- `_delete(self,` *agent_id* - Union[str, UUID], tool_id: Union[str, UUID]):
    Deletes a tool associated with the specified agent.

#### Signature

```python
class BaseToolsManager(BaseManager): ...
```

### BaseToolsManager()._create

[Show source in tool.py:76](../../../../../../julep/managers/tool.py#L76)

Create a new tool associated with a given agent.

Args:
    agent_id (Union[str, UUID]): The ID of the agent for which to create the tool. Must be a valid UUID v4.
    tool (ToolDict): A dictionary with tool data conforming to the CreateToolRequest structure.

Returns:
    Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]: The response object indicating the newly created tool,
    either as a direct response or as an awaitable if it's an asynchronous operation.

#### Signature

```python
def _create(
    self, agent_id: Union[str, UUID], tool: ToolDict
) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]: ...
```

### BaseToolsManager()._delete

[Show source in tool.py:141](../../../../../../julep/managers/tool.py#L141)

Delete a tool associated with an agent.

Args:
    agent_id (Union[str, UUID]): The UUID of the agent.
    tool_id (Union[str, UUID]): The UUID of the tool to be deleted.

Returns:
    The response from the API client's delete_agent_tool method.

Raises:
    AssertionError: If either `agent_id` or `tool_id` is not a valid UUID v4.

#### Signature

```python
def _delete(self, agent_id: Union[str, UUID], tool_id: Union[str, UUID]): ...
```

### BaseToolsManager()._get

[Show source in tool.py:44](../../../../../../julep/managers/tool.py#L44)

Retrieve tools associated with the given agent.

This is a private method that fetches tools for the provided agent ID, with optional
limit and offset parameters for pagination.

#### Arguments

agent_id (Union[str, UUID]): The unique identifier for the agent, which can be a
    string or UUID object.
- `limit` *Optional[int], optional* - The maximum number of tools to retrieve. Defaults to None.
- `offset` *Optional[int], optional* - The number of tools to skip before starting to collect
    the result set. Defaults to None.

#### Returns

- `Union[GetAgentToolsResponse,` *Awaitable[GetAgentToolsResponse]]* - The response object which
contains the list of tools, or an awaitable response object for asynchronous operations.

#### Raises

- `AssertionError` - If the agent_id is not a valid UUID v4.

#### Signature

```python
def _get(
    self,
    agent_id: Union[str, UUID],
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Union[GetAgentToolsResponse, Awaitable[GetAgentToolsResponse]]: ...
```

### BaseToolsManager()._update

[Show source in tool.py:101](../../../../../../julep/managers/tool.py#L101)

Update the tool definition for a given agent.

Args:
    agent_id (Union[str, UUID]): The unique identifier for the agent, either in string or UUID format.
    tool_id (Union[str, UUID]): The unique identifier for the tool, either in string or UUID format.
    function (FunctionDefDict): A dictionary containing the function definition that conforms with the required API schema.
    overwrite (bool): A flag to indicate whether to overwrite the existing function definition. Defaults to False.

Returns:
    Union[ResourceUpdatedResponse, Awaitable[ResourceUpdatedResponse]]: The updated resource response sync or async.

Raises:
    AssertionError: If the `agent_id` or `tool_id` is not a valid UUID v4.

#### Signature

```python
def _update(
    self,
    agent_id: Union[str, UUID],
    tool_id: Union[str, UUID],
    function: FunctionDefDict,
    overwrite: bool = False,
) -> Union[ResourceUpdatedResponse, Awaitable[ResourceUpdatedResponse]]: ...
```



## ToolsManager

[Show source in tool.py:169](../../../../../../julep/managers/tool.py#L169)

A manager class for handling tools related to agents.

This class provides an interface to manage tools, including their retrieval, creation,
deletion, and updating. It extends the functionalities of the BaseToolsManager.

#### Methods

get:
    Retrieves a list of tools for the given agent.

#### Arguments

agent_id (Union[str, UUID]): The identifier of the agent whose tools are being retrieved.
- `limit` *Optional[int], optional* - The maximum number of tools to retrieve.
- `offset` *Optional[int], optional* - The index from which to start the retrieval.

agent_id (Union[str, UUID]): The identifier of the agent for whom the tool is being created.
- `tool` *ToolDict* - A dictionary of tool attributes.

agent_id (Union[str, UUID]): The identifier of the agent whose tool is being deleted.
tool_id (Union[str, UUID]): The unique identifier of the tool to be deleted.

update:
    Updates the definition of an existing tool for the given agent.

agent_id (Union[str, UUID]): The identifier of the agent whose tool is being updated.
tool_id (Union[str, UUID]): The unique identifier of the tool to be updated.
- `function` *FunctionDefDict* - A dictionary representing the definition of the tool to be updated.

#### Returns

- `List[Tool]` - A list of Tool objects.

create:
    Creates a new tool for the given agent.

- `ResourceCreatedResponse` - An object indicating the successful creation of the tool.

delete:
    Deletes a tool for the given agent.

- `ResourceUpdatedResponse` - An object indicating the successful update of the tool.

Inherits:
    - [BaseToolsManager](#basetoolsmanager) - A base class that defines the basic operations for tool management.

#### Signature

```python
class ToolsManager(BaseToolsManager): ...
```

#### See also

- [BaseToolsManager](#basetoolsmanager)

### ToolsManager().create

[Show source in tool.py:251](../../../../../../julep/managers/tool.py#L251)

Create a new resource with the provided agent identifier and tool information.

This method wraps the internal `_create` method to construct and return a ResourceCreatedResponse.

Args:
    agent_id (Union[str, UUID]): The unique identifier for the agent. Can be a string or a UUID object.
    tool (ToolDict): A dictionary containing tool-specific configuration or information.

Returns:
    ResourceCreatedResponse: An object representing the successfully created resource, including metadata like creation timestamps and resource identifiers.

Raises:
    TypeError: If the `agent_id` or `tool` arguments are not of the expected type.
    ValueError: If any values within the `tool` dictionary are invalid or out of accepted range.
    RuntimeError: If the creation process encounters an unexpected error.

Note:
    The `@beartype` decorator is used to enforce type checking of the arguments at runtime.

Example usage:

```python
>>> response = instance.create(agent_id="123e4567-e89b-12d3-a456-426614174000", tool={"type": "screwdriver", "size": "M4"})
>>> print(response)
ResourceCreatedResponse(resource_id='abcde-12345', created_at='2021-01-01T12:00:00Z')
```

#### Signature

```python
@beartype
def create(
    self, agent_id: Union[str, UUID], tool: ToolDict
) -> ResourceCreatedResponse: ...
```

### ToolsManager().delete

[Show source in tool.py:289](../../../../../../julep/managers/tool.py#L289)

Deletes an agent's access to a specific tool.

#### Arguments

agent_id (Union[str, UUID]): The unique identifier of the agent.
tool_id (Union[str, UUID]): The unique identifier of the tool.

#### Returns

The result of the delete operation, the specific type of which may depend on the implementation of `_delete`.

#### Raises

- `Beartype` *exceptions* - If `agent_id` or `tool_id` are of the wrong type.

#### Signature

```python
@beartype
def delete(self, agent_id: Union[str, UUID], tool_id: Union[str, UUID]): ...
```

### ToolsManager().get

[Show source in tool.py:220](../../../../../../julep/managers/tool.py#L220)

Retrieve a list of Tool objects for the specified agent.

This method wraps the internal _get method and returns the 'items' property
from the result, which contains a list of Tool instances.

Args:
    agent_id (Union[str, UUID]): The ID of the agent to retrieve Tool objects for.
    limit (Optional[int]): The maximum number of Tool objects to return. Defaults to None, implying no limit.
    offset (Optional[int]): The number to skip before starting to collect the result set. Defaults to None, implying no offset.

Returns:
    List[Tool]: A list of Tool instances associated with the specified agent ID.

Raises:
    BeartypeException: If the input argument types do not match the expected types.

#### Signature

```python
@beartype
def get(
    self,
    agent_id: Union[str, UUID],
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Tool]: ...
```

### ToolsManager().update

[Show source in tool.py:314](../../../../../../julep/managers/tool.py#L314)

Update a specific tool definition for an agent.

#### Arguments

agent_id (Union[str, UUID]): The unique identifier of the agent.
tool_id (Union[str, UUID]): The unique identifier of the tool to be updated.
- `function` *FunctionDefDict* - A dictionary containing the new definition of the tool.
- `overwrite` *bool* - A flag indicating whether to overwrite the existing definition.

#### Returns

- `ResourceUpdatedResponse` - An object representing the update operation response.

#### Notes

This function is decorated with `beartype` which ensures that the arguments provided
match the expected types at runtime.

#### Raises

- `BeartypeDecorHintPepParamException` - If the type of any parameter does not match the expected type.
Any exceptions that `self._update` method might raise.

#### Signature

```python
@beartype
def update(
    self,
    agent_id: Union[str, UUID],
    tool_id: Union[str, UUID],
    function: FunctionDefDict,
    overwrite: bool = False,
) -> ResourceUpdatedResponse: ...
```