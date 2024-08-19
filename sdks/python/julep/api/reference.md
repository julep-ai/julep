# Reference
<details><summary><code>client.<a href="src/julep/client.py">agents_route_list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List Agents (paginated)
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**limit:** `CommonLimit` — Limit the number of items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the items returned
    
</dd>
</dl>

<dl>
<dd>

**sort_by:** `AgentsRouteListRequestSortBy` — Sort by a field
    
</dd>
</dl>

<dl>
<dd>

**direction:** `AgentsRouteListRequestDirection` — Sort direction
    
</dd>
</dl>

<dl>
<dd>

**metadata_filter:** `str` — JSON string of object that should be used to filter objects by metadata
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">agents_route_create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a new Agent
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**name:** `CommonIdentifierSafeUnicode` — Name of the agent
    
</dd>
</dl>

<dl>
<dd>

**about:** `str` — About the agent
    
</dd>
</dl>

<dl>
<dd>

**model:** `str` — Model name to use (gpt-4-turbo, gemini-nano etc)
    
</dd>
</dl>

<dl>
<dd>

**instructions:** `AgentsCreateAgentRequestInstructions` — Instructions for the agent
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**default_settings:** `typing.Optional[ChatDefaultChatSettings]` — Default settings for all sessions created by this agent
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">agents_route_get</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get an Agent by id
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agents_route_get(
    id="id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of the resource
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">agents_route_create_or_update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create or update an Agent
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` 
    
</dd>
</dl>

<dl>
<dd>

**name:** `CommonIdentifierSafeUnicode` — Name of the agent
    
</dd>
</dl>

<dl>
<dd>

**about:** `str` — About the agent
    
</dd>
</dl>

<dl>
<dd>

**model:** `str` — Model name to use (gpt-4-turbo, gemini-nano etc)
    
</dd>
</dl>

<dl>
<dd>

**instructions:** `AgentsUpdateAgentRequestInstructions` — Instructions for the agent
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**default_settings:** `typing.Optional[ChatDefaultChatSettings]` — Default settings for all sessions created by this agent
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">agents_route_update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update an existing Agent by id (overwrites existing values; use PATCH for merging instead)
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of the resource
    
</dd>
</dl>

<dl>
<dd>

**name:** `CommonIdentifierSafeUnicode` — Name of the agent
    
</dd>
</dl>

<dl>
<dd>

**about:** `str` — About the agent
    
</dd>
</dl>

<dl>
<dd>

**model:** `str` — Model name to use (gpt-4-turbo, gemini-nano etc)
    
</dd>
</dl>

<dl>
<dd>

**instructions:** `AgentsUpdateAgentRequestInstructions` — Instructions for the agent
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**default_settings:** `typing.Optional[ChatDefaultChatSettings]` — Default settings for all sessions created by this agent
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">agents_route_delete</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete Agent by id
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agents_route_delete(
    id="id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of the resource
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">agents_route_patch</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update an existing Agent by id (merges with existing values)
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agents_route_patch(
    id="id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of the resource
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**name:** `typing.Optional[CommonIdentifierSafeUnicode]` — Name of the agent
    
</dd>
</dl>

<dl>
<dd>

**about:** `typing.Optional[str]` — About the agent
    
</dd>
</dl>

<dl>
<dd>

**model:** `typing.Optional[str]` — Model name to use (gpt-4-turbo, gemini-nano etc)
    
</dd>
</dl>

<dl>
<dd>

**instructions:** `typing.Optional[AgentsPatchAgentRequestInstructions]` — Instructions for the agent
    
</dd>
</dl>

<dl>
<dd>

**default_settings:** `typing.Optional[ChatDefaultChatSettings]` — Default settings for all sessions created by this agent
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">agent_docs_route_list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List Docs owned by an Agent
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of parent
    
</dd>
</dl>

<dl>
<dd>

**limit:** `CommonLimit` — Limit the number of items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the items returned
    
</dd>
</dl>

<dl>
<dd>

**sort_by:** `AgentDocsRouteListRequestSortBy` — Sort by a field
    
</dd>
</dl>

<dl>
<dd>

**direction:** `AgentDocsRouteListRequestDirection` — Sort direction
    
</dd>
</dl>

<dl>
<dd>

**metadata_filter:** `str` — JSON string of object that should be used to filter objects by metadata
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">agent_docs_route_create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a Doc for this Agent
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of parent resource
    
</dd>
</dl>

<dl>
<dd>

**title:** `CommonIdentifierSafeUnicode` — Title describing what this document contains
    
</dd>
</dl>

<dl>
<dd>

**content:** `DocsCreateDocRequestContent` — Contents of the document
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">agent_docs_route_delete</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete a Doc for this Agent
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agent_docs_route_delete(
    id="id",
    child_id="child_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of parent resource
    
</dd>
</dl>

<dl>
<dd>

**child_id:** `CommonUuid` — ID of the resource to be deleted
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">agents_docs_search_route_search</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Search Docs owned by an Agent
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of the parent
    
</dd>
</dl>

<dl>
<dd>

**body:** `AgentsDocsSearchRouteSearchRequestBody` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">tasks_route_list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List tasks (paginated)
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of parent
    
</dd>
</dl>

<dl>
<dd>

**limit:** `CommonLimit` — Limit the number of items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the items returned
    
</dd>
</dl>

<dl>
<dd>

**sort_by:** `TasksRouteListRequestSortBy` — Sort by a field
    
</dd>
</dl>

<dl>
<dd>

**direction:** `TasksRouteListRequestDirection` — Sort direction
    
</dd>
</dl>

<dl>
<dd>

**metadata_filter:** `str` — JSON string of object that should be used to filter objects by metadata
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">tasks_route_create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a new task
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of parent resource
    
</dd>
</dl>

<dl>
<dd>

**name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**description:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**main:** `typing.Sequence[TasksCreateTaskRequestMainItem]` — The entrypoint of the task.
    
</dd>
</dl>

<dl>
<dd>

**tools:** `typing.Sequence[TasksTaskTool]` — Tools defined specifically for this task not included in the Agent itself.
    
</dd>
</dl>

<dl>
<dd>

**inherit_tools:** `bool` — Whether to inherit tools from the parent agent or not. Defaults to true.
    
</dd>
</dl>

<dl>
<dd>

**input_schema:** `typing.Optional[typing.Dict[str, typing.Any]]` — The schema for the input to the task. `null` means all inputs are valid.
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">tasks_route_update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update an existing task (overwrite existing values)
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of parent resource
    
</dd>
</dl>

<dl>
<dd>

**child_id:** `CommonUuid` — ID of the resource to be updated
    
</dd>
</dl>

<dl>
<dd>

**description:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**main:** `typing.Sequence[TasksUpdateTaskRequestMainItem]` — The entrypoint of the task.
    
</dd>
</dl>

<dl>
<dd>

**tools:** `typing.Sequence[TasksTaskTool]` — Tools defined specifically for this task not included in the Agent itself.
    
</dd>
</dl>

<dl>
<dd>

**inherit_tools:** `bool` — Whether to inherit tools from the parent agent or not. Defaults to true.
    
</dd>
</dl>

<dl>
<dd>

**input_schema:** `typing.Optional[typing.Dict[str, typing.Any]]` — The schema for the input to the task. `null` means all inputs are valid.
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">tasks_route_delete</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete a task by its id
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.tasks_route_delete(
    id="id",
    child_id="child_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of parent resource
    
</dd>
</dl>

<dl>
<dd>

**child_id:** `CommonUuid` — ID of the resource to be deleted
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">tasks_route_patch</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update an existing task (merges with existing values)
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.tasks_route_patch(
    id="id",
    child_id="child_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of parent resource
    
</dd>
</dl>

<dl>
<dd>

**child_id:** `CommonUuid` — ID of the resource to be patched
    
</dd>
</dl>

<dl>
<dd>

**description:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**main:** `typing.Optional[typing.Sequence[TasksPatchTaskRequestMainItem]]` — The entrypoint of the task.
    
</dd>
</dl>

<dl>
<dd>

**input_schema:** `typing.Optional[typing.Dict[str, typing.Any]]` — The schema for the input to the task. `null` means all inputs are valid.
    
</dd>
</dl>

<dl>
<dd>

**tools:** `typing.Optional[typing.Sequence[TasksTaskTool]]` — Tools defined specifically for this task not included in the Agent itself.
    
</dd>
</dl>

<dl>
<dd>

**inherit_tools:** `typing.Optional[bool]` — Whether to inherit tools from the parent agent or not. Defaults to true.
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">agent_tools_route_list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List tools of the given agent
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of parent
    
</dd>
</dl>

<dl>
<dd>

**limit:** `CommonLimit` — Limit the number of items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the items returned
    
</dd>
</dl>

<dl>
<dd>

**sort_by:** `AgentToolsRouteListRequestSortBy` — Sort by a field
    
</dd>
</dl>

<dl>
<dd>

**direction:** `AgentToolsRouteListRequestDirection` — Sort direction
    
</dd>
</dl>

<dl>
<dd>

**metadata_filter:** `str` — JSON string of object that should be used to filter objects by metadata
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">agent_tools_route_create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a new tool for this agent
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of parent resource
    
</dd>
</dl>

<dl>
<dd>

**name:** `CommonIdentifierSafeUnicode` — Name of the agent
    
</dd>
</dl>

<dl>
<dd>

**about:** `str` — About the agent
    
</dd>
</dl>

<dl>
<dd>

**model:** `str` — Model name to use (gpt-4-turbo, gemini-nano etc)
    
</dd>
</dl>

<dl>
<dd>

**instructions:** `AgentsCreateAgentRequestInstructions` — Instructions for the agent
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**default_settings:** `typing.Optional[ChatDefaultChatSettings]` — Default settings for all sessions created by this agent
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">agent_tools_route_update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update an existing tool (overwrite existing values)
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of parent resource
    
</dd>
</dl>

<dl>
<dd>

**child_id:** `CommonUuid` — ID of the resource to be updated
    
</dd>
</dl>

<dl>
<dd>

**type:** `ToolsToolType` — Whether this tool is a `function`, `api_call`, `system` etc. (Only `function` tool supported right now)
    
</dd>
</dl>

<dl>
<dd>

**name:** `CommonValidPythonIdentifier` — Name of the tool (must be unique for this agent and a valid python identifier string )
    
</dd>
</dl>

<dl>
<dd>

**function:** `typing.Optional[ToolsFunctionDef]` 
    
</dd>
</dl>

<dl>
<dd>

**integration:** `typing.Optional[typing.Any]` 
    
</dd>
</dl>

<dl>
<dd>

**system:** `typing.Optional[typing.Any]` 
    
</dd>
</dl>

<dl>
<dd>

**api_call:** `typing.Optional[typing.Any]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">agent_tools_route_delete</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete an existing tool by id
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agent_tools_route_delete(
    id="id",
    child_id="child_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of parent resource
    
</dd>
</dl>

<dl>
<dd>

**child_id:** `CommonUuid` — ID of the resource to be deleted
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">agent_tools_route_patch</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update an existing tool (merges with existing values)
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agent_tools_route_patch(
    id="id",
    child_id="child_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of parent resource
    
</dd>
</dl>

<dl>
<dd>

**child_id:** `CommonUuid` — ID of the resource to be patched
    
</dd>
</dl>

<dl>
<dd>

**type:** `typing.Optional[ToolsToolType]` — Whether this tool is a `function`, `api_call`, `system` etc. (Only `function` tool supported right now)
    
</dd>
</dl>

<dl>
<dd>

**name:** `typing.Optional[CommonValidPythonIdentifier]` — Name of the tool (must be unique for this agent and a valid python identifier string )
    
</dd>
</dl>

<dl>
<dd>

**function:** `typing.Optional[ToolsFunctionDef]` 
    
</dd>
</dl>

<dl>
<dd>

**integration:** `typing.Optional[typing.Any]` 
    
</dd>
</dl>

<dl>
<dd>

**system:** `typing.Optional[typing.Any]` 
    
</dd>
</dl>

<dl>
<dd>

**api_call:** `typing.Optional[typing.Any]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">tasks_create_or_update_route_create_or_update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create or update a task
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**parent_id:** `CommonUuid` — ID of the agent
    
</dd>
</dl>

<dl>
<dd>

**id:** `CommonUuid` 
    
</dd>
</dl>

<dl>
<dd>

**name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**description:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**main:** `typing.Sequence[TasksCreateTaskRequestMainItem]` — The entrypoint of the task.
    
</dd>
</dl>

<dl>
<dd>

**tools:** `typing.Sequence[TasksTaskTool]` — Tools defined specifically for this task not included in the Agent itself.
    
</dd>
</dl>

<dl>
<dd>

**inherit_tools:** `bool` — Whether to inherit tools from the parent agent or not. Defaults to true.
    
</dd>
</dl>

<dl>
<dd>

**input_schema:** `typing.Optional[typing.Dict[str, typing.Any]]` — The schema for the input to the task. `null` means all inputs are valid.
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">individual_docs_route_get</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get Doc by id
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.individual_docs_route_get(
    id="id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of the resource
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">embed_route_embed</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Embed a query for search
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**body:** `DocsEmbedQueryRequest` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">executions_route_resume_with_task_token</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Resume an execution with a task token
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.executions_route_resume_with_task_token(
    task_token="task_token",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**task_token:** `str` — A Task Token is a unique identifier for a specific Task Execution.
    
</dd>
</dl>

<dl>
<dd>

**input:** `typing.Optional[typing.Dict[str, typing.Any]]` — The input to resume the execution with
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">executions_route_get</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get an Execution by id
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.executions_route_get(
    id="id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of the resource
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">executions_route_update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update an existing Execution
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of the resource
    
</dd>
</dl>

<dl>
<dd>

**request:** `ExecutionsUpdateExecutionRequest` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">execution_transitions_route_list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List the Transitions of an Execution by id
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of parent
    
</dd>
</dl>

<dl>
<dd>

**limit:** `CommonLimit` — Limit the number of items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the items returned
    
</dd>
</dl>

<dl>
<dd>

**sort_by:** `ExecutionTransitionsRouteListRequestSortBy` — Sort by a field
    
</dd>
</dl>

<dl>
<dd>

**direction:** `ExecutionTransitionsRouteListRequestDirection` — Sort direction
    
</dd>
</dl>

<dl>
<dd>

**metadata_filter:** `str` — JSON string of object that should be used to filter objects by metadata
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">job_route_get</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get the status of an existing Job by its id
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.job_route_get(
    id="id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of the resource
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">sessions_route_list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List sessions (paginated)
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**limit:** `CommonLimit` — Limit the number of items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the items returned
    
</dd>
</dl>

<dl>
<dd>

**sort_by:** `SessionsRouteListRequestSortBy` — Sort by a field
    
</dd>
</dl>

<dl>
<dd>

**direction:** `SessionsRouteListRequestDirection` — Sort direction
    
</dd>
</dl>

<dl>
<dd>

**metadata_filter:** `str` — JSON string of object that should be used to filter objects by metadata
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">sessions_route_create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a new session
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.sessions_route_create(
    situation="situation",
    render_templates=True,
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**situation:** `str` — A specific situation that sets the background for this session
    
</dd>
</dl>

<dl>
<dd>

**render_templates:** `bool` — Render system and assistant message content as jinja templates
    
</dd>
</dl>

<dl>
<dd>

**user:** `typing.Optional[CommonUuid]` — User ID of user associated with this session
    
</dd>
</dl>

<dl>
<dd>

**users:** `typing.Optional[typing.Sequence[CommonUuid]]` 
    
</dd>
</dl>

<dl>
<dd>

**agent:** `typing.Optional[CommonUuid]` — Agent ID of agent associated with this session
    
</dd>
</dl>

<dl>
<dd>

**agents:** `typing.Optional[typing.Sequence[CommonUuid]]` 
    
</dd>
</dl>

<dl>
<dd>

**token_budget:** `typing.Optional[int]` — Threshold value for the adaptive context functionality
    
</dd>
</dl>

<dl>
<dd>

**context_overflow:** `typing.Optional[SessionsContextOverflowType]` — Action to start on context window overflow
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">sessions_route_get</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get a session by id
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.sessions_route_get(
    id="string",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of the resource
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">sessions_route_create_or_update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create or update a session
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` 
    
</dd>
</dl>

<dl>
<dd>

**situation:** `str` — A specific situation that sets the background for this session
    
</dd>
</dl>

<dl>
<dd>

**render_templates:** `bool` — Render system and assistant message content as jinja templates
    
</dd>
</dl>

<dl>
<dd>

**user:** `typing.Optional[CommonUuid]` — User ID of user associated with this session
    
</dd>
</dl>

<dl>
<dd>

**users:** `typing.Optional[typing.Sequence[CommonUuid]]` 
    
</dd>
</dl>

<dl>
<dd>

**agent:** `typing.Optional[CommonUuid]` — Agent ID of agent associated with this session
    
</dd>
</dl>

<dl>
<dd>

**agents:** `typing.Optional[typing.Sequence[CommonUuid]]` 
    
</dd>
</dl>

<dl>
<dd>

**token_budget:** `typing.Optional[int]` — Threshold value for the adaptive context functionality
    
</dd>
</dl>

<dl>
<dd>

**context_overflow:** `typing.Optional[SessionsContextOverflowType]` — Action to start on context window overflow
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">sessions_route_update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update an existing session by its id (overwrites all existing values)
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of the resource
    
</dd>
</dl>

<dl>
<dd>

**situation:** `str` — A specific situation that sets the background for this session
    
</dd>
</dl>

<dl>
<dd>

**render_templates:** `bool` — Render system and assistant message content as jinja templates
    
</dd>
</dl>

<dl>
<dd>

**token_budget:** `typing.Optional[int]` — Threshold value for the adaptive context functionality
    
</dd>
</dl>

<dl>
<dd>

**context_overflow:** `typing.Optional[SessionsContextOverflowType]` — Action to start on context window overflow
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">sessions_route_delete</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete a session by its id
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.sessions_route_delete(
    id="id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of the resource
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">sessions_route_patch</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update an existing session by its id (merges with existing values)
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.sessions_route_patch(
    id="id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of the resource
    
</dd>
</dl>

<dl>
<dd>

**situation:** `typing.Optional[str]` — A specific situation that sets the background for this session
    
</dd>
</dl>

<dl>
<dd>

**render_templates:** `typing.Optional[bool]` — Render system and assistant message content as jinja templates
    
</dd>
</dl>

<dl>
<dd>

**token_budget:** `typing.Optional[int]` — Threshold value for the adaptive context functionality
    
</dd>
</dl>

<dl>
<dd>

**context_overflow:** `typing.Optional[SessionsContextOverflowType]` — Action to start on context window overflow
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">chat_route_generate</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Generate a response from the model
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — The session ID
    
</dd>
</dl>

<dl>
<dd>

**remember:** `bool` — DISABLED: Whether this interaction should form new memories or not (will be enabled in a future release)
    
</dd>
</dl>

<dl>
<dd>

**recall:** `bool` — Whether previous memories and docs should be recalled or not
    
</dd>
</dl>

<dl>
<dd>

**save:** `bool` — Whether this interaction should be stored in the session history or not
    
</dd>
</dl>

<dl>
<dd>

**stream:** `bool` — Indicates if the server should stream the response as it's generated
    
</dd>
</dl>

<dl>
<dd>

**messages:** `typing.Sequence[EntriesInputChatMlMessage]` — A list of new input messages comprising the conversation so far.
    
</dd>
</dl>

<dl>
<dd>

**model:** `typing.Optional[CommonIdentifierSafeUnicode]` — Identifier of the model to be used
    
</dd>
</dl>

<dl>
<dd>

**stop:** `typing.Optional[typing.Sequence[str]]` — Up to 4 sequences where the API will stop generating further tokens.
    
</dd>
</dl>

<dl>
<dd>

**seed:** `typing.Optional[int]` — If specified, the system will make a best effort to sample deterministically for that particular seed value
    
</dd>
</dl>

<dl>
<dd>

**max_tokens:** `typing.Optional[int]` — The maximum number of tokens to generate in the chat completion
    
</dd>
</dl>

<dl>
<dd>

**logit_bias:** `typing.Optional[typing.Dict[str, CommonLogitBias]]` — Modify the likelihood of specified tokens appearing in the completion
    
</dd>
</dl>

<dl>
<dd>

**response_format:** `typing.Optional[ChatCompletionResponseFormat]` — Response format (set to `json_object` to restrict output to JSON)
    
</dd>
</dl>

<dl>
<dd>

**agent:** `typing.Optional[CommonUuid]` — Agent ID of the agent to use for this interaction. (Only applicable for multi-agent sessions)
    
</dd>
</dl>

<dl>
<dd>

**repetition_penalty:** `typing.Optional[float]` — Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
    
</dd>
</dl>

<dl>
<dd>

**length_penalty:** `typing.Optional[float]` — Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated.
    
</dd>
</dl>

<dl>
<dd>

**min_p:** `typing.Optional[float]` — Minimum probability compared to leading token to be considered
    
</dd>
</dl>

<dl>
<dd>

**frequency_penalty:** `typing.Optional[float]` — Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
    
</dd>
</dl>

<dl>
<dd>

**presence_penalty:** `typing.Optional[float]` — Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
    
</dd>
</dl>

<dl>
<dd>

**temperature:** `typing.Optional[float]` — What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.
    
</dd>
</dl>

<dl>
<dd>

**top_p:** `typing.Optional[float]` — Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both.
    
</dd>
</dl>

<dl>
<dd>

**tools:** `typing.Optional[typing.Sequence[ToolsFunctionTool]]` — (Advanced) List of tools that are provided in addition to agent's default set of tools.
    
</dd>
</dl>

<dl>
<dd>

**tool_choice:** `typing.Optional[ChatChatInputDataToolChoice]` — Can be one of existing tools given to the agent earlier or the ones provided in this request.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">history_route_history</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get history of a Session
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.history_route_history(
    id="id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of parent
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">history_route_delete</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Clear the history of a Session (resets the Session)
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.history_route_delete(
    id="id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of the resource
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">task_executions_route_list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List executions of the given task
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of parent
    
</dd>
</dl>

<dl>
<dd>

**limit:** `CommonLimit` — Limit the number of items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the items returned
    
</dd>
</dl>

<dl>
<dd>

**sort_by:** `TaskExecutionsRouteListRequestSortBy` — Sort by a field
    
</dd>
</dl>

<dl>
<dd>

**direction:** `TaskExecutionsRouteListRequestDirection` — Sort direction
    
</dd>
</dl>

<dl>
<dd>

**metadata_filter:** `str` — JSON string of object that should be used to filter objects by metadata
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">task_executions_route_create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create an execution for the given task
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.task_executions_route_create(
    id="id",
    input={"key": "value"},
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of parent resource
    
</dd>
</dl>

<dl>
<dd>

**input:** `typing.Dict[str, typing.Any]` — The input to the execution
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">users_route_list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List users (paginated)
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**limit:** `CommonLimit` — Limit the number of items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the items returned
    
</dd>
</dl>

<dl>
<dd>

**sort_by:** `UsersRouteListRequestSortBy` — Sort by a field
    
</dd>
</dl>

<dl>
<dd>

**direction:** `UsersRouteListRequestDirection` — Sort direction
    
</dd>
</dl>

<dl>
<dd>

**metadata_filter:** `str` — JSON string of object that should be used to filter objects by metadata
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">users_route_create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a new user
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.users_route_create(
    name="name",
    about="about",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**name:** `CommonIdentifierSafeUnicode` — Name of the user
    
</dd>
</dl>

<dl>
<dd>

**about:** `str` — About the user
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">users_route_get</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get a user by id
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.users_route_get(
    id="id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of the resource
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">users_route_create_or_update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create or update a user
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` 
    
</dd>
</dl>

<dl>
<dd>

**name:** `CommonIdentifierSafeUnicode` — Name of the user
    
</dd>
</dl>

<dl>
<dd>

**about:** `str` — About the user
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">users_route_update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update an existing user by id (overwrite existing values)
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of the resource
    
</dd>
</dl>

<dl>
<dd>

**name:** `CommonIdentifierSafeUnicode` — Name of the user
    
</dd>
</dl>

<dl>
<dd>

**about:** `str` — About the user
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">users_route_delete</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete a user by id
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.users_route_delete(
    id="id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of the resource
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">users_route_patch</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update an existing user by id (merge with existing values)
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.users_route_patch(
    id="id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of the resource
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**name:** `typing.Optional[CommonIdentifierSafeUnicode]` — Name of the user
    
</dd>
</dl>

<dl>
<dd>

**about:** `typing.Optional[str]` — About the user
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">user_docs_route_list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List Docs owned by a User
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of parent
    
</dd>
</dl>

<dl>
<dd>

**limit:** `CommonLimit` — Limit the number of items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the items returned
    
</dd>
</dl>

<dl>
<dd>

**sort_by:** `UserDocsRouteListRequestSortBy` — Sort by a field
    
</dd>
</dl>

<dl>
<dd>

**direction:** `UserDocsRouteListRequestDirection` — Sort direction
    
</dd>
</dl>

<dl>
<dd>

**metadata_filter:** `str` — JSON string of object that should be used to filter objects by metadata
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">user_docs_route_create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a Doc for this User
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of parent resource
    
</dd>
</dl>

<dl>
<dd>

**title:** `CommonIdentifierSafeUnicode` — Title describing what this document contains
    
</dd>
</dl>

<dl>
<dd>

**content:** `DocsCreateDocRequestContent` — Contents of the document
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">user_docs_route_delete</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete a Doc for this User
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.user_docs_route_delete(
    id="id",
    child_id="child_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of parent resource
    
</dd>
</dl>

<dl>
<dd>

**child_id:** `CommonUuid` — ID of the resource to be deleted
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">user_docs_search_route_search</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Search Docs owned by a User
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
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

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `CommonUuid` — ID of the parent
    
</dd>
</dl>

<dl>
<dd>

**body:** `UserDocsSearchRouteSearchRequestBody` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

