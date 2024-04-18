# Agent

[Julep Python SDK Index](../../README.md#julep-python-sdk-index) / [Julep](../index.md#julep) / [Managers](./index.md#managers) / Agent

> Auto-generated documentation for [julep.managers.agent](../../../../../../julep/managers/agent.py) module.

- [Agent](#agent)
  - [AgentCreateArgs](#agentcreateargs)
  - [AgentUpdateArgs](#agentupdateargs)
  - [AgentsManager](#agentsmanager)
  - [AsyncAgentsManager](#asyncagentsmanager)
  - [BaseAgentsManager](#baseagentsmanager)

## AgentCreateArgs

[Show source in agent.py:41](../../../../../../julep/managers/agent.py#L41)

#### Signature

```python
class AgentCreateArgs(TypedDict): ...
```



## AgentUpdateArgs

[Show source in agent.py:53](../../../../../../julep/managers/agent.py#L53)

#### Signature

```python
class AgentUpdateArgs(TypedDict): ...
```



## AgentsManager

[Show source in agent.py:312](../../../../../../julep/managers/agent.py#L312)

A class for managing agents, inheriting from [BaseAgentsManager](#baseagentsmanager).

This class provides functionalities to interact with and manage agents, including creating, retrieving, listing, updating, and deleting agents. It utilizes type annotations to ensure type correctness at runtime using the `beartype` decorator.

#### Methods

- `get(id` - Union[str, UUID]) -> Agent:
    Retrieves an agent by its unique identifier.

#### Arguments

id (Union[str, UUID]): The unique identifier of the agent, which can be either a string or a UUID.

- `name` *str* - The name of the agent.
- `about` *str* - A description of the agent.
- `instructions` *List[str]* - A list of instructions or dictionaries defining instructions.
- `tools` *List[ToolDict], optional* - A list of dictionaries defining tools. Defaults to an empty list.
- `functions` *List[FunctionDefDict], optional* - A list of dictionaries defining functions. Defaults to an empty list.
- `default_settings` *DefaultSettingsDict, optional* - A dictionary of default settings. Defaults to an empty dictionary.
- `model` *ModelName, optional* - The model name to be used. Defaults to 'julep-ai/samantha-1-turbo'.
- `docs` *List[DocDict], optional* - A list of dictionaries defining documentation. Defaults to an empty list.
metadata (Dict[str, Any])

- `limit` *Optional[int], optional* - The maximum number of agents to retrieve. Defaults to None, meaning no limit.
- `offset` *Optional[int], optional* - The number of agents to skip (for pagination). Defaults to None.

agent_id (Union[str, UUID]): The unique identifier of the agent to be deleted.

- `update(*,` *agent_id* - Union[str, UUID], about: Optional[str]=None, instructions: Optional[List[str]]=None, name: Optional[str]=None, model: Optional[str]=None, default_settings: Optional[DefaultSettingsDict]=None) -> ResourceUpdatedResponse:
    Updates an existing agent with new details.

agent_id (Union[str, UUID]): The unique identifier of the agent to be updated.
- `about` *Optional[str], optional* - A new description of the agent. Defaults to None (no change).
- `instructions` *Optional[List[str]], optional* - A new list of instructions or dictionaries defining instructions. Defaults to None (no change).
- `name` *Optional[str], optional* - A new name for the agent. Defaults to None (no change).
- `model` *Optional[str], optional* - A new model name to be used. Defaults to None (no change).
- `default_settings` *Optional[DefaultSettingsDict], optional* - A new dictionary of default settings. Defaults to None (no change).
metadata (Dict[str, Any])

#### Returns

- `Agent` - The agent with the corresponding identifier.

- `create(*,` *name* - str, about: str, instructions: List[str], tools: List[ToolDict]=[], functions: List[FunctionDefDict]=[], default_settings: DefaultSettingsDict={}, model: ModelName='julep-ai/samantha-1-turbo', docs: List[DocDict]=[]) -> ResourceCreatedResponse:
    Creates a new agent with the provided details.

- `ResourceCreatedResponse` - The response indicating the resource (agent) was successfully created.

- `list(*,` *limit* - Optional[int]=None, offset: Optional[int]=None) -> List[Agent]:
    Lists all agents with pagination support.

- `List[Agent]` - A list of agents, considering the pagination parameters.

- `delete(agent_id` - Union[str, UUID]):
    Deletes an agent by its unique identifier.

- `ResourceUpdatedResponse` - The response indicating the resource (agent) was successfully updated.

#### Signature

```python
class AgentsManager(BaseAgentsManager): ...
```

#### See also

- [BaseAgentsManager](#baseagentsmanager)

### AgentsManager().create

[Show source in agent.py:394](../../../../../../julep/managers/agent.py#L394)

Creates a new resource with the specified details.

#### Arguments

- `name` *str* - The name of the resource.
- `about` *str* - A description of the resource.
- `instructions` *List[str]* - A list of instructions or dictionaries with instruction details.
- `tools` *List[ToolDict], optional* - A list of dictionaries with tool details. Defaults to an empty list.
- `functions` *List[FunctionDefDict], optional* - A list of dictionaries with function definition details. Defaults to an empty list.
- `default_settings` *DefaultSettingsDict, optional* - A dictionary with default settings. Defaults to an empty dictionary.
- `model` *ModelName, optional* - The name of the model to use. Defaults to 'julep-ai/samantha-1-turbo'.
- `docs` *List[DocDict], optional* - A list of dictionaries with documentation details. Defaults to an empty list.
metadata (Dict[str, Any])

#### Returns

- `Agent` - An instance of the Agent with the specified details

#### Notes

This function is decorated with `@beartype`, which will perform runtime type checking on the arguments.

#### Signature

```python
@beartype
@rewrap_in_class(Agent)
def create(self, **kwargs: AgentCreateArgs) -> Agent: ...
```

#### See also

- [AgentCreateArgs](#agentcreateargs)

### AgentsManager().delete

[Show source in agent.py:453](../../../../../../julep/managers/agent.py#L453)

Delete the agent with the specified ID.

Args:
    agent_id (Union[str, UUID]): The identifier of the agent to be deleted.

Returns:
    The return type depends on the implementation of the `_delete` method. This will typically be `None`
    if the deletion is successful, or an error may be raised if the deletion fails.

Note:
    The `@beartype` decorator is used to enforce type checking of the `agent_id` parameter.

#### Signature

```python
@beartype
def delete(self, agent_id: Union[str, UUID]): ...
```

### AgentsManager().get

[Show source in agent.py:377](../../../../../../julep/managers/agent.py#L377)

Retrieve an Agent object by its identifier.

#### Arguments

id (Union[str, UUID]): The unique identifier of the Agent to be retrieved.

#### Returns

- `Agent` - An instance of the Agent with the specified ID.

#### Raises

- `BeartypeException` - If the type of `id` is neither a string nor a UUID.
Any exception raised by the `_get` method.

#### Signature

```python
@beartype
def get(self, id: Union[str, UUID]) -> Agent: ...
```

### AgentsManager().list

[Show source in agent.py:420](../../../../../../julep/managers/agent.py#L420)

List the Agent objects, possibly with pagination.

#### Arguments

- `limit` *Optional[int], optional* - The maximum number of Agent objects to return.
                                 Defaults to None, meaning no limit is applied.
- `offset` *Optional[int], optional* - The number of initial Agent objects to skip before
                                  starting to collect the return list. Defaults to None,
                                  meaning no offset is applied.

#### Returns

- `List[Agent]` - A list of Agent objects.

#### Raises

- `BeartypeDecorHintPepParamViolation` - If the function is called with incorrect types
                                    for the `limit` or `offset` parameters.

#### Signature

```python
@beartype
def list(
    self,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    metadata_filter: Dict[str, Any] = {},
) -> List[Agent]: ...
```

### AgentsManager().update

[Show source in agent.py:470](../../../../../../julep/managers/agent.py#L470)

Update the properties of a resource.

This function updates various attributes of an existing resource based on the provided keyword arguments. All updates are optional and are applied only if the corresponding argument is given.

#### Arguments

agent_id (Union[str, UUID]): The identifier of the agent, either as a string or a UUID object.
- `about` *Optional[str], optional* - A brief description of the agent. Defaults to None.
- `instructions` *Optional[List[str]], optional* - A list of instructions or instruction dictionaries to update the agent with. Defaults to None.
- `name` *Optional[str], optional* - The new name to assign to the agent. Defaults to None.
- `model` *Optional[str], optional* - The model identifier to associate with the agent. Defaults to None.
- `default_settings` *Optional[DefaultSettingsDict], optional* - A dictionary of default settings to apply to the agent. Defaults to None.
metadata (Dict[str, Any])
- `overwrite` *bool, optional* - Whether to overwrite the existing agent settings. Defaults to False.

#### Returns

- `ResourceUpdatedResponse` - An object representing the response to the update request.

#### Notes

This method is decorated with `beartype`, which means it enforces type annotations at runtime.

#### Signature

```python
@beartype
@rewrap_in_class(Agent)
def update(self, agent_id: Union[str, UUID], **kwargs: AgentUpdateArgs) -> Agent: ...
```

#### See also

- [AgentUpdateArgs](#agentupdateargs)



## AsyncAgentsManager

[Show source in agent.py:499](../../../../../../julep/managers/agent.py#L499)

A class for managing asynchronous agent operations.

This class provides asynchronous methods for creating, retrieving, updating,
listing, and deleting agents. It is a subclass of BaseAgentsManager, which
defines the underlying functionality and structure that this class utilizes.

#### Attributes

None explicitly listed, as they are inherited from the [BaseAgentsManager](#baseagentsmanager) class.

#### Methods

get:
    Retrieves a single agent by its ID.

#### Arguments

id (Union[UUID, str]): The unique identifier of the agent to retrieve.

- `name` *str* - The name of the agent to create.
- `about` *str* - A description of the agent.
- `instructions` *List[str]* - The instructions for operating the agent.
- `tools` *List[ToolDict], optional* - An optional list of tools for the agent.
- `functions` *List[FunctionDefDict], optional* - An optional list of functions the agent can perform.
- `default_settings` *DefaultSettingsDict, optional* - Optional default settings for the agent.
- `model` *ModelName, optional* - The model name to associate with the agent, defaults to 'julep-ai/samantha-1-turbo'.
- `docs` *List[DocDict], optional* - An optional list of documents associated with the agent.
metadata (Dict[str, Any])

- `limit` *Optional[int], optional* - The maximum number of agents to retrieve.
- `offset` *Optional[int], optional* - The number of agents to skip before starting to collect the results.

agent_id (Union[str, UUID]): The unique identifier of the agent to delete.

agent_id (Union[str, UUID]): The unique identifier of the agent to update.
- `about` *Optional[str], optional* - An optional new description for the agent.
- `instructions` *Optional[List[str]], optional* - Optional new instructions for the agent.
- `name` *Optional[str], optional* - An optional new name for the agent.
- `model` *Optional[str], optional* - Optional new model associated with the agent.
- `default_settings` *Optional[DefaultSettingsDict], optional* - Optional new default settings for the agent.
metadata (Dict[str, Any])

#### Returns

- `Agent` - The requested agent.

create:
    Creates a new agent with the provided specifications.

- `ResourceCreatedResponse` - A response indicating the agent was created successfully.

list:
    Asynchronously lists agents with optional pagination and returns an awaitable object.

- `List[Agent]` - A list of agents.

delete:
    Asynchronously deletes an agent by its ID and returns an awaitable object.

The response from the delete operation (specific return type may vary).

update:
    Asynchronously updates the specified fields of an agent by its ID and returns an awaitable object.

- `ResourceUpdatedResponse` - A response indicating the agent was updated successfully.

#### Signature

```python
class AsyncAgentsManager(BaseAgentsManager): ...
```

#### See also

- [BaseAgentsManager](#baseagentsmanager)

### AsyncAgentsManager().create

[Show source in agent.py:591](../../../../../../julep/managers/agent.py#L591)

Create a new resource asynchronously with specified details.

This function is decorated with `beartype` to ensure that arguments conform to specified types.

#### Arguments

- `name` *str* - The name of the resource to create.
- `about` *str* - Information or description about the resource.
- `instructions` *List[str]* - A list of strings or dictionaries detailing the instructions for the resource.
- `tools` *List[ToolDict], optional* - A list of dictionaries representing the tools associated with the resource. Defaults to an empty list.
- `functions` *List[FunctionDefDict], optional* - A list of dictionaries defining functions that can be performed with the resource. Defaults to an empty list.
- `default_settings` *DefaultSettingsDict, optional* - A dictionary with default settings for the resource. Defaults to an empty dictionary.
- `model` *ModelName, optional* - The model identifier to use for the resource. Defaults to 'julep-ai/samantha-1-turbo'.
- `docs` *List[DocDict], optional* - A list of dictionaries containing documentation for the resource. Defaults to an empty list.
metadata (Dict[str, Any])

#### Returns

- `Agent` - An instance of the Agent with the specified details

#### Raises

The exceptions that may be raised are not specified in the signature and depend on the implementation of the _create method.

#### Signature

```python
@beartype
@rewrap_in_class(Agent)
async def create(self, **kwargs: AgentCreateArgs) -> Agent: ...
```

#### See also

- [AgentCreateArgs](#agentcreateargs)

### AsyncAgentsManager().delete

[Show source in agent.py:650](../../../../../../julep/managers/agent.py#L650)

Asynchronously deletes an agent given its identifier.

This function is decorated with @beartype to ensure type checking of the input argument at runtime.

#### Arguments

agent_id (Union[str, UUID]): The identifier of the agent to be deleted. Can be a string or a UUID object.

#### Returns

The result of the asynchronous deletion operation, which is implementation-dependent.

#### Signature

```python
@beartype
async def delete(self, agent_id: Union[str, UUID]): ...
```

### AsyncAgentsManager().get

[Show source in agent.py:572](../../../../../../julep/managers/agent.py#L572)

Asynchronously retrieve an Agent object by its ID.

The `id` parameter can be either a UUID or a string representation of a UUID.

#### Arguments

id (Union[UUID, str]): The unique identifier of the Agent to retrieve.

#### Returns

- `Agent` - The Agent object associated with the given id.

#### Raises

- `Beartype` *exceptions* - If the input id does not conform to the specified types.
- `Other` *exceptions* - Depending on the implementation of the `_get` method.

#### Signature

```python
@beartype
async def get(self, id: Union[UUID, str]) -> Agent: ...
```

### AsyncAgentsManager().list

[Show source in agent.py:619](../../../../../../julep/managers/agent.py#L619)

Asynchronously lists agents with optional limit and offset.

This method wraps the call to a private method '_list_items' which performs the actual listing
of agent items. It uses the 'beartype' decorator for runtime type checking.

#### Arguments

- `limit` *Optional[int], optional* - The maximum number of agent items to return. Defaults to None, which means no limit.
- `offset` *Optional[int], optional* - The offset from where to start the listing. Defaults to None, which means start from the beginning.

#### Returns

- `List[Agent]` - A list of agent items collected based on the provided 'limit' and 'offset' parameters.

#### Signature

```python
@beartype
async def list(
    self,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    metadata_filter: Dict[str, Any] = {},
) -> List[Agent]: ...
```

### AsyncAgentsManager().update

[Show source in agent.py:665](../../../../../../julep/managers/agent.py#L665)

Asynchronously update an agent's details.

This function is decorated with `beartype` to enforce the type checking of parameters. It updates the properties of the agent identified by `agent_id`.

#### Arguments

agent_id (Union[str, UUID]): Unique identifier for the agent. It can be a string or a UUID object.
- `about` *Optional[str]* - Additional information about the agent. Default is None.
- `instructions` *Optional[List[str]]* - A list of instructions or instruction dictionaries. Default is None.
- `name` *Optional[str]* - The name of the agent. Default is None.
- `model` *Optional[str]* - The model identifier or name. Default is None.
- `default_settings` *Optional[DefaultSettingsDict]* - Dictionary with default settings for the agent. Default is None.
metadata (Dict[str, Any])
- `overwrite` *bool* - Whether to overwrite the existing agent settings. Default is False.

#### Returns

- `ResourceUpdatedResponse` - An object containing the details of the update response.

#### Signature

```python
@beartype
@rewrap_in_class(Agent)
async def update(
    self, agent_id: Union[str, UUID], **kwargs: AgentUpdateArgs
) -> Agent: ...
```

#### See also

- [AgentUpdateArgs](#agentupdateargs)



## BaseAgentsManager

[Show source in agent.py:63](../../../../../../julep/managers/agent.py#L63)

A class responsible for managing agent entities.

This manager handles CRUD operations for agents including retrieving, creating, listing, deleting, and updating agents using an API client.

#### Attributes

- `api_client` *ApiClientType* - The client responsible for API interactions.

#### Methods

- `_get(self,` *id* - Union[str, UUID]) -> Union[Agent, Awaitable[Agent]]:
    Retrieves a single agent by its UUID.

#### Arguments

id (Union[str, UUID]): The UUID of the agent to retrieve.
- `name` *str* - The name of the new agent.
- `about` *str* - Description about the new agent.
- `instructions` *List[str]* - List of instructions or instruction dictionaries for the new agent.
- `tools` *List[ToolDict], optional* - List of tool dictionaries. Defaults to an empty list.
- `functions` *List[FunctionDefDict], optional* - List of function definition dictionaries. Defaults to an empty list.
- `default_settings` *DefaultSettingsDict, optional* - Dictionary of default settings for the new agent. Defaults to an empty dictionary.
- `model` *ModelName, optional* - The model name for the new agent. Defaults to 'julep-ai/samantha-1-turbo'.
- `docs` *List[DocDict], optional* - List of document dictionaries for the new agent. Defaults to an empty list.
metadata (Dict[str, Any], optional): Dictionary of metadata for the new agent. Defaults to an empty dictionary.
- `limit` *Optional[int], optional* - The maximum number of agents to list. Defaults to None.
- `offset` *Optional[int], optional* - The number of agents to skip (for pagination). Defaults to None.
metadata_filter (Dict[str, Any], optional): Filters for querying agents based on metadata. Defaults to an empty dictionary.
agent_id (Union[str, UUID]): The UUID of the agent to delete.
agent_id (Union[str, UUID]): The UUID of the agent to update.
- `about` *Optional[str], optional* - The new description about the agent.
- `instructions` *Optional[List[str]], optional* - The new list of instructions or instruction dictionaries.
- `name` *Optional[str], optional* - The new name for the agent.
- `model` *Optional[str], optional* - The new model name for the agent.
- `default_settings` *Optional[DefaultSettingsDict], optional* - The new default settings dictionary for the agent.
metadata (Dict[str, Any])

#### Returns

The agent object or an awaitable that resolves to the agent object.

- `_create(self,` *name* - str, about: str, instructions: List[str], tools: List[ToolDict] = [], functions: List[FunctionDefDict] = [], default_settings: DefaultSettingsDict = {}, model: ModelName = 'julep-ai/samantha-1-turbo', docs: List[DocDict] = [], metadata: Dict[str, Any] = {}) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]:
    Creates an agent with the given specifications.
        The response indicating creation or an awaitable that resolves to the creation response.

- `_list_items(self,` *limit* - Optional[int] = None, offset: Optional[int] = None, metadata_filter: Dict[str, Any] = {}) -> Union[ListAgentsResponse, Awaitable[ListAgentsResponse]]:
    Lists agents with pagination support and optional metadata filtering.
        The list of agents or an awaitable that resolves to the list of agents.

- `_delete(self,` *agent_id* - Union[str, UUID]) -> Union[None, Awaitable[None]]:
    Deletes an agent with the specified UUID.
        None or an awaitable that resolves to None.

- `_update(self,` *agent_id* - Union[str, UUID], about: Optional[str] = None, instructions: Optional[List[str]] = None, name: Optional[str] = None, model: Optional[str] = None, default_settings: Optional[DefaultSettingsDict] = None, metadata: Dict[str, Any] = {}) -> Union[ResourceUpdatedResponse, Awaitable[ResourceUpdatedResponse]]:
    Updates the specified fields of an agent.
        The response indicating successful update or an awaitable that resolves to the update response.

#### Signature

```python
class BaseAgentsManager(BaseManager): ...
```

### BaseAgentsManager()._create

[Show source in agent.py:141](../../../../../../julep/managers/agent.py#L141)

Create a new agent with the specified configuration.

#### Arguments

- `name` *str* - Name of the agent.
- `about` *str* - Information about the agent.
- `instructions` *List[str]* - List of instructions as either string or dictionaries for the agent.
- `tools` *List[ToolDict], optional* - List of tool configurations for the agent. Defaults to an empty list.
- `functions` *List[FunctionDefDict], optional* - List of function definitions for the agent. Defaults to an empty list.
- `default_settings` *DefaultSettingsDict, optional* - Dictionary of default settings for the agent. Defaults to an empty dict.
- `model` *ModelName, optional* - The model name identifier. Defaults to 'julep-ai/samantha-1-turbo'.
- `docs` *List[DocDict], optional* - List of document configurations for the agent. Defaults to an empty list.
metadata (Dict[str, Any])

#### Returns

- `Union[ResourceCreatedResponse,` *Awaitable[ResourceCreatedResponse]]* - The response object indicating the resource has been created or a future of the response object if the creation is being awaited.

#### Raises

- `AssertionError` - If both functions and tools are provided.

#### Notes

The `_create` method is meant to be used internally and should be considered private.
It assumes the input data for instructions, tools, and docs will have the proper format,
and items in the 'instructions' list will be converted to Instruction instances.

#### Signature

```python
def _create(
    self,
    name: str,
    about: str = "",
    instructions: List[str] = [],
    tools: List[ToolDict] = [],
    functions: List[FunctionDefDict] = [],
    default_settings: DefaultSettingsDict = {},
    model: ModelName = "julep-ai/samantha-1-turbo",
    docs: List[DocDict] = [],
    metadata: Dict[str, Any] = {},
) -> Union[ResourceCreatedResponse, Awaitable[ResourceCreatedResponse]]: ...
```

#### See also

- [ModelName](#modelname)

### BaseAgentsManager()._delete

[Show source in agent.py:235](../../../../../../julep/managers/agent.py#L235)

Delete an agent by its ID.

#### Arguments

agent_id (Union[str, UUID]): The UUID v4 of the agent to be deleted.

#### Returns

- `Union[None,` *Awaitable[None]]* - A future that resolves to None if the
operation is asynchronous, or None immediately if the operation is
synchronous.

#### Raises

- `AssertionError` - If `agent_id` is not a valid UUID v4.

#### Signature

```python
def _delete(self, agent_id: Union[str, UUID]) -> Union[None, Awaitable[None]]: ...
```

### BaseAgentsManager()._get

[Show source in agent.py:125](../../../../../../julep/managers/agent.py#L125)

Retrieves an agent based on the provided identifier.

#### Arguments

id (Union[str, UUID]): The identifier of the agent, which can be a string or UUID object.

#### Returns

- `Union[Agent,` *Awaitable[Agent]]* - The agent object or an awaitable yielding the agent object, depending on the API client.

#### Raises

- `AssertionError` - If the provided id is not a valid UUID v4.

#### Signature

```python
def _get(self, id: Union[str, UUID]) -> Union[Agent, Awaitable[Agent]]: ...
```

### BaseAgentsManager()._list_items

[Show source in agent.py:211](../../../../../../julep/managers/agent.py#L211)

Lists items with optional pagination.

This method wraps the `list_agents` API call and includes optional limit and offset parameters for pagination.

Args:
    limit (Optional[int], optional): The maximum number of items to return. Defaults to None, which means no limit.
    offset (Optional[int], optional): The index of the first item to return. Defaults to None, which means no offset.

Returns:
    Union[ListAgentsResponse, Awaitable[ListAgentsResponse]]: A ListAgentsResponse object, or an awaitable that resolves to a ListAgentsResponse object.

#### Signature

```python
def _list_items(
    self,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    metadata_filter: str = "{}",
) -> Union[ListAgentsResponse, Awaitable[ListAgentsResponse]]: ...
```

### BaseAgentsManager()._update

[Show source in agent.py:253](../../../../../../julep/managers/agent.py#L253)

Update the agent's properties.

Args:
    agent_id (Union[str, UUID]): The unique identifier for the agent, which can be a string or UUID object.
    about (Optional[str], optional): A brief description of the agent. Defaults to None.
    instructions (Optional[List[str]], optional): A list of either strings or instruction dictionaries that will be converted into Instruction objects. Defaults to None.
    name (Optional[str], optional): The name of the agent. Defaults to None.
    model (Optional[str], optional): The model identifier for the agent. Defaults to None.
    default_settings (Optional[DefaultSettingsDict], optional): A dictionary of default settings to apply to the agent. Defaults to None.
    metadata (Dict[str, Any])
    overwrite (bool, optional): Whether to overwrite the existing agent settings. Defaults to False.

Returns:
    Union[ResourceUpdatedResponse, Awaitable[ResourceUpdatedResponse]]: An object representing the response for the resource updated, which can also be an awaitable in asynchronous contexts.

Raises:
    AssertionError: If the provided agent_id is not validated by the is_valid_uuid4 function.

Note:
    This method asserts that the agent_id must be a valid UUID v4. The instructions and default_settings, if provided, are converted into their respective object types before making the update API call.

#### Signature

```python
def _update(
    self,
    agent_id: Union[str, UUID],
    about: Optional[str] = NotSet,
    instructions: List[str] = NotSet,
    name: Optional[str] = NotSet,
    model: Optional[str] = NotSet,
    default_settings: Optional[DefaultSettingsDict] = NotSet,
    metadata: Dict[str, Any] = NotSet,
    overwrite: bool = False,
) -> Union[ResourceUpdatedResponse, Awaitable[ResourceUpdatedResponse]]: ...
```