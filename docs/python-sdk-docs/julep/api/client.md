# Client

[Julep Python SDK Index](../../README.md#julep-python-sdk-index) / [Julep](../index.md#julep) / [Julep Python Library](./index.md#julep-python-library) / Client

> Auto-generated documentation for [julep.api.client](../../../../../../julep/api/client.py) module.

#### Attributes

- `OMIT` - this is used as the default value for optional parameters: typing.cast(typing.Any, ...)


- [Client](#client)
  - [AsyncJulepApi](#asyncjulepapi)
  - [JulepApi](#julepapi)

## AsyncJulepApi

[Show source in client.py:3706](../../../../../../julep/api/client.py#L3706)

Use this class to access the different functions within the SDK. You can instantiate any number of clients with different configuration that will propagate to these functions.

Parameters
----------
base_url : typing.Optional[str]
    The base url to use for requests from the client.

environment : JulepApiEnvironment
    The environment to use for requests from the client. from .environment import JulepApiEnvironment

Defaults to JulepApiEnvironment.DEFAULT

auth_key : str
api_key : str
timeout : typing.Optional[float]
    The timeout to be used, in seconds, for requests. By default the timeout is 300 seconds, unless a custom httpx client is used, in which case this default is not enforced.

follow_redirects : typing.Optional[bool]
    Whether the default httpx client follows redirects or not, this is irrelevant if a custom httpx client is passed in.

httpx_client : typing.Optional[httpx.AsyncClient]
    The httpx client to use for making requests, a preconfigured client is used by default, however this is useful should you want to pass in any custom httpx configuration.

Examples
--------
from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

#### Signature

```python
class AsyncJulepApi:
    def __init__(
        self,
        base_url: typing.Optional[str] = None,
        environment: JulepApiEnvironment = JulepApiEnvironment.DEFAULT,
        auth_key: str,
        api_key: str,
        timeout: typing.Optional[float] = None,
        follow_redirects: typing.Optional[bool] = True,
        httpx_client: typing.Optional[httpx.AsyncClient] = None,
    ): ...
```

### AsyncJulepApi().agent_docs_route_create

[Show source in client.py:4404](../../../../../../julep/api/client.py#L4404)

Create a Doc for this Agent

Parameters
----------
id : CommonUuid
    ID of parent resource

title : CommonIdentifierSafeUnicode
    Title describing what this document contains

content : DocsCreateDocRequestContent
    Contents of the document

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceCreatedResponse
    The request has succeeded and a new resource has been created as a result.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.agent_docs_route_create(
        id="id",
        title="title",
        content="content",
    )

asyncio.run(main())

#### Signature

```python
async def agent_docs_route_create(
    self,
    id: CommonUuid,
    title: CommonIdentifierSafeUnicode,
    content: DocsCreateDocRequestContent,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceCreatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().agent_docs_route_delete

[Show source in client.py:4474](../../../../../../julep/api/client.py#L4474)

Delete a Doc for this Agent

Parameters
----------
id : CommonUuid
    ID of parent resource

child_id : CommonUuid
    ID of the resource to be deleted

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceDeletedResponse
    The request has been accepted for processing, but processing has not yet completed.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.agent_docs_route_delete(
        id="id",
        child_id="child_id",
    )

asyncio.run(main())

#### Signature

```python
async def agent_docs_route_delete(
    self,
    id: CommonUuid,
    child_id: CommonUuid,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceDeletedResponse: ...
```

### AsyncJulepApi().agent_docs_route_list

[Show source in client.py:4317](../../../../../../julep/api/client.py#L4317)

List Docs owned by an Agent

Parameters
----------
id : CommonUuid
    ID of parent

limit : CommonLimit
    Limit the number of items returned

offset : CommonOffset
    Offset the items returned

sort_by : AgentDocsRouteListRequestSortBy
    Sort by a field

direction : AgentDocsRouteListRequestDirection
    Sort direction

metadata_filter : str
    JSON string of object that should be used to filter objects by metadata

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
AgentDocsRouteListResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.agent_docs_route_list(
        id="id",
        limit=1,
        offset=1,
        sort_by="created_at",
        direction="asc",
        metadata_filter="metadata_filter",
    )

asyncio.run(main())

#### Signature

```python
async def agent_docs_route_list(
    self,
    id: CommonUuid,
    limit: CommonLimit,
    offset: CommonOffset,
    sort_by: AgentDocsRouteListRequestSortBy,
    direction: AgentDocsRouteListRequestDirection,
    metadata_filter: str,
    request_options: typing.Optional[RequestOptions] = None,
) -> AgentDocsRouteListResponse: ...
```

### AsyncJulepApi().agent_tools_route_create

[Show source in client.py:5127](../../../../../../julep/api/client.py#L5127)

Create a new tool for this agent

Parameters
----------
id : CommonUuid
    ID of parent resource

name : CommonIdentifierSafeUnicode
    Name of the agent

about : str
    About the agent

model : str
    Model name to use (gpt-4-turbo, gemini-nano etc)

instructions : AgentsCreateAgentRequestInstructions
    Instructions for the agent

metadata : typing.Optional[typing.Dict[str, typing.Any]]

default_settings : typing.Optional[ChatDefaultChatSettings]
    Default settings for all sessions created by this agent

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceCreatedResponse
    The request has succeeded and a new resource has been created as a result.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.agent_tools_route_create(
        id="id",
        name="name",
        about="about",
        model="model",
        instructions="instructions",
    )

asyncio.run(main())

#### Signature

```python
async def agent_tools_route_create(
    self,
    id: CommonUuid,
    name: CommonIdentifierSafeUnicode,
    about: str,
    model: str,
    instructions: AgentsCreateAgentRequestInstructions,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    default_settings: typing.Optional[ChatDefaultChatSettings] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceCreatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().agent_tools_route_delete

[Show source in client.py:5309](../../../../../../julep/api/client.py#L5309)

Delete an existing tool by id

Parameters
----------
id : CommonUuid
    ID of parent resource

child_id : CommonUuid
    ID of the resource to be deleted

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceDeletedResponse
    The request has been accepted for processing, but processing has not yet completed.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.agent_tools_route_delete(
        id="id",
        child_id="child_id",
    )

asyncio.run(main())

#### Signature

```python
async def agent_tools_route_delete(
    self,
    id: CommonUuid,
    child_id: CommonUuid,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceDeletedResponse: ...
```

### AsyncJulepApi().agent_tools_route_list

[Show source in client.py:5040](../../../../../../julep/api/client.py#L5040)

List tools of the given agent

Parameters
----------
id : CommonUuid
    ID of parent

limit : CommonLimit
    Limit the number of items returned

offset : CommonOffset
    Offset the items returned

sort_by : AgentToolsRouteListRequestSortBy
    Sort by a field

direction : AgentToolsRouteListRequestDirection
    Sort direction

metadata_filter : str
    JSON string of object that should be used to filter objects by metadata

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
AgentToolsRouteListResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.agent_tools_route_list(
        id="id",
        limit=1,
        offset=1,
        sort_by="created_at",
        direction="asc",
        metadata_filter="metadata_filter",
    )

asyncio.run(main())

#### Signature

```python
async def agent_tools_route_list(
    self,
    id: CommonUuid,
    limit: CommonLimit,
    offset: CommonOffset,
    sort_by: AgentToolsRouteListRequestSortBy,
    direction: AgentToolsRouteListRequestDirection,
    metadata_filter: str,
    request_options: typing.Optional[RequestOptions] = None,
) -> AgentToolsRouteListResponse: ...
```

### AsyncJulepApi().agent_tools_route_patch

[Show source in client.py:5369](../../../../../../julep/api/client.py#L5369)

Update an existing tool (merges with existing values)

Parameters
----------
id : CommonUuid
    ID of parent resource

child_id : CommonUuid
    ID of the resource to be patched

type : typing.Optional[ToolsToolType]
    Whether this tool is a `function`, `api_call`, `system` etc. (Only `function` tool supported right now)

name : typing.Optional[CommonValidPythonIdentifier]
    Name of the tool (must be unique for this agent and a valid python identifier string )

function : typing.Optional[ToolsFunctionDef]

integration : typing.Optional[typing.Any]

system : typing.Optional[typing.Any]

api_call : typing.Optional[typing.Any]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.agent_tools_route_patch(
        id="id",
        child_id="child_id",
    )

asyncio.run(main())

#### Signature

```python
async def agent_tools_route_patch(
    self,
    id: CommonUuid,
    child_id: CommonUuid,
    type: typing.Optional[ToolsToolType] = OMIT,
    name: typing.Optional[CommonValidPythonIdentifier] = OMIT,
    function: typing.Optional[ToolsFunctionDef] = OMIT,
    integration: typing.Optional[typing.Any] = OMIT,
    system: typing.Optional[typing.Any] = OMIT,
    api_call: typing.Optional[typing.Any] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().agent_tools_route_update

[Show source in client.py:5218](../../../../../../julep/api/client.py#L5218)

Update an existing tool (overwrite existing values)

Parameters
----------
id : CommonUuid
    ID of parent resource

child_id : CommonUuid
    ID of the resource to be updated

type : ToolsToolType
    Whether this tool is a `function`, `api_call`, `system` etc. (Only `function` tool supported right now)

name : CommonValidPythonIdentifier
    Name of the tool (must be unique for this agent and a valid python identifier string )

function : typing.Optional[ToolsFunctionDef]

integration : typing.Optional[typing.Any]

system : typing.Optional[typing.Any]

api_call : typing.Optional[typing.Any]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.agent_tools_route_update(
        id="id",
        child_id="child_id",
        type="function",
        name="name",
    )

asyncio.run(main())

#### Signature

```python
async def agent_tools_route_update(
    self,
    id: CommonUuid,
    child_id: CommonUuid,
    type: ToolsToolType,
    name: CommonValidPythonIdentifier,
    function: typing.Optional[ToolsFunctionDef] = OMIT,
    integration: typing.Optional[typing.Any] = OMIT,
    system: typing.Optional[typing.Any] = OMIT,
    api_call: typing.Optional[typing.Any] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().agents_docs_search_route_search

[Show source in client.py:4534](../../../../../../julep/api/client.py#L4534)

Search Docs owned by an Agent

Parameters
----------
id : CommonUuid
    ID of the parent

body : AgentsDocsSearchRouteSearchRequestBody

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
DocsDocSearchResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep import DocsVectorDocSearchRequest
from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.agents_docs_search_route_search(
        id="id",
        body=DocsVectorDocSearchRequest(
            limit=1,
            confidence=1.1,
            vector=[1.1],
        ),
    )

asyncio.run(main())

#### Signature

```python
async def agents_docs_search_route_search(
    self,
    id: CommonUuid,
    body: AgentsDocsSearchRouteSearchRequestBody,
    request_options: typing.Optional[RequestOptions] = None,
) -> DocsDocSearchResponse: ...
```

### AsyncJulepApi().agents_route_create

[Show source in client.py:3859](../../../../../../julep/api/client.py#L3859)

Create a new Agent

Parameters
----------
name : CommonIdentifierSafeUnicode
    Name of the agent

about : str
    About the agent

model : str
    Model name to use (gpt-4-turbo, gemini-nano etc)

instructions : AgentsCreateAgentRequestInstructions
    Instructions for the agent

metadata : typing.Optional[typing.Dict[str, typing.Any]]

default_settings : typing.Optional[ChatDefaultChatSettings]
    Default settings for all sessions created by this agent

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceCreatedResponse
    The request has succeeded and a new resource has been created as a result.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.agents_route_create(
        name="name",
        about="about",
        model="model",
        instructions="instructions",
    )

asyncio.run(main())

#### Signature

```python
async def agents_route_create(
    self,
    name: CommonIdentifierSafeUnicode,
    about: str,
    model: str,
    instructions: AgentsCreateAgentRequestInstructions,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    default_settings: typing.Optional[ChatDefaultChatSettings] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceCreatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().agents_route_create_or_update

[Show source in client.py:3997](../../../../../../julep/api/client.py#L3997)

Create or update an Agent

Parameters
----------
id : CommonUuid

name : CommonIdentifierSafeUnicode
    Name of the agent

about : str
    About the agent

model : str
    Model name to use (gpt-4-turbo, gemini-nano etc)

instructions : AgentsUpdateAgentRequestInstructions
    Instructions for the agent

metadata : typing.Optional[typing.Dict[str, typing.Any]]

default_settings : typing.Optional[ChatDefaultChatSettings]
    Default settings for all sessions created by this agent

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.agents_route_create_or_update(
        id="id",
        name="name",
        about="about",
        model="model",
        instructions="instructions",
    )

asyncio.run(main())

#### Signature

```python
async def agents_route_create_or_update(
    self,
    id: CommonUuid,
    name: CommonIdentifierSafeUnicode,
    about: str,
    model: str,
    instructions: AgentsUpdateAgentRequestInstructions,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    default_settings: typing.Optional[ChatDefaultChatSettings] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().agents_route_delete

[Show source in client.py:4178](../../../../../../julep/api/client.py#L4178)

Delete Agent by id

Parameters
----------
id : CommonUuid
    ID of the resource

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceDeletedResponse
    The request has been accepted for processing, but processing has not yet completed.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.agents_route_delete(
        id="id",
    )

asyncio.run(main())

#### Signature

```python
async def agents_route_delete(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> CommonResourceDeletedResponse: ...
```

### AsyncJulepApi().agents_route_get

[Show source in client.py:3945](../../../../../../julep/api/client.py#L3945)

Get an Agent by id

Parameters
----------
id : CommonUuid
    ID of the resource

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
AgentsAgent
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.agents_route_get(
        id="id",
    )

asyncio.run(main())

#### Signature

```python
async def agents_route_get(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> AgentsAgent: ...
```

### AsyncJulepApi().agents_route_list

[Show source in client.py:3777](../../../../../../julep/api/client.py#L3777)

List Agents (paginated)

Parameters
----------
limit : CommonLimit
    Limit the number of items returned

offset : CommonOffset
    Offset the items returned

sort_by : AgentsRouteListRequestSortBy
    Sort by a field

direction : AgentsRouteListRequestDirection
    Sort direction

metadata_filter : str
    JSON string of object that should be used to filter objects by metadata

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
AgentsRouteListResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.agents_route_list(
        limit=1,
        offset=1,
        sort_by="created_at",
        direction="asc",
        metadata_filter="metadata_filter",
    )

asyncio.run(main())

#### Signature

```python
async def agents_route_list(
    self,
    limit: CommonLimit,
    offset: CommonOffset,
    sort_by: AgentsRouteListRequestSortBy,
    direction: AgentsRouteListRequestDirection,
    metadata_filter: str,
    request_options: typing.Optional[RequestOptions] = None,
) -> AgentsRouteListResponse: ...
```

### AsyncJulepApi().agents_route_patch

[Show source in client.py:4230](../../../../../../julep/api/client.py#L4230)

Update an existing Agent by id (merges with existing values)

Parameters
----------
id : CommonUuid
    ID of the resource

metadata : typing.Optional[typing.Dict[str, typing.Any]]

name : typing.Optional[CommonIdentifierSafeUnicode]
    Name of the agent

about : typing.Optional[str]
    About the agent

model : typing.Optional[str]
    Model name to use (gpt-4-turbo, gemini-nano etc)

instructions : typing.Optional[AgentsPatchAgentRequestInstructions]
    Instructions for the agent

default_settings : typing.Optional[ChatDefaultChatSettings]
    Default settings for all sessions created by this agent

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.agents_route_patch(
        id="id",
    )

asyncio.run(main())

#### Signature

```python
async def agents_route_patch(
    self,
    id: CommonUuid,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    name: typing.Optional[CommonIdentifierSafeUnicode] = OMIT,
    about: typing.Optional[str] = OMIT,
    model: typing.Optional[str] = OMIT,
    instructions: typing.Optional[AgentsPatchAgentRequestInstructions] = OMIT,
    default_settings: typing.Optional[ChatDefaultChatSettings] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().agents_route_update

[Show source in client.py:4087](../../../../../../julep/api/client.py#L4087)

Update an existing Agent by id (overwrites existing values; use PATCH for merging instead)

Parameters
----------
id : CommonUuid
    ID of the resource

name : CommonIdentifierSafeUnicode
    Name of the agent

about : str
    About the agent

model : str
    Model name to use (gpt-4-turbo, gemini-nano etc)

instructions : AgentsUpdateAgentRequestInstructions
    Instructions for the agent

metadata : typing.Optional[typing.Dict[str, typing.Any]]

default_settings : typing.Optional[ChatDefaultChatSettings]
    Default settings for all sessions created by this agent

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.agents_route_update(
        id="id",
        name="name",
        about="about",
        model="model",
        instructions="instructions",
    )

asyncio.run(main())

#### Signature

```python
async def agents_route_update(
    self,
    id: CommonUuid,
    name: CommonIdentifierSafeUnicode,
    about: str,
    model: str,
    instructions: AgentsUpdateAgentRequestInstructions,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    default_settings: typing.Optional[ChatDefaultChatSettings] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().chat_route_generate

[Show source in client.py:6541](../../../../../../julep/api/client.py#L6541)

Generate a response from the model

Parameters
----------
id : CommonUuid
    The session ID

remember : bool
    DISABLED: Whether this interaction should form new memories or not (will be enabled in a future release)

recall : bool
    Whether previous memories and docs should be recalled or not

save : bool
    Whether this interaction should be stored in the session history or not

stream : bool
    Indicates if the server should stream the response as it's generated

messages : typing.Sequence[EntriesInputChatMlMessage]
    A list of new input messages comprising the conversation so far.

model : typing.Optional[CommonIdentifierSafeUnicode]
    Identifier of the model to be used

stop : typing.Optional[typing.Sequence[str]]
    Up to 4 sequences where the API will stop generating further tokens.

seed : typing.Optional[int]
    If specified, the system will make a best effort to sample deterministically for that particular seed value

max_tokens : typing.Optional[int]
    The maximum number of tokens to generate in the chat completion

logit_bias : typing.Optional[typing.Dict[str, CommonLogitBias]]
    Modify the likelihood of specified tokens appearing in the completion

response_format : typing.Optional[ChatCompletionResponseFormat]
    Response format (set to `json_object` to restrict output to JSON)

agent : typing.Optional[CommonUuid]
    Agent ID of the agent to use for this interaction. (Only applicable for multi-agent sessions)

repetition_penalty : typing.Optional[float]
    Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.

length_penalty : typing.Optional[float]
    Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated.

min_p : typing.Optional[float]
    Minimum probability compared to leading token to be considered

frequency_penalty : typing.Optional[float]
    Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.

presence_penalty : typing.Optional[float]
    Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.

temperature : typing.Optional[float]
    What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.

top_p : typing.Optional[float]
    Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both.

tools : typing.Optional[typing.Sequence[ToolsFunctionTool]]
    (Advanced) List of tools that are provided in addition to agent's default set of tools.

tool_choice : typing.Optional[ChatChatInputDataToolChoice]
    Can be one of existing tools given to the agent earlier or the ones provided in this request.

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
ChatRouteGenerateResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep import EntriesInputChatMlMessage
from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.chat_route_generate(
        id="id",
        messages=[
            EntriesInputChatMlMessage(
                role="user",
                content="content",
            )
        ],
        remember=True,
        recall=True,
        save=True,
        stream=True,
    )

asyncio.run(main())

#### Signature

```python
async def chat_route_generate(
    self,
    id: CommonUuid,
    remember: bool,
    recall: bool,
    save: bool,
    stream: bool,
    messages: typing.Sequence[EntriesInputChatMlMessage],
    model: typing.Optional[CommonIdentifierSafeUnicode] = OMIT,
    stop: typing.Optional[typing.Sequence[str]] = OMIT,
    seed: typing.Optional[int] = OMIT,
    max_tokens: typing.Optional[int] = OMIT,
    logit_bias: typing.Optional[typing.Dict[str, CommonLogitBias]] = OMIT,
    response_format: typing.Optional[ChatCompletionResponseFormat] = OMIT,
    agent: typing.Optional[CommonUuid] = OMIT,
    repetition_penalty: typing.Optional[float] = OMIT,
    length_penalty: typing.Optional[float] = OMIT,
    min_p: typing.Optional[float] = OMIT,
    frequency_penalty: typing.Optional[float] = OMIT,
    presence_penalty: typing.Optional[float] = OMIT,
    temperature: typing.Optional[float] = OMIT,
    top_p: typing.Optional[float] = OMIT,
    tools: typing.Optional[typing.Sequence[ToolsFunctionTool]] = OMIT,
    tool_choice: typing.Optional[ChatChatInputDataToolChoice] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> ChatRouteGenerateResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().embed_route_embed

[Show source in client.py:5615](../../../../../../julep/api/client.py#L5615)

Embed a query for search

Parameters
----------
body : DocsEmbedQueryRequest

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
DocsEmbedQueryResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep import DocsEmbedQueryRequest
from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.embed_route_embed(
        body=DocsEmbedQueryRequest(
            text="text",
        ),
    )

asyncio.run(main())

#### Signature

```python
async def embed_route_embed(
    self,
    body: DocsEmbedQueryRequest,
    request_options: typing.Optional[RequestOptions] = None,
) -> DocsEmbedQueryResponse: ...
```

### AsyncJulepApi().execution_transitions_route_list

[Show source in client.py:5852](../../../../../../julep/api/client.py#L5852)

List the Transitions of an Execution by id

Parameters
----------
id : CommonUuid
    ID of parent

limit : CommonLimit
    Limit the number of items returned

offset : CommonOffset
    Offset the items returned

sort_by : ExecutionTransitionsRouteListRequestSortBy
    Sort by a field

direction : ExecutionTransitionsRouteListRequestDirection
    Sort direction

metadata_filter : str
    JSON string of object that should be used to filter objects by metadata

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
ExecutionTransitionsRouteListResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.execution_transitions_route_list(
        id="id",
        limit=1,
        offset=1,
        sort_by="created_at",
        direction="asc",
        metadata_filter="metadata_filter",
    )

asyncio.run(main())

#### Signature

```python
async def execution_transitions_route_list(
    self,
    id: CommonUuid,
    limit: CommonLimit,
    offset: CommonOffset,
    sort_by: ExecutionTransitionsRouteListRequestSortBy,
    direction: ExecutionTransitionsRouteListRequestDirection,
    metadata_filter: str,
    request_options: typing.Optional[RequestOptions] = None,
) -> ExecutionTransitionsRouteListResponse: ...
```

### AsyncJulepApi().executions_route_get

[Show source in client.py:5736](../../../../../../julep/api/client.py#L5736)

Get an Execution by id

Parameters
----------
id : CommonUuid
    ID of the resource

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
ExecutionsExecution
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.executions_route_get(
        id="id",
    )

asyncio.run(main())

#### Signature

```python
async def executions_route_get(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> ExecutionsExecution: ...
```

### AsyncJulepApi().executions_route_resume_with_task_token

[Show source in client.py:5674](../../../../../../julep/api/client.py#L5674)

Resume an execution with a task token

Parameters
----------
task_token : str
    A Task Token is a unique identifier for a specific Task Execution.

input : typing.Optional[typing.Dict[str, typing.Any]]
    The input to resume the execution with

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.executions_route_resume_with_task_token(
        task_token="task_token",
    )

asyncio.run(main())

#### Signature

```python
async def executions_route_resume_with_task_token(
    self,
    task_token: str,
    input: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().executions_route_update

[Show source in client.py:5788](../../../../../../julep/api/client.py#L5788)

Update an existing Execution

Parameters
----------
id : CommonUuid
    ID of the resource

request : ExecutionsUpdateExecutionRequest

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep import ExecutionsUpdateExecutionRequest_Cancelled
from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.executions_route_update(
        id="string",
        request=ExecutionsUpdateExecutionRequest_Cancelled(
            reason="string",
        ),
    )

asyncio.run(main())

#### Signature

```python
async def executions_route_update(
    self,
    id: CommonUuid,
    request: ExecutionsUpdateExecutionRequest,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

### AsyncJulepApi().history_route_delete

[Show source in client.py:6767](../../../../../../julep/api/client.py#L6767)

Clear the history of a Session (resets the Session)

Parameters
----------
id : CommonUuid
    ID of the resource

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceDeletedResponse
    The request has been accepted for processing, but processing has not yet completed.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.history_route_delete(
        id="id",
    )

asyncio.run(main())

#### Signature

```python
async def history_route_delete(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> CommonResourceDeletedResponse: ...
```

### AsyncJulepApi().history_route_history

[Show source in client.py:6715](../../../../../../julep/api/client.py#L6715)

Get history of a Session

Parameters
----------
id : CommonUuid
    ID of parent

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
EntriesHistory
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.history_route_history(
        id="id",
    )

asyncio.run(main())

#### Signature

```python
async def history_route_history(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> EntriesHistory: ...
```

### AsyncJulepApi().individual_docs_route_get

[Show source in client.py:5563](../../../../../../julep/api/client.py#L5563)

Get Doc by id

Parameters
----------
id : CommonUuid
    ID of the resource

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
DocsDoc
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.individual_docs_route_get(
        id="id",
    )

asyncio.run(main())

#### Signature

```python
async def individual_docs_route_get(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> DocsDoc: ...
```

### AsyncJulepApi().job_route_get

[Show source in client.py:5939](../../../../../../julep/api/client.py#L5939)

Get the status of an existing Job by its id

Parameters
----------
id : CommonUuid
    ID of the resource

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
JobsJobStatus
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.job_route_get(
        id="id",
    )

asyncio.run(main())

#### Signature

```python
async def job_route_get(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> JobsJobStatus: ...
```

### AsyncJulepApi().sessions_route_create

[Show source in client.py:6073](../../../../../../julep/api/client.py#L6073)

Create a new session

Parameters
----------
situation : str
    A specific situation that sets the background for this session

render_templates : bool
    Render system and assistant message content as jinja templates

user : typing.Optional[CommonUuid]
    User ID of user associated with this session

users : typing.Optional[typing.Sequence[CommonUuid]]

agent : typing.Optional[CommonUuid]
    Agent ID of agent associated with this session

agents : typing.Optional[typing.Sequence[CommonUuid]]

token_budget : typing.Optional[int]
    Threshold value for the adaptive context functionality

context_overflow : typing.Optional[SessionsContextOverflowType]
    Action to start on context window overflow

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceCreatedResponse
    The request has succeeded and a new resource has been created as a result.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.sessions_route_create(
        situation="situation",
        render_templates=True,
    )

asyncio.run(main())

#### Signature

```python
async def sessions_route_create(
    self,
    situation: str,
    render_templates: bool,
    user: typing.Optional[CommonUuid] = OMIT,
    users: typing.Optional[typing.Sequence[CommonUuid]] = OMIT,
    agent: typing.Optional[CommonUuid] = OMIT,
    agents: typing.Optional[typing.Sequence[CommonUuid]] = OMIT,
    token_budget: typing.Optional[int] = OMIT,
    context_overflow: typing.Optional[SessionsContextOverflowType] = OMIT,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceCreatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().sessions_route_create_or_update

[Show source in client.py:6222](../../../../../../julep/api/client.py#L6222)

Create or update a session

Parameters
----------
id : CommonUuid

situation : str
    A specific situation that sets the background for this session

render_templates : bool
    Render system and assistant message content as jinja templates

user : typing.Optional[CommonUuid]
    User ID of user associated with this session

users : typing.Optional[typing.Sequence[CommonUuid]]

agent : typing.Optional[CommonUuid]
    Agent ID of agent associated with this session

agents : typing.Optional[typing.Sequence[CommonUuid]]

token_budget : typing.Optional[int]
    Threshold value for the adaptive context functionality

context_overflow : typing.Optional[SessionsContextOverflowType]
    Action to start on context window overflow

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.sessions_route_create_or_update(
        id="id",
        situation="situation",
        render_templates=True,
    )

asyncio.run(main())

#### Signature

```python
async def sessions_route_create_or_update(
    self,
    id: CommonUuid,
    situation: str,
    render_templates: bool,
    user: typing.Optional[CommonUuid] = OMIT,
    users: typing.Optional[typing.Sequence[CommonUuid]] = OMIT,
    agent: typing.Optional[CommonUuid] = OMIT,
    agents: typing.Optional[typing.Sequence[CommonUuid]] = OMIT,
    token_budget: typing.Optional[int] = OMIT,
    context_overflow: typing.Optional[SessionsContextOverflowType] = OMIT,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().sessions_route_delete

[Show source in client.py:6407](../../../../../../julep/api/client.py#L6407)

Delete a session by its id

Parameters
----------
id : CommonUuid
    ID of the resource

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceDeletedResponse
    The request has been accepted for processing, but processing has not yet completed.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.sessions_route_delete(
        id="id",
    )

asyncio.run(main())

#### Signature

```python
async def sessions_route_delete(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> CommonResourceDeletedResponse: ...
```

### AsyncJulepApi().sessions_route_get

[Show source in client.py:6170](../../../../../../julep/api/client.py#L6170)

Get a session by id

Parameters
----------
id : CommonUuid
    ID of the resource

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
SessionsSession
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.sessions_route_get(
        id="string",
    )

asyncio.run(main())

#### Signature

```python
async def sessions_route_get(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> SessionsSession: ...
```

### AsyncJulepApi().sessions_route_list

[Show source in client.py:5991](../../../../../../julep/api/client.py#L5991)

List sessions (paginated)

Parameters
----------
limit : CommonLimit
    Limit the number of items returned

offset : CommonOffset
    Offset the items returned

sort_by : SessionsRouteListRequestSortBy
    Sort by a field

direction : SessionsRouteListRequestDirection
    Sort direction

metadata_filter : str
    JSON string of object that should be used to filter objects by metadata

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
SessionsRouteListResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.sessions_route_list(
        limit=1,
        offset=1,
        sort_by="created_at",
        direction="asc",
        metadata_filter="metadata_filter",
    )

asyncio.run(main())

#### Signature

```python
async def sessions_route_list(
    self,
    limit: CommonLimit,
    offset: CommonOffset,
    sort_by: SessionsRouteListRequestSortBy,
    direction: SessionsRouteListRequestDirection,
    metadata_filter: str,
    request_options: typing.Optional[RequestOptions] = None,
) -> SessionsRouteListResponse: ...
```

### AsyncJulepApi().sessions_route_patch

[Show source in client.py:6459](../../../../../../julep/api/client.py#L6459)

Update an existing session by its id (merges with existing values)

Parameters
----------
id : CommonUuid
    ID of the resource

situation : typing.Optional[str]
    A specific situation that sets the background for this session

render_templates : typing.Optional[bool]
    Render system and assistant message content as jinja templates

token_budget : typing.Optional[int]
    Threshold value for the adaptive context functionality

context_overflow : typing.Optional[SessionsContextOverflowType]
    Action to start on context window overflow

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.sessions_route_patch(
        id="id",
    )

asyncio.run(main())

#### Signature

```python
async def sessions_route_patch(
    self,
    id: CommonUuid,
    situation: typing.Optional[str] = OMIT,
    render_templates: typing.Optional[bool] = OMIT,
    token_budget: typing.Optional[int] = OMIT,
    context_overflow: typing.Optional[SessionsContextOverflowType] = OMIT,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().sessions_route_update

[Show source in client.py:6323](../../../../../../julep/api/client.py#L6323)

Update an existing session by its id (overwrites all existing values)

Parameters
----------
id : CommonUuid
    ID of the resource

situation : str
    A specific situation that sets the background for this session

render_templates : bool
    Render system and assistant message content as jinja templates

token_budget : typing.Optional[int]
    Threshold value for the adaptive context functionality

context_overflow : typing.Optional[SessionsContextOverflowType]
    Action to start on context window overflow

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.sessions_route_update(
        id="id",
        situation="situation",
        render_templates=True,
    )

asyncio.run(main())

#### Signature

```python
async def sessions_route_update(
    self,
    id: CommonUuid,
    situation: str,
    render_templates: bool,
    token_budget: typing.Optional[int] = OMIT,
    context_overflow: typing.Optional[SessionsContextOverflowType] = OMIT,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().task_executions_route_create

[Show source in client.py:6906](../../../../../../julep/api/client.py#L6906)

Create an execution for the given task

Parameters
----------
id : CommonUuid
    ID of parent resource

input : typing.Dict[str, typing.Any]
    The input to the execution

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceCreatedResponse
    The request has succeeded and a new resource has been created as a result.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.task_executions_route_create(
        id="id",
        input={"key": "value"},
    )

asyncio.run(main())

#### Signature

```python
async def task_executions_route_create(
    self,
    id: CommonUuid,
    input: typing.Dict[str, typing.Any],
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceCreatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().task_executions_route_list

[Show source in client.py:6819](../../../../../../julep/api/client.py#L6819)

List executions of the given task

Parameters
----------
id : CommonUuid
    ID of parent

limit : CommonLimit
    Limit the number of items returned

offset : CommonOffset
    Offset the items returned

sort_by : TaskExecutionsRouteListRequestSortBy
    Sort by a field

direction : TaskExecutionsRouteListRequestDirection
    Sort direction

metadata_filter : str
    JSON string of object that should be used to filter objects by metadata

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
TaskExecutionsRouteListResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.task_executions_route_list(
        id="id",
        limit=1,
        offset=1,
        sort_by="created_at",
        direction="asc",
        metadata_filter="metadata_filter",
    )

asyncio.run(main())

#### Signature

```python
async def task_executions_route_list(
    self,
    id: CommonUuid,
    limit: CommonLimit,
    offset: CommonOffset,
    sort_by: TaskExecutionsRouteListRequestSortBy,
    direction: TaskExecutionsRouteListRequestDirection,
    metadata_filter: str,
    request_options: typing.Optional[RequestOptions] = None,
) -> TaskExecutionsRouteListResponse: ...
```

### AsyncJulepApi().tasks_create_or_update_route_create_or_update

[Show source in client.py:5458](../../../../../../julep/api/client.py#L5458)

Create or update a task

Parameters
----------
parent_id : CommonUuid
    ID of the agent

id : CommonUuid

name : str

description : str

main : typing.Sequence[TasksCreateTaskRequestMainItem]
    The entrypoint of the task.

tools : typing.Sequence[TasksTaskTool]
    Tools defined specifically for this task not included in the Agent itself.

inherit_tools : bool
    Whether to inherit tools from the parent agent or not. Defaults to true.

input_schema : typing.Optional[typing.Dict[str, typing.Any]]
    The schema for the input to the task. `null` means all inputs are valid.

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceCreatedResponse
    The request has succeeded and a new resource has been created as a result.

Examples
--------
import asyncio

from julep import TasksTaskTool
from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.tasks_create_or_update_route_create_or_update(
        parent_id="parent_id",
        id="id",
        name="name",
        description="description",
        main=[],
        tools=[
            TasksTaskTool(
                type="function",
                name="name",
            )
        ],
        inherit_tools=True,
    )

asyncio.run(main())

#### Signature

```python
async def tasks_create_or_update_route_create_or_update(
    self,
    parent_id: CommonUuid,
    id: CommonUuid,
    name: str,
    description: str,
    main: typing.Sequence[TasksCreateTaskRequestMainItem],
    tools: typing.Sequence[TasksTaskTool],
    inherit_tools: bool,
    input_schema: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceCreatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().tasks_route_create

[Show source in client.py:4687](../../../../../../julep/api/client.py#L4687)

Create a new task

Parameters
----------
id : CommonUuid
    ID of parent resource

name : str

description : str

main : typing.Sequence[TasksCreateTaskRequestMainItem]
    The entrypoint of the task.

tools : typing.Sequence[TasksTaskTool]
    Tools defined specifically for this task not included in the Agent itself.

inherit_tools : bool
    Whether to inherit tools from the parent agent or not. Defaults to true.

input_schema : typing.Optional[typing.Dict[str, typing.Any]]
    The schema for the input to the task. `null` means all inputs are valid.

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceCreatedResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep import TasksTaskTool
from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.tasks_route_create(
        id="id",
        name="name",
        description="description",
        main=[],
        tools=[
            TasksTaskTool(
                type="function",
                name="name",
            )
        ],
        inherit_tools=True,
    )

asyncio.run(main())

#### Signature

```python
async def tasks_route_create(
    self,
    id: CommonUuid,
    name: str,
    description: str,
    main: typing.Sequence[TasksCreateTaskRequestMainItem],
    tools: typing.Sequence[TasksTaskTool],
    inherit_tools: bool,
    input_schema: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceCreatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().tasks_route_delete

[Show source in client.py:4889](../../../../../../julep/api/client.py#L4889)

Delete a task by its id

Parameters
----------
id : CommonUuid
    ID of parent resource

child_id : CommonUuid
    ID of the resource to be deleted

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceDeletedResponse
    The request has been accepted for processing, but processing has not yet completed.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.tasks_route_delete(
        id="id",
        child_id="child_id",
    )

asyncio.run(main())

#### Signature

```python
async def tasks_route_delete(
    self,
    id: CommonUuid,
    child_id: CommonUuid,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceDeletedResponse: ...
```

### AsyncJulepApi().tasks_route_list

[Show source in client.py:4600](../../../../../../julep/api/client.py#L4600)

List tasks (paginated)

Parameters
----------
id : CommonUuid
    ID of parent

limit : CommonLimit
    Limit the number of items returned

offset : CommonOffset
    Offset the items returned

sort_by : TasksRouteListRequestSortBy
    Sort by a field

direction : TasksRouteListRequestDirection
    Sort direction

metadata_filter : str
    JSON string of object that should be used to filter objects by metadata

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
TasksRouteListResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.tasks_route_list(
        id="id",
        limit=1,
        offset=1,
        sort_by="created_at",
        direction="asc",
        metadata_filter="metadata_filter",
    )

asyncio.run(main())

#### Signature

```python
async def tasks_route_list(
    self,
    id: CommonUuid,
    limit: CommonLimit,
    offset: CommonOffset,
    sort_by: TasksRouteListRequestSortBy,
    direction: TasksRouteListRequestDirection,
    metadata_filter: str,
    request_options: typing.Optional[RequestOptions] = None,
) -> TasksRouteListResponse: ...
```

### AsyncJulepApi().tasks_route_patch

[Show source in client.py:4949](../../../../../../julep/api/client.py#L4949)

Update an existing task (merges with existing values)

Parameters
----------
id : CommonUuid
    ID of parent resource

child_id : CommonUuid
    ID of the resource to be patched

description : typing.Optional[str]

main : typing.Optional[typing.Sequence[TasksPatchTaskRequestMainItem]]
    The entrypoint of the task.

input_schema : typing.Optional[typing.Dict[str, typing.Any]]
    The schema for the input to the task. `null` means all inputs are valid.

tools : typing.Optional[typing.Sequence[TasksTaskTool]]
    Tools defined specifically for this task not included in the Agent itself.

inherit_tools : typing.Optional[bool]
    Whether to inherit tools from the parent agent or not. Defaults to true.

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.tasks_route_patch(
        id="id",
        child_id="child_id",
    )

asyncio.run(main())

#### Signature

```python
async def tasks_route_patch(
    self,
    id: CommonUuid,
    child_id: CommonUuid,
    description: typing.Optional[str] = OMIT,
    main: typing.Optional[typing.Sequence[TasksPatchTaskRequestMainItem]] = OMIT,
    input_schema: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    tools: typing.Optional[typing.Sequence[TasksTaskTool]] = OMIT,
    inherit_tools: typing.Optional[bool] = OMIT,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().tasks_route_update

[Show source in client.py:4788](../../../../../../julep/api/client.py#L4788)

Update an existing task (overwrite existing values)

Parameters
----------
id : CommonUuid
    ID of parent resource

child_id : CommonUuid
    ID of the resource to be updated

description : str

main : typing.Sequence[TasksUpdateTaskRequestMainItem]
    The entrypoint of the task.

tools : typing.Sequence[TasksTaskTool]
    Tools defined specifically for this task not included in the Agent itself.

inherit_tools : bool
    Whether to inherit tools from the parent agent or not. Defaults to true.

input_schema : typing.Optional[typing.Dict[str, typing.Any]]
    The schema for the input to the task. `null` means all inputs are valid.

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep import TasksTaskTool
from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.tasks_route_update(
        id="id",
        child_id="child_id",
        description="description",
        main=[],
        tools=[
            TasksTaskTool(
                type="function",
                name="name",
            )
        ],
        inherit_tools=True,
    )

asyncio.run(main())

#### Signature

```python
async def tasks_route_update(
    self,
    id: CommonUuid,
    child_id: CommonUuid,
    description: str,
    main: typing.Sequence[TasksUpdateTaskRequestMainItem],
    tools: typing.Sequence[TasksTaskTool],
    inherit_tools: bool,
    input_schema: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().user_docs_route_create

[Show source in client.py:7516](../../../../../../julep/api/client.py#L7516)

Create a Doc for this User

Parameters
----------
id : CommonUuid
    ID of parent resource

title : CommonIdentifierSafeUnicode
    Title describing what this document contains

content : DocsCreateDocRequestContent
    Contents of the document

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceCreatedResponse
    The request has succeeded and a new resource has been created as a result.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.user_docs_route_create(
        id="id",
        title="title",
        content="content",
    )

asyncio.run(main())

#### Signature

```python
async def user_docs_route_create(
    self,
    id: CommonUuid,
    title: CommonIdentifierSafeUnicode,
    content: DocsCreateDocRequestContent,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceCreatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().user_docs_route_delete

[Show source in client.py:7586](../../../../../../julep/api/client.py#L7586)

Delete a Doc for this User

Parameters
----------
id : CommonUuid
    ID of parent resource

child_id : CommonUuid
    ID of the resource to be deleted

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceDeletedResponse
    The request has been accepted for processing, but processing has not yet completed.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.user_docs_route_delete(
        id="id",
        child_id="child_id",
    )

asyncio.run(main())

#### Signature

```python
async def user_docs_route_delete(
    self,
    id: CommonUuid,
    child_id: CommonUuid,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceDeletedResponse: ...
```

### AsyncJulepApi().user_docs_route_list

[Show source in client.py:7429](../../../../../../julep/api/client.py#L7429)

List Docs owned by a User

Parameters
----------
id : CommonUuid
    ID of parent

limit : CommonLimit
    Limit the number of items returned

offset : CommonOffset
    Offset the items returned

sort_by : UserDocsRouteListRequestSortBy
    Sort by a field

direction : UserDocsRouteListRequestDirection
    Sort direction

metadata_filter : str
    JSON string of object that should be used to filter objects by metadata

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
UserDocsRouteListResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.user_docs_route_list(
        id="id",
        limit=1,
        offset=1,
        sort_by="created_at",
        direction="asc",
        metadata_filter="metadata_filter",
    )

asyncio.run(main())

#### Signature

```python
async def user_docs_route_list(
    self,
    id: CommonUuid,
    limit: CommonLimit,
    offset: CommonOffset,
    sort_by: UserDocsRouteListRequestSortBy,
    direction: UserDocsRouteListRequestDirection,
    metadata_filter: str,
    request_options: typing.Optional[RequestOptions] = None,
) -> UserDocsRouteListResponse: ...
```

### AsyncJulepApi().user_docs_search_route_search

[Show source in client.py:7646](../../../../../../julep/api/client.py#L7646)

Search Docs owned by a User

Parameters
----------
id : CommonUuid
    ID of the parent

body : UserDocsSearchRouteSearchRequestBody

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
DocsDocSearchResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep import DocsVectorDocSearchRequest
from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.user_docs_search_route_search(
        id="id",
        body=DocsVectorDocSearchRequest(
            limit=1,
            confidence=1.1,
            vector=[1.1],
        ),
    )

asyncio.run(main())

#### Signature

```python
async def user_docs_search_route_search(
    self,
    id: CommonUuid,
    body: UserDocsSearchRouteSearchRequestBody,
    request_options: typing.Optional[RequestOptions] = None,
) -> DocsDocSearchResponse: ...
```

### AsyncJulepApi().users_route_create

[Show source in client.py:7053](../../../../../../julep/api/client.py#L7053)

Create a new user

Parameters
----------
name : CommonIdentifierSafeUnicode
    Name of the user

about : str
    About the user

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceCreatedResponse
    The request has succeeded and a new resource has been created as a result.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.users_route_create(
        name="name",
        about="about",
    )

asyncio.run(main())

#### Signature

```python
async def users_route_create(
    self,
    name: CommonIdentifierSafeUnicode,
    about: str,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceCreatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().users_route_create_or_update

[Show source in client.py:7170](../../../../../../julep/api/client.py#L7170)

Create or update a user

Parameters
----------
id : CommonUuid

name : CommonIdentifierSafeUnicode
    Name of the user

about : str
    About the user

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.users_route_create_or_update(
        id="id",
        name="name",
        about="about",
    )

asyncio.run(main())

#### Signature

```python
async def users_route_create_or_update(
    self,
    id: CommonUuid,
    name: CommonIdentifierSafeUnicode,
    about: str,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().users_route_delete

[Show source in client.py:7309](../../../../../../julep/api/client.py#L7309)

Delete a user by id

Parameters
----------
id : CommonUuid
    ID of the resource

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceDeletedResponse
    The request has been accepted for processing, but processing has not yet completed.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.users_route_delete(
        id="id",
    )

asyncio.run(main())

#### Signature

```python
async def users_route_delete(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> CommonResourceDeletedResponse: ...
```

### AsyncJulepApi().users_route_get

[Show source in client.py:7118](../../../../../../julep/api/client.py#L7118)

Get a user by id

Parameters
----------
id : CommonUuid
    ID of the resource

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
UsersUser
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.users_route_get(
        id="id",
    )

asyncio.run(main())

#### Signature

```python
async def users_route_get(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> UsersUser: ...
```

### AsyncJulepApi().users_route_list

[Show source in client.py:6971](../../../../../../julep/api/client.py#L6971)

List users (paginated)

Parameters
----------
limit : CommonLimit
    Limit the number of items returned

offset : CommonOffset
    Offset the items returned

sort_by : UsersRouteListRequestSortBy
    Sort by a field

direction : UsersRouteListRequestDirection
    Sort direction

metadata_filter : str
    JSON string of object that should be used to filter objects by metadata

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
UsersRouteListResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.users_route_list(
        limit=1,
        offset=1,
        sort_by="created_at",
        direction="asc",
        metadata_filter="metadata_filter",
    )

asyncio.run(main())

#### Signature

```python
async def users_route_list(
    self,
    limit: CommonLimit,
    offset: CommonOffset,
    sort_by: UsersRouteListRequestSortBy,
    direction: UsersRouteListRequestDirection,
    metadata_filter: str,
    request_options: typing.Optional[RequestOptions] = None,
) -> UsersRouteListResponse: ...
```

### AsyncJulepApi().users_route_patch

[Show source in client.py:7361](../../../../../../julep/api/client.py#L7361)

Update an existing user by id (merge with existing values)

Parameters
----------
id : CommonUuid
    ID of the resource

metadata : typing.Optional[typing.Dict[str, typing.Any]]

name : typing.Optional[CommonIdentifierSafeUnicode]
    Name of the user

about : typing.Optional[str]
    About the user

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.users_route_patch(
        id="id",
    )

asyncio.run(main())

#### Signature

```python
async def users_route_patch(
    self,
    id: CommonUuid,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    name: typing.Optional[CommonIdentifierSafeUnicode] = OMIT,
    about: typing.Optional[str] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### AsyncJulepApi().users_route_update

[Show source in client.py:7239](../../../../../../julep/api/client.py#L7239)

Update an existing user by id (overwrite existing values)

Parameters
----------
id : CommonUuid
    ID of the resource

name : CommonIdentifierSafeUnicode
    Name of the user

about : str
    About the user

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
import asyncio

from julep.client import AsyncJulepApi

client = AsyncJulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

async def main() -> None:
    await client.users_route_update(
        id="id",
        name="name",
        about="about",
    )

asyncio.run(main())

#### Signature

```python
async def users_route_update(
    self,
    id: CommonUuid,
    name: CommonIdentifierSafeUnicode,
    about: str,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)



## JulepApi

[Show source in client.py:115](../../../../../../julep/api/client.py#L115)

Use this class to access the different functions within the SDK. You can instantiate any number of clients with different configuration that will propagate to these functions.

Parameters
----------
base_url : typing.Optional[str]
    The base url to use for requests from the client.

environment : JulepApiEnvironment
    The environment to use for requests from the client. from .environment import JulepApiEnvironment

Defaults to JulepApiEnvironment.DEFAULT

auth_key : str
api_key : str
timeout : typing.Optional[float]
    The timeout to be used, in seconds, for requests. By default the timeout is 300 seconds, unless a custom httpx client is used, in which case this default is not enforced.

follow_redirects : typing.Optional[bool]
    Whether the default httpx client follows redirects or not, this is irrelevant if a custom httpx client is passed in.

httpx_client : typing.Optional[httpx.Client]
    The httpx client to use for making requests, a preconfigured client is used by default, however this is useful should you want to pass in any custom httpx configuration.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)

#### Signature

```python
class JulepApi:
    def __init__(
        self,
        base_url: typing.Optional[str] = None,
        environment: JulepApiEnvironment = JulepApiEnvironment.DEFAULT,
        auth_key: str,
        api_key: str,
        timeout: typing.Optional[float] = None,
        follow_redirects: typing.Optional[bool] = True,
        httpx_client: typing.Optional[httpx.Client] = None,
    ): ...
```

### JulepApi().agent_docs_route_create

[Show source in client.py:749](../../../../../../julep/api/client.py#L749)

Create a Doc for this Agent

Parameters
----------
id : CommonUuid
    ID of parent resource

title : CommonIdentifierSafeUnicode
    Title describing what this document contains

content : DocsCreateDocRequestContent
    Contents of the document

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceCreatedResponse
    The request has succeeded and a new resource has been created as a result.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agent_docs_route_create(
    id="id",
    title="title",
    content="content",
)

#### Signature

```python
def agent_docs_route_create(
    self,
    id: CommonUuid,
    title: CommonIdentifierSafeUnicode,
    content: DocsCreateDocRequestContent,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceCreatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().agent_docs_route_delete

[Show source in client.py:811](../../../../../../julep/api/client.py#L811)

Delete a Doc for this Agent

Parameters
----------
id : CommonUuid
    ID of parent resource

child_id : CommonUuid
    ID of the resource to be deleted

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceDeletedResponse
    The request has been accepted for processing, but processing has not yet completed.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agent_docs_route_delete(
    id="id",
    child_id="child_id",
)

#### Signature

```python
def agent_docs_route_delete(
    self,
    id: CommonUuid,
    child_id: CommonUuid,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceDeletedResponse: ...
```

### JulepApi().agent_docs_route_list

[Show source in client.py:670](../../../../../../julep/api/client.py#L670)

List Docs owned by an Agent

Parameters
----------
id : CommonUuid
    ID of parent

limit : CommonLimit
    Limit the number of items returned

offset : CommonOffset
    Offset the items returned

sort_by : AgentDocsRouteListRequestSortBy
    Sort by a field

direction : AgentDocsRouteListRequestDirection
    Sort direction

metadata_filter : str
    JSON string of object that should be used to filter objects by metadata

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
AgentDocsRouteListResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agent_docs_route_list(
    id="id",
    limit=1,
    offset=1,
    sort_by="created_at",
    direction="asc",
    metadata_filter="metadata_filter",
)

#### Signature

```python
def agent_docs_route_list(
    self,
    id: CommonUuid,
    limit: CommonLimit,
    offset: CommonOffset,
    sort_by: AgentDocsRouteListRequestSortBy,
    direction: AgentDocsRouteListRequestDirection,
    metadata_filter: str,
    request_options: typing.Optional[RequestOptions] = None,
) -> AgentDocsRouteListResponse: ...
```

### JulepApi().agent_tools_route_create

[Show source in client.py:1400](../../../../../../julep/api/client.py#L1400)

Create a new tool for this agent

Parameters
----------
id : CommonUuid
    ID of parent resource

name : CommonIdentifierSafeUnicode
    Name of the agent

about : str
    About the agent

model : str
    Model name to use (gpt-4-turbo, gemini-nano etc)

instructions : AgentsCreateAgentRequestInstructions
    Instructions for the agent

metadata : typing.Optional[typing.Dict[str, typing.Any]]

default_settings : typing.Optional[ChatDefaultChatSettings]
    Default settings for all sessions created by this agent

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceCreatedResponse
    The request has succeeded and a new resource has been created as a result.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agent_tools_route_create(
    id="id",
    name="name",
    about="about",
    model="model",
    instructions="instructions",
)

#### Signature

```python
def agent_tools_route_create(
    self,
    id: CommonUuid,
    name: CommonIdentifierSafeUnicode,
    about: str,
    model: str,
    instructions: AgentsCreateAgentRequestInstructions,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    default_settings: typing.Optional[ChatDefaultChatSettings] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceCreatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().agent_tools_route_delete

[Show source in client.py:1566](../../../../../../julep/api/client.py#L1566)

Delete an existing tool by id

Parameters
----------
id : CommonUuid
    ID of parent resource

child_id : CommonUuid
    ID of the resource to be deleted

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceDeletedResponse
    The request has been accepted for processing, but processing has not yet completed.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agent_tools_route_delete(
    id="id",
    child_id="child_id",
)

#### Signature

```python
def agent_tools_route_delete(
    self,
    id: CommonUuid,
    child_id: CommonUuid,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceDeletedResponse: ...
```

### JulepApi().agent_tools_route_list

[Show source in client.py:1321](../../../../../../julep/api/client.py#L1321)

List tools of the given agent

Parameters
----------
id : CommonUuid
    ID of parent

limit : CommonLimit
    Limit the number of items returned

offset : CommonOffset
    Offset the items returned

sort_by : AgentToolsRouteListRequestSortBy
    Sort by a field

direction : AgentToolsRouteListRequestDirection
    Sort direction

metadata_filter : str
    JSON string of object that should be used to filter objects by metadata

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
AgentToolsRouteListResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agent_tools_route_list(
    id="id",
    limit=1,
    offset=1,
    sort_by="created_at",
    direction="asc",
    metadata_filter="metadata_filter",
)

#### Signature

```python
def agent_tools_route_list(
    self,
    id: CommonUuid,
    limit: CommonLimit,
    offset: CommonOffset,
    sort_by: AgentToolsRouteListRequestSortBy,
    direction: AgentToolsRouteListRequestDirection,
    metadata_filter: str,
    request_options: typing.Optional[RequestOptions] = None,
) -> AgentToolsRouteListResponse: ...
```

### JulepApi().agent_tools_route_patch

[Show source in client.py:1618](../../../../../../julep/api/client.py#L1618)

Update an existing tool (merges with existing values)

Parameters
----------
id : CommonUuid
    ID of parent resource

child_id : CommonUuid
    ID of the resource to be patched

type : typing.Optional[ToolsToolType]
    Whether this tool is a `function`, `api_call`, `system` etc. (Only `function` tool supported right now)

name : typing.Optional[CommonValidPythonIdentifier]
    Name of the tool (must be unique for this agent and a valid python identifier string )

function : typing.Optional[ToolsFunctionDef]

integration : typing.Optional[typing.Any]

system : typing.Optional[typing.Any]

api_call : typing.Optional[typing.Any]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agent_tools_route_patch(
    id="id",
    child_id="child_id",
)

#### Signature

```python
def agent_tools_route_patch(
    self,
    id: CommonUuid,
    child_id: CommonUuid,
    type: typing.Optional[ToolsToolType] = OMIT,
    name: typing.Optional[CommonValidPythonIdentifier] = OMIT,
    function: typing.Optional[ToolsFunctionDef] = OMIT,
    integration: typing.Optional[typing.Any] = OMIT,
    system: typing.Optional[typing.Any] = OMIT,
    api_call: typing.Optional[typing.Any] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().agent_tools_route_update

[Show source in client.py:1483](../../../../../../julep/api/client.py#L1483)

Update an existing tool (overwrite existing values)

Parameters
----------
id : CommonUuid
    ID of parent resource

child_id : CommonUuid
    ID of the resource to be updated

type : ToolsToolType
    Whether this tool is a `function`, `api_call`, `system` etc. (Only `function` tool supported right now)

name : CommonValidPythonIdentifier
    Name of the tool (must be unique for this agent and a valid python identifier string )

function : typing.Optional[ToolsFunctionDef]

integration : typing.Optional[typing.Any]

system : typing.Optional[typing.Any]

api_call : typing.Optional[typing.Any]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agent_tools_route_update(
    id="id",
    child_id="child_id",
    type="function",
    name="name",
)

#### Signature

```python
def agent_tools_route_update(
    self,
    id: CommonUuid,
    child_id: CommonUuid,
    type: ToolsToolType,
    name: CommonValidPythonIdentifier,
    function: typing.Optional[ToolsFunctionDef] = OMIT,
    integration: typing.Optional[typing.Any] = OMIT,
    system: typing.Optional[typing.Any] = OMIT,
    api_call: typing.Optional[typing.Any] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().agents_docs_search_route_search

[Show source in client.py:863](../../../../../../julep/api/client.py#L863)

Search Docs owned by an Agent

Parameters
----------
id : CommonUuid
    ID of the parent

body : AgentsDocsSearchRouteSearchRequestBody

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
DocsDocSearchResponse
    The request has succeeded.

Examples
--------
from julep import DocsVectorDocSearchRequest
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agents_docs_search_route_search(
    id="id",
    body=DocsVectorDocSearchRequest(
        limit=1,
        confidence=1.1,
        vector=[1.1],
    ),
)

#### Signature

```python
def agents_docs_search_route_search(
    self,
    id: CommonUuid,
    body: AgentsDocsSearchRouteSearchRequestBody,
    request_options: typing.Optional[RequestOptions] = None,
) -> DocsDocSearchResponse: ...
```

### JulepApi().agents_route_create

[Show source in client.py:260](../../../../../../julep/api/client.py#L260)

Create a new Agent

Parameters
----------
name : CommonIdentifierSafeUnicode
    Name of the agent

about : str
    About the agent

model : str
    Model name to use (gpt-4-turbo, gemini-nano etc)

instructions : AgentsCreateAgentRequestInstructions
    Instructions for the agent

metadata : typing.Optional[typing.Dict[str, typing.Any]]

default_settings : typing.Optional[ChatDefaultChatSettings]
    Default settings for all sessions created by this agent

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceCreatedResponse
    The request has succeeded and a new resource has been created as a result.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agents_route_create(
    name="name",
    about="about",
    model="model",
    instructions="instructions",
)

#### Signature

```python
def agents_route_create(
    self,
    name: CommonIdentifierSafeUnicode,
    about: str,
    model: str,
    instructions: AgentsCreateAgentRequestInstructions,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    default_settings: typing.Optional[ChatDefaultChatSettings] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceCreatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().agents_route_create_or_update

[Show source in client.py:382](../../../../../../julep/api/client.py#L382)

Create or update an Agent

Parameters
----------
id : CommonUuid

name : CommonIdentifierSafeUnicode
    Name of the agent

about : str
    About the agent

model : str
    Model name to use (gpt-4-turbo, gemini-nano etc)

instructions : AgentsUpdateAgentRequestInstructions
    Instructions for the agent

metadata : typing.Optional[typing.Dict[str, typing.Any]]

default_settings : typing.Optional[ChatDefaultChatSettings]
    Default settings for all sessions created by this agent

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agents_route_create_or_update(
    id="id",
    name="name",
    about="about",
    model="model",
    instructions="instructions",
)

#### Signature

```python
def agents_route_create_or_update(
    self,
    id: CommonUuid,
    name: CommonIdentifierSafeUnicode,
    about: str,
    model: str,
    instructions: AgentsUpdateAgentRequestInstructions,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    default_settings: typing.Optional[ChatDefaultChatSettings] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().agents_route_delete

[Show source in client.py:547](../../../../../../julep/api/client.py#L547)

Delete Agent by id

Parameters
----------
id : CommonUuid
    ID of the resource

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceDeletedResponse
    The request has been accepted for processing, but processing has not yet completed.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agents_route_delete(
    id="id",
)

#### Signature

```python
def agents_route_delete(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> CommonResourceDeletedResponse: ...
```

### JulepApi().agents_route_get

[Show source in client.py:338](../../../../../../julep/api/client.py#L338)

Get an Agent by id

Parameters
----------
id : CommonUuid
    ID of the resource

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
AgentsAgent
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agents_route_get(
    id="id",
)

#### Signature

```python
def agents_route_get(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> AgentsAgent: ...
```

### JulepApi().agents_route_list

[Show source in client.py:186](../../../../../../julep/api/client.py#L186)

List Agents (paginated)

Parameters
----------
limit : CommonLimit
    Limit the number of items returned

offset : CommonOffset
    Offset the items returned

sort_by : AgentsRouteListRequestSortBy
    Sort by a field

direction : AgentsRouteListRequestDirection
    Sort direction

metadata_filter : str
    JSON string of object that should be used to filter objects by metadata

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
AgentsRouteListResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agents_route_list(
    limit=1,
    offset=1,
    sort_by="created_at",
    direction="asc",
    metadata_filter="metadata_filter",
)

#### Signature

```python
def agents_route_list(
    self,
    limit: CommonLimit,
    offset: CommonOffset,
    sort_by: AgentsRouteListRequestSortBy,
    direction: AgentsRouteListRequestDirection,
    metadata_filter: str,
    request_options: typing.Optional[RequestOptions] = None,
) -> AgentsRouteListResponse: ...
```

### JulepApi().agents_route_patch

[Show source in client.py:591](../../../../../../julep/api/client.py#L591)

Update an existing Agent by id (merges with existing values)

Parameters
----------
id : CommonUuid
    ID of the resource

metadata : typing.Optional[typing.Dict[str, typing.Any]]

name : typing.Optional[CommonIdentifierSafeUnicode]
    Name of the agent

about : typing.Optional[str]
    About the agent

model : typing.Optional[str]
    Model name to use (gpt-4-turbo, gemini-nano etc)

instructions : typing.Optional[AgentsPatchAgentRequestInstructions]
    Instructions for the agent

default_settings : typing.Optional[ChatDefaultChatSettings]
    Default settings for all sessions created by this agent

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agents_route_patch(
    id="id",
)

#### Signature

```python
def agents_route_patch(
    self,
    id: CommonUuid,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    name: typing.Optional[CommonIdentifierSafeUnicode] = OMIT,
    about: typing.Optional[str] = OMIT,
    model: typing.Optional[str] = OMIT,
    instructions: typing.Optional[AgentsPatchAgentRequestInstructions] = OMIT,
    default_settings: typing.Optional[ChatDefaultChatSettings] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().agents_route_update

[Show source in client.py:464](../../../../../../julep/api/client.py#L464)

Update an existing Agent by id (overwrites existing values; use PATCH for merging instead)

Parameters
----------
id : CommonUuid
    ID of the resource

name : CommonIdentifierSafeUnicode
    Name of the agent

about : str
    About the agent

model : str
    Model name to use (gpt-4-turbo, gemini-nano etc)

instructions : AgentsUpdateAgentRequestInstructions
    Instructions for the agent

metadata : typing.Optional[typing.Dict[str, typing.Any]]

default_settings : typing.Optional[ChatDefaultChatSettings]
    Default settings for all sessions created by this agent

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agents_route_update(
    id="id",
    name="name",
    about="about",
    model="model",
    instructions="instructions",
)

#### Signature

```python
def agents_route_update(
    self,
    id: CommonUuid,
    name: CommonIdentifierSafeUnicode,
    about: str,
    model: str,
    instructions: AgentsUpdateAgentRequestInstructions,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    default_settings: typing.Optional[ChatDefaultChatSettings] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().chat_route_generate

[Show source in client.py:2662](../../../../../../julep/api/client.py#L2662)

Generate a response from the model

Parameters
----------
id : CommonUuid
    The session ID

remember : bool
    DISABLED: Whether this interaction should form new memories or not (will be enabled in a future release)

recall : bool
    Whether previous memories and docs should be recalled or not

save : bool
    Whether this interaction should be stored in the session history or not

stream : bool
    Indicates if the server should stream the response as it's generated

messages : typing.Sequence[EntriesInputChatMlMessage]
    A list of new input messages comprising the conversation so far.

model : typing.Optional[CommonIdentifierSafeUnicode]
    Identifier of the model to be used

stop : typing.Optional[typing.Sequence[str]]
    Up to 4 sequences where the API will stop generating further tokens.

seed : typing.Optional[int]
    If specified, the system will make a best effort to sample deterministically for that particular seed value

max_tokens : typing.Optional[int]
    The maximum number of tokens to generate in the chat completion

logit_bias : typing.Optional[typing.Dict[str, CommonLogitBias]]
    Modify the likelihood of specified tokens appearing in the completion

response_format : typing.Optional[ChatCompletionResponseFormat]
    Response format (set to `json_object` to restrict output to JSON)

agent : typing.Optional[CommonUuid]
    Agent ID of the agent to use for this interaction. (Only applicable for multi-agent sessions)

repetition_penalty : typing.Optional[float]
    Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.

length_penalty : typing.Optional[float]
    Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated.

min_p : typing.Optional[float]
    Minimum probability compared to leading token to be considered

frequency_penalty : typing.Optional[float]
    Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.

presence_penalty : typing.Optional[float]
    Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.

temperature : typing.Optional[float]
    What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.

top_p : typing.Optional[float]
    Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both.

tools : typing.Optional[typing.Sequence[ToolsFunctionTool]]
    (Advanced) List of tools that are provided in addition to agent's default set of tools.

tool_choice : typing.Optional[ChatChatInputDataToolChoice]
    Can be one of existing tools given to the agent earlier or the ones provided in this request.

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
ChatRouteGenerateResponse
    The request has succeeded.

Examples
--------
from julep import EntriesInputChatMlMessage
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.chat_route_generate(
    id="id",
    messages=[
        EntriesInputChatMlMessage(
            role="user",
            content="content",
        )
    ],
    remember=True,
    recall=True,
    save=True,
    stream=True,
)

#### Signature

```python
def chat_route_generate(
    self,
    id: CommonUuid,
    remember: bool,
    recall: bool,
    save: bool,
    stream: bool,
    messages: typing.Sequence[EntriesInputChatMlMessage],
    model: typing.Optional[CommonIdentifierSafeUnicode] = OMIT,
    stop: typing.Optional[typing.Sequence[str]] = OMIT,
    seed: typing.Optional[int] = OMIT,
    max_tokens: typing.Optional[int] = OMIT,
    logit_bias: typing.Optional[typing.Dict[str, CommonLogitBias]] = OMIT,
    response_format: typing.Optional[ChatCompletionResponseFormat] = OMIT,
    agent: typing.Optional[CommonUuid] = OMIT,
    repetition_penalty: typing.Optional[float] = OMIT,
    length_penalty: typing.Optional[float] = OMIT,
    min_p: typing.Optional[float] = OMIT,
    frequency_penalty: typing.Optional[float] = OMIT,
    presence_penalty: typing.Optional[float] = OMIT,
    temperature: typing.Optional[float] = OMIT,
    top_p: typing.Optional[float] = OMIT,
    tools: typing.Optional[typing.Sequence[ToolsFunctionTool]] = OMIT,
    tool_choice: typing.Optional[ChatChatInputDataToolChoice] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> ChatRouteGenerateResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().embed_route_embed

[Show source in client.py:1840](../../../../../../julep/api/client.py#L1840)

Embed a query for search

Parameters
----------
body : DocsEmbedQueryRequest

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
DocsEmbedQueryResponse
    The request has succeeded.

Examples
--------
from julep import DocsEmbedQueryRequest
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.embed_route_embed(
    body=DocsEmbedQueryRequest(
        text="text",
    ),
)

#### Signature

```python
def embed_route_embed(
    self,
    body: DocsEmbedQueryRequest,
    request_options: typing.Optional[RequestOptions] = None,
) -> DocsEmbedQueryResponse: ...
```

### JulepApi().execution_transitions_route_list

[Show source in client.py:2045](../../../../../../julep/api/client.py#L2045)

List the Transitions of an Execution by id

Parameters
----------
id : CommonUuid
    ID of parent

limit : CommonLimit
    Limit the number of items returned

offset : CommonOffset
    Offset the items returned

sort_by : ExecutionTransitionsRouteListRequestSortBy
    Sort by a field

direction : ExecutionTransitionsRouteListRequestDirection
    Sort direction

metadata_filter : str
    JSON string of object that should be used to filter objects by metadata

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
ExecutionTransitionsRouteListResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.execution_transitions_route_list(
    id="id",
    limit=1,
    offset=1,
    sort_by="created_at",
    direction="asc",
    metadata_filter="metadata_filter",
)

#### Signature

```python
def execution_transitions_route_list(
    self,
    id: CommonUuid,
    limit: CommonLimit,
    offset: CommonOffset,
    sort_by: ExecutionTransitionsRouteListRequestSortBy,
    direction: ExecutionTransitionsRouteListRequestDirection,
    metadata_filter: str,
    request_options: typing.Optional[RequestOptions] = None,
) -> ExecutionTransitionsRouteListResponse: ...
```

### JulepApi().executions_route_get

[Show source in client.py:1945](../../../../../../julep/api/client.py#L1945)

Get an Execution by id

Parameters
----------
id : CommonUuid
    ID of the resource

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
ExecutionsExecution
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.executions_route_get(
    id="id",
)

#### Signature

```python
def executions_route_get(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> ExecutionsExecution: ...
```

### JulepApi().executions_route_resume_with_task_token

[Show source in client.py:1891](../../../../../../julep/api/client.py#L1891)

Resume an execution with a task token

Parameters
----------
task_token : str
    A Task Token is a unique identifier for a specific Task Execution.

input : typing.Optional[typing.Dict[str, typing.Any]]
    The input to resume the execution with

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.executions_route_resume_with_task_token(
    task_token="task_token",
)

#### Signature

```python
def executions_route_resume_with_task_token(
    self,
    task_token: str,
    input: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().executions_route_update

[Show source in client.py:1989](../../../../../../julep/api/client.py#L1989)

Update an existing Execution

Parameters
----------
id : CommonUuid
    ID of the resource

request : ExecutionsUpdateExecutionRequest

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
from julep import ExecutionsUpdateExecutionRequest_Cancelled
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.executions_route_update(
    id="string",
    request=ExecutionsUpdateExecutionRequest_Cancelled(
        reason="string",
    ),
)

#### Signature

```python
def executions_route_update(
    self,
    id: CommonUuid,
    request: ExecutionsUpdateExecutionRequest,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

### JulepApi().history_route_delete

[Show source in client.py:2872](../../../../../../julep/api/client.py#L2872)

Clear the history of a Session (resets the Session)

Parameters
----------
id : CommonUuid
    ID of the resource

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceDeletedResponse
    The request has been accepted for processing, but processing has not yet completed.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.history_route_delete(
    id="id",
)

#### Signature

```python
def history_route_delete(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> CommonResourceDeletedResponse: ...
```

### JulepApi().history_route_history

[Show source in client.py:2828](../../../../../../julep/api/client.py#L2828)

Get history of a Session

Parameters
----------
id : CommonUuid
    ID of parent

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
EntriesHistory
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.history_route_history(
    id="id",
)

#### Signature

```python
def history_route_history(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> EntriesHistory: ...
```

### JulepApi().individual_docs_route_get

[Show source in client.py:1796](../../../../../../julep/api/client.py#L1796)

Get Doc by id

Parameters
----------
id : CommonUuid
    ID of the resource

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
DocsDoc
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.individual_docs_route_get(
    id="id",
)

#### Signature

```python
def individual_docs_route_get(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> DocsDoc: ...
```

### JulepApi().job_route_get

[Show source in client.py:2124](../../../../../../julep/api/client.py#L2124)

Get the status of an existing Job by its id

Parameters
----------
id : CommonUuid
    ID of the resource

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
JobsJobStatus
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.job_route_get(
    id="id",
)

#### Signature

```python
def job_route_get(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> JobsJobStatus: ...
```

### JulepApi().sessions_route_create

[Show source in client.py:2242](../../../../../../julep/api/client.py#L2242)

Create a new session

Parameters
----------
situation : str
    A specific situation that sets the background for this session

render_templates : bool
    Render system and assistant message content as jinja templates

user : typing.Optional[CommonUuid]
    User ID of user associated with this session

users : typing.Optional[typing.Sequence[CommonUuid]]

agent : typing.Optional[CommonUuid]
    Agent ID of agent associated with this session

agents : typing.Optional[typing.Sequence[CommonUuid]]

token_budget : typing.Optional[int]
    Threshold value for the adaptive context functionality

context_overflow : typing.Optional[SessionsContextOverflowType]
    Action to start on context window overflow

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceCreatedResponse
    The request has succeeded and a new resource has been created as a result.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.sessions_route_create(
    situation="situation",
    render_templates=True,
)

#### Signature

```python
def sessions_route_create(
    self,
    situation: str,
    render_templates: bool,
    user: typing.Optional[CommonUuid] = OMIT,
    users: typing.Optional[typing.Sequence[CommonUuid]] = OMIT,
    agent: typing.Optional[CommonUuid] = OMIT,
    agents: typing.Optional[typing.Sequence[CommonUuid]] = OMIT,
    token_budget: typing.Optional[int] = OMIT,
    context_overflow: typing.Optional[SessionsContextOverflowType] = OMIT,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceCreatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().sessions_route_create_or_update

[Show source in client.py:2375](../../../../../../julep/api/client.py#L2375)

Create or update a session

Parameters
----------
id : CommonUuid

situation : str
    A specific situation that sets the background for this session

render_templates : bool
    Render system and assistant message content as jinja templates

user : typing.Optional[CommonUuid]
    User ID of user associated with this session

users : typing.Optional[typing.Sequence[CommonUuid]]

agent : typing.Optional[CommonUuid]
    Agent ID of agent associated with this session

agents : typing.Optional[typing.Sequence[CommonUuid]]

token_budget : typing.Optional[int]
    Threshold value for the adaptive context functionality

context_overflow : typing.Optional[SessionsContextOverflowType]
    Action to start on context window overflow

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.sessions_route_create_or_update(
    id="id",
    situation="situation",
    render_templates=True,
)

#### Signature

```python
def sessions_route_create_or_update(
    self,
    id: CommonUuid,
    situation: str,
    render_templates: bool,
    user: typing.Optional[CommonUuid] = OMIT,
    users: typing.Optional[typing.Sequence[CommonUuid]] = OMIT,
    agent: typing.Optional[CommonUuid] = OMIT,
    agents: typing.Optional[typing.Sequence[CommonUuid]] = OMIT,
    token_budget: typing.Optional[int] = OMIT,
    context_overflow: typing.Optional[SessionsContextOverflowType] = OMIT,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().sessions_route_delete

[Show source in client.py:2544](../../../../../../julep/api/client.py#L2544)

Delete a session by its id

Parameters
----------
id : CommonUuid
    ID of the resource

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceDeletedResponse
    The request has been accepted for processing, but processing has not yet completed.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.sessions_route_delete(
    id="id",
)

#### Signature

```python
def sessions_route_delete(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> CommonResourceDeletedResponse: ...
```

### JulepApi().sessions_route_get

[Show source in client.py:2331](../../../../../../julep/api/client.py#L2331)

Get a session by id

Parameters
----------
id : CommonUuid
    ID of the resource

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
SessionsSession
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.sessions_route_get(
    id="string",
)

#### Signature

```python
def sessions_route_get(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> SessionsSession: ...
```

### JulepApi().sessions_route_list

[Show source in client.py:2168](../../../../../../julep/api/client.py#L2168)

List sessions (paginated)

Parameters
----------
limit : CommonLimit
    Limit the number of items returned

offset : CommonOffset
    Offset the items returned

sort_by : SessionsRouteListRequestSortBy
    Sort by a field

direction : SessionsRouteListRequestDirection
    Sort direction

metadata_filter : str
    JSON string of object that should be used to filter objects by metadata

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
SessionsRouteListResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.sessions_route_list(
    limit=1,
    offset=1,
    sort_by="created_at",
    direction="asc",
    metadata_filter="metadata_filter",
)

#### Signature

```python
def sessions_route_list(
    self,
    limit: CommonLimit,
    offset: CommonOffset,
    sort_by: SessionsRouteListRequestSortBy,
    direction: SessionsRouteListRequestDirection,
    metadata_filter: str,
    request_options: typing.Optional[RequestOptions] = None,
) -> SessionsRouteListResponse: ...
```

### JulepApi().sessions_route_patch

[Show source in client.py:2588](../../../../../../julep/api/client.py#L2588)

Update an existing session by its id (merges with existing values)

Parameters
----------
id : CommonUuid
    ID of the resource

situation : typing.Optional[str]
    A specific situation that sets the background for this session

render_templates : typing.Optional[bool]
    Render system and assistant message content as jinja templates

token_budget : typing.Optional[int]
    Threshold value for the adaptive context functionality

context_overflow : typing.Optional[SessionsContextOverflowType]
    Action to start on context window overflow

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.sessions_route_patch(
    id="id",
)

#### Signature

```python
def sessions_route_patch(
    self,
    id: CommonUuid,
    situation: typing.Optional[str] = OMIT,
    render_templates: typing.Optional[bool] = OMIT,
    token_budget: typing.Optional[int] = OMIT,
    context_overflow: typing.Optional[SessionsContextOverflowType] = OMIT,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().sessions_route_update

[Show source in client.py:2468](../../../../../../julep/api/client.py#L2468)

Update an existing session by its id (overwrites all existing values)

Parameters
----------
id : CommonUuid
    ID of the resource

situation : str
    A specific situation that sets the background for this session

render_templates : bool
    Render system and assistant message content as jinja templates

token_budget : typing.Optional[int]
    Threshold value for the adaptive context functionality

context_overflow : typing.Optional[SessionsContextOverflowType]
    Action to start on context window overflow

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.sessions_route_update(
    id="id",
    situation="situation",
    render_templates=True,
)

#### Signature

```python
def sessions_route_update(
    self,
    id: CommonUuid,
    situation: str,
    render_templates: bool,
    token_budget: typing.Optional[int] = OMIT,
    context_overflow: typing.Optional[SessionsContextOverflowType] = OMIT,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().task_executions_route_create

[Show source in client.py:2995](../../../../../../julep/api/client.py#L2995)

Create an execution for the given task

Parameters
----------
id : CommonUuid
    ID of parent resource

input : typing.Dict[str, typing.Any]
    The input to the execution

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceCreatedResponse
    The request has succeeded and a new resource has been created as a result.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.task_executions_route_create(
    id="id",
    input={"key": "value"},
)

#### Signature

```python
def task_executions_route_create(
    self,
    id: CommonUuid,
    input: typing.Dict[str, typing.Any],
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceCreatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().task_executions_route_list

[Show source in client.py:2916](../../../../../../julep/api/client.py#L2916)

List executions of the given task

Parameters
----------
id : CommonUuid
    ID of parent

limit : CommonLimit
    Limit the number of items returned

offset : CommonOffset
    Offset the items returned

sort_by : TaskExecutionsRouteListRequestSortBy
    Sort by a field

direction : TaskExecutionsRouteListRequestDirection
    Sort direction

metadata_filter : str
    JSON string of object that should be used to filter objects by metadata

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
TaskExecutionsRouteListResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.task_executions_route_list(
    id="id",
    limit=1,
    offset=1,
    sort_by="created_at",
    direction="asc",
    metadata_filter="metadata_filter",
)

#### Signature

```python
def task_executions_route_list(
    self,
    id: CommonUuid,
    limit: CommonLimit,
    offset: CommonOffset,
    sort_by: TaskExecutionsRouteListRequestSortBy,
    direction: TaskExecutionsRouteListRequestDirection,
    metadata_filter: str,
    request_options: typing.Optional[RequestOptions] = None,
) -> TaskExecutionsRouteListResponse: ...
```

### JulepApi().tasks_create_or_update_route_create_or_update

[Show source in client.py:1699](../../../../../../julep/api/client.py#L1699)

Create or update a task

Parameters
----------
parent_id : CommonUuid
    ID of the agent

id : CommonUuid

name : str

description : str

main : typing.Sequence[TasksCreateTaskRequestMainItem]
    The entrypoint of the task.

tools : typing.Sequence[TasksTaskTool]
    Tools defined specifically for this task not included in the Agent itself.

inherit_tools : bool
    Whether to inherit tools from the parent agent or not. Defaults to true.

input_schema : typing.Optional[typing.Dict[str, typing.Any]]
    The schema for the input to the task. `null` means all inputs are valid.

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceCreatedResponse
    The request has succeeded and a new resource has been created as a result.

Examples
--------
from julep import TasksTaskTool
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.tasks_create_or_update_route_create_or_update(
    parent_id="parent_id",
    id="id",
    name="name",
    description="description",
    main=[],
    tools=[
        TasksTaskTool(
            type="function",
            name="name",
        )
    ],
    inherit_tools=True,
)

#### Signature

```python
def tasks_create_or_update_route_create_or_update(
    self,
    parent_id: CommonUuid,
    id: CommonUuid,
    name: str,
    description: str,
    main: typing.Sequence[TasksCreateTaskRequestMainItem],
    tools: typing.Sequence[TasksTaskTool],
    inherit_tools: bool,
    input_schema: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceCreatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().tasks_route_create

[Show source in client.py:1000](../../../../../../julep/api/client.py#L1000)

Create a new task

Parameters
----------
id : CommonUuid
    ID of parent resource

name : str

description : str

main : typing.Sequence[TasksCreateTaskRequestMainItem]
    The entrypoint of the task.

tools : typing.Sequence[TasksTaskTool]
    Tools defined specifically for this task not included in the Agent itself.

inherit_tools : bool
    Whether to inherit tools from the parent agent or not. Defaults to true.

input_schema : typing.Optional[typing.Dict[str, typing.Any]]
    The schema for the input to the task. `null` means all inputs are valid.

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceCreatedResponse
    The request has succeeded.

Examples
--------
from julep import TasksTaskTool
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.tasks_route_create(
    id="id",
    name="name",
    description="description",
    main=[],
    tools=[
        TasksTaskTool(
            type="function",
            name="name",
        )
    ],
    inherit_tools=True,
)

#### Signature

```python
def tasks_route_create(
    self,
    id: CommonUuid,
    name: str,
    description: str,
    main: typing.Sequence[TasksCreateTaskRequestMainItem],
    tools: typing.Sequence[TasksTaskTool],
    inherit_tools: bool,
    input_schema: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceCreatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().tasks_route_delete

[Show source in client.py:1186](../../../../../../julep/api/client.py#L1186)

Delete a task by its id

Parameters
----------
id : CommonUuid
    ID of parent resource

child_id : CommonUuid
    ID of the resource to be deleted

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceDeletedResponse
    The request has been accepted for processing, but processing has not yet completed.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.tasks_route_delete(
    id="id",
    child_id="child_id",
)

#### Signature

```python
def tasks_route_delete(
    self,
    id: CommonUuid,
    child_id: CommonUuid,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceDeletedResponse: ...
```

### JulepApi().tasks_route_list

[Show source in client.py:921](../../../../../../julep/api/client.py#L921)

List tasks (paginated)

Parameters
----------
id : CommonUuid
    ID of parent

limit : CommonLimit
    Limit the number of items returned

offset : CommonOffset
    Offset the items returned

sort_by : TasksRouteListRequestSortBy
    Sort by a field

direction : TasksRouteListRequestDirection
    Sort direction

metadata_filter : str
    JSON string of object that should be used to filter objects by metadata

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
TasksRouteListResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.tasks_route_list(
    id="id",
    limit=1,
    offset=1,
    sort_by="created_at",
    direction="asc",
    metadata_filter="metadata_filter",
)

#### Signature

```python
def tasks_route_list(
    self,
    id: CommonUuid,
    limit: CommonLimit,
    offset: CommonOffset,
    sort_by: TasksRouteListRequestSortBy,
    direction: TasksRouteListRequestDirection,
    metadata_filter: str,
    request_options: typing.Optional[RequestOptions] = None,
) -> TasksRouteListResponse: ...
```

### JulepApi().tasks_route_patch

[Show source in client.py:1238](../../../../../../julep/api/client.py#L1238)

Update an existing task (merges with existing values)

Parameters
----------
id : CommonUuid
    ID of parent resource

child_id : CommonUuid
    ID of the resource to be patched

description : typing.Optional[str]

main : typing.Optional[typing.Sequence[TasksPatchTaskRequestMainItem]]
    The entrypoint of the task.

input_schema : typing.Optional[typing.Dict[str, typing.Any]]
    The schema for the input to the task. `null` means all inputs are valid.

tools : typing.Optional[typing.Sequence[TasksTaskTool]]
    Tools defined specifically for this task not included in the Agent itself.

inherit_tools : typing.Optional[bool]
    Whether to inherit tools from the parent agent or not. Defaults to true.

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.tasks_route_patch(
    id="id",
    child_id="child_id",
)

#### Signature

```python
def tasks_route_patch(
    self,
    id: CommonUuid,
    child_id: CommonUuid,
    description: typing.Optional[str] = OMIT,
    main: typing.Optional[typing.Sequence[TasksPatchTaskRequestMainItem]] = OMIT,
    input_schema: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    tools: typing.Optional[typing.Sequence[TasksTaskTool]] = OMIT,
    inherit_tools: typing.Optional[bool] = OMIT,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().tasks_route_update

[Show source in client.py:1093](../../../../../../julep/api/client.py#L1093)

Update an existing task (overwrite existing values)

Parameters
----------
id : CommonUuid
    ID of parent resource

child_id : CommonUuid
    ID of the resource to be updated

description : str

main : typing.Sequence[TasksUpdateTaskRequestMainItem]
    The entrypoint of the task.

tools : typing.Sequence[TasksTaskTool]
    Tools defined specifically for this task not included in the Agent itself.

inherit_tools : bool
    Whether to inherit tools from the parent agent or not. Defaults to true.

input_schema : typing.Optional[typing.Dict[str, typing.Any]]
    The schema for the input to the task. `null` means all inputs are valid.

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
from julep import TasksTaskTool
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.tasks_route_update(
    id="id",
    child_id="child_id",
    description="description",
    main=[],
    tools=[
        TasksTaskTool(
            type="function",
            name="name",
        )
    ],
    inherit_tools=True,
)

#### Signature

```python
def tasks_route_update(
    self,
    id: CommonUuid,
    child_id: CommonUuid,
    description: str,
    main: typing.Sequence[TasksUpdateTaskRequestMainItem],
    tools: typing.Sequence[TasksTaskTool],
    inherit_tools: bool,
    input_schema: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().user_docs_route_create

[Show source in client.py:3533](../../../../../../julep/api/client.py#L3533)

Create a Doc for this User

Parameters
----------
id : CommonUuid
    ID of parent resource

title : CommonIdentifierSafeUnicode
    Title describing what this document contains

content : DocsCreateDocRequestContent
    Contents of the document

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceCreatedResponse
    The request has succeeded and a new resource has been created as a result.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.user_docs_route_create(
    id="id",
    title="title",
    content="content",
)

#### Signature

```python
def user_docs_route_create(
    self,
    id: CommonUuid,
    title: CommonIdentifierSafeUnicode,
    content: DocsCreateDocRequestContent,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceCreatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().user_docs_route_delete

[Show source in client.py:3595](../../../../../../julep/api/client.py#L3595)

Delete a Doc for this User

Parameters
----------
id : CommonUuid
    ID of parent resource

child_id : CommonUuid
    ID of the resource to be deleted

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceDeletedResponse
    The request has been accepted for processing, but processing has not yet completed.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.user_docs_route_delete(
    id="id",
    child_id="child_id",
)

#### Signature

```python
def user_docs_route_delete(
    self,
    id: CommonUuid,
    child_id: CommonUuid,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceDeletedResponse: ...
```

### JulepApi().user_docs_route_list

[Show source in client.py:3454](../../../../../../julep/api/client.py#L3454)

List Docs owned by a User

Parameters
----------
id : CommonUuid
    ID of parent

limit : CommonLimit
    Limit the number of items returned

offset : CommonOffset
    Offset the items returned

sort_by : UserDocsRouteListRequestSortBy
    Sort by a field

direction : UserDocsRouteListRequestDirection
    Sort direction

metadata_filter : str
    JSON string of object that should be used to filter objects by metadata

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
UserDocsRouteListResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.user_docs_route_list(
    id="id",
    limit=1,
    offset=1,
    sort_by="created_at",
    direction="asc",
    metadata_filter="metadata_filter",
)

#### Signature

```python
def user_docs_route_list(
    self,
    id: CommonUuid,
    limit: CommonLimit,
    offset: CommonOffset,
    sort_by: UserDocsRouteListRequestSortBy,
    direction: UserDocsRouteListRequestDirection,
    metadata_filter: str,
    request_options: typing.Optional[RequestOptions] = None,
) -> UserDocsRouteListResponse: ...
```

### JulepApi().user_docs_search_route_search

[Show source in client.py:3647](../../../../../../julep/api/client.py#L3647)

Search Docs owned by a User

Parameters
----------
id : CommonUuid
    ID of the parent

body : UserDocsSearchRouteSearchRequestBody

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
DocsDocSearchResponse
    The request has succeeded.

Examples
--------
from julep import DocsVectorDocSearchRequest
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.user_docs_search_route_search(
    id="id",
    body=DocsVectorDocSearchRequest(
        limit=1,
        confidence=1.1,
        vector=[1.1],
    ),
)

#### Signature

```python
def user_docs_search_route_search(
    self,
    id: CommonUuid,
    body: UserDocsSearchRouteSearchRequestBody,
    request_options: typing.Optional[RequestOptions] = None,
) -> DocsDocSearchResponse: ...
```

### JulepApi().users_route_create

[Show source in client.py:3126](../../../../../../julep/api/client.py#L3126)

Create a new user

Parameters
----------
name : CommonIdentifierSafeUnicode
    Name of the user

about : str
    About the user

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceCreatedResponse
    The request has succeeded and a new resource has been created as a result.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.users_route_create(
    name="name",
    about="about",
)

#### Signature

```python
def users_route_create(
    self,
    name: CommonIdentifierSafeUnicode,
    about: str,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceCreatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().users_route_create_or_update

[Show source in client.py:3227](../../../../../../julep/api/client.py#L3227)

Create or update a user

Parameters
----------
id : CommonUuid

name : CommonIdentifierSafeUnicode
    Name of the user

about : str
    About the user

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.users_route_create_or_update(
    id="id",
    name="name",
    about="about",
)

#### Signature

```python
def users_route_create_or_update(
    self,
    id: CommonUuid,
    name: CommonIdentifierSafeUnicode,
    about: str,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().users_route_delete

[Show source in client.py:3350](../../../../../../julep/api/client.py#L3350)

Delete a user by id

Parameters
----------
id : CommonUuid
    ID of the resource

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceDeletedResponse
    The request has been accepted for processing, but processing has not yet completed.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.users_route_delete(
    id="id",
)

#### Signature

```python
def users_route_delete(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> CommonResourceDeletedResponse: ...
```

### JulepApi().users_route_get

[Show source in client.py:3183](../../../../../../julep/api/client.py#L3183)

Get a user by id

Parameters
----------
id : CommonUuid
    ID of the resource

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
UsersUser
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.users_route_get(
    id="id",
)

#### Signature

```python
def users_route_get(
    self, id: CommonUuid, request_options: typing.Optional[RequestOptions] = None
) -> UsersUser: ...
```

### JulepApi().users_route_list

[Show source in client.py:3052](../../../../../../julep/api/client.py#L3052)

List users (paginated)

Parameters
----------
limit : CommonLimit
    Limit the number of items returned

offset : CommonOffset
    Offset the items returned

sort_by : UsersRouteListRequestSortBy
    Sort by a field

direction : UsersRouteListRequestDirection
    Sort direction

metadata_filter : str
    JSON string of object that should be used to filter objects by metadata

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
UsersRouteListResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.users_route_list(
    limit=1,
    offset=1,
    sort_by="created_at",
    direction="asc",
    metadata_filter="metadata_filter",
)

#### Signature

```python
def users_route_list(
    self,
    limit: CommonLimit,
    offset: CommonOffset,
    sort_by: UsersRouteListRequestSortBy,
    direction: UsersRouteListRequestDirection,
    metadata_filter: str,
    request_options: typing.Optional[RequestOptions] = None,
) -> UsersRouteListResponse: ...
```

### JulepApi().users_route_patch

[Show source in client.py:3394](../../../../../../julep/api/client.py#L3394)

Update an existing user by id (merge with existing values)

Parameters
----------
id : CommonUuid
    ID of the resource

metadata : typing.Optional[typing.Dict[str, typing.Any]]

name : typing.Optional[CommonIdentifierSafeUnicode]
    Name of the user

about : typing.Optional[str]
    About the user

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.users_route_patch(
    id="id",
)

#### Signature

```python
def users_route_patch(
    self,
    id: CommonUuid,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    name: typing.Optional[CommonIdentifierSafeUnicode] = OMIT,
    about: typing.Optional[str] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)

### JulepApi().users_route_update

[Show source in client.py:3288](../../../../../../julep/api/client.py#L3288)

Update an existing user by id (overwrite existing values)

Parameters
----------
id : CommonUuid
    ID of the resource

name : CommonIdentifierSafeUnicode
    Name of the user

about : str
    About the user

metadata : typing.Optional[typing.Dict[str, typing.Any]]

request_options : typing.Optional[RequestOptions]
    Request-specific configuration.

Returns
-------
CommonResourceUpdatedResponse
    The request has succeeded.

Examples
--------
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.users_route_update(
    id="id",
    name="name",
    about="about",
)

#### Signature

```python
def users_route_update(
    self,
    id: CommonUuid,
    name: CommonIdentifierSafeUnicode,
    about: str,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = OMIT,
    request_options: typing.Optional[RequestOptions] = None,
) -> CommonResourceUpdatedResponse: ...
```

#### See also

- [OMIT](#omit)