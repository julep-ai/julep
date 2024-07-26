# Reference
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
    limit=1,
    offset=1,
    sort_by="created_at",
    direction="asc",
    metadata_filter="metadata_filter",
    body=DocsVectorDocSearchRequest(
        confidence=1.1,
        alpha=1.1,
        mmr=True,
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

**sort_by:** `AgentsDocsSearchRouteSearchRequestSortBy` — Sort by a field
    
</dd>
</dl>

<dl>
<dd>

**direction:** `AgentsDocsSearchRouteSearchRequestDirection` — Sort direction
    
</dd>
</dl>

<dl>
<dd>

**metadata_filter:** `str` — JSON string of object that should be used to filter objects by metadata
    
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
from julep import TasksEvaluateStep, TasksTaskTool
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.tasks_route_create(
    id="id",
    name="name",
    description="description",
    main=[
        TasksEvaluateStep(
            evaluate={"key": "value"},
        )
    ],
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
from julep import TasksEvaluateStep, TasksTaskTool
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.tasks_route_update(
    id="id",
    child_id="child_id",
    description="description",
    main=[
        TasksEvaluateStep(
            evaluate={"key": "value"},
        )
    ],
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

<details><summary><code>client.<a href="src/julep/client.py">individual_docs_route_delete</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete an existing Doc by id
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
client.individual_docs_route_delete(
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
from julep import ChatRouteGenerateRequestPreset, EntriesInputChatMlMessage
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.chat_route_generate(
    id="id",
    request=ChatRouteGenerateRequestPreset(
        messages=[
            EntriesInputChatMlMessage(
                role="user",
                content="content",
            )
        ],
        recall=True,
        remember=True,
        save=True,
        stream=True,
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

**id:** `CommonUuid` — The session ID
    
</dd>
</dl>

<dl>
<dd>

**request:** `ChatRouteGenerateRequest` 
    
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

<details><summary><code>client.<a href="src/julep/client.py">history_route_list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get history of a Session (paginated)
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
client.history_route_list(
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

**sort_by:** `HistoryRouteListRequestSortBy` — Sort by a field
    
</dd>
</dl>

<dl>
<dd>

**direction:** `HistoryRouteListRequestDirection` — Sort direction
    
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

<details><summary><code>client.<a href="src/julep/client.py">task_executions_route_resume_with_task_token</a>(...)</code></summary>
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
client.task_executions_route_resume_with_task_token(
    id="id",
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

**id:** `CommonUuid` — ID of parent Task
    
</dd>
</dl>

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

<details><summary><code>client.<a href="src/julep/client.py">task_executions_route_update</a>(...)</code></summary>
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
client.task_executions_route_update(
    id="string",
    child_id="string",
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
    limit=1,
    offset=1,
    sort_by="created_at",
    direction="asc",
    metadata_filter="metadata_filter",
    body=DocsVectorDocSearchRequest(
        confidence=1.1,
        alpha=1.1,
        mmr=True,
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

**sort_by:** `UserDocsSearchRouteSearchRequestSortBy` — Sort by a field
    
</dd>
</dl>

<dl>
<dd>

**direction:** `UserDocsSearchRouteSearchRequestDirection` — Sort direction
    
</dd>
</dl>

<dl>
<dd>

**metadata_filter:** `str` — JSON string of object that should be used to filter objects by metadata
    
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

