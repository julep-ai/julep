# Reference
<details><summary><code>client.<a href="src/julep/client.py">agents_route_list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List undefined items
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

**limit:** `CommonLimit` — Limit the number of undefined items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the undefined items returned
    
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

Create new undefined
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
    docs=[],
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

**docs:** `typing.Sequence[typing.Any]` — Documents to index for this agent. (Max: 100 items)
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**default_settings:** `typing.Optional[AgentsCreateAgentRequestDefaultSettings]` — Default settings for all sessions created by this agent
    
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

Create or update undefined (ID is required in payload; existing resource will be overwritten)
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

**instructions:** `AgentsCreateOrUpdateAgentRequestInstructions` — Instructions for the agent
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**default_settings:** `typing.Optional[AgentsCreateOrUpdateAgentRequestDefaultSettings]` — Default settings for all sessions created by this agent
    
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

Get undefined by id
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

**id:** `CommonUuid` — ID of the undefined
    
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

Update undefined by id (overwrite)
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

**id:** `CommonUuid` — ID of the undefined
    
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

**default_settings:** `typing.Optional[AgentsUpdateAgentRequestDefaultSettings]` — Default settings for all sessions created by this agent
    
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

Delete undefined by id
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

**id:** `CommonUuid` — ID of the undefined
    
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

Patch undefined by id (merge changes)
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

**id:** `CommonUuid` — ID of the undefined
    
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

**default_settings:** `typing.Optional[AgentsPatchAgentRequestDefaultSettings]` — Default settings for all sessions created by this agent
    
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

List undefined items of parent undefined
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

**id:** `CommonUuid` — ID of parent undefined
    
</dd>
</dl>

<dl>
<dd>

**limit:** `CommonLimit` — Limit the number of undefined items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the undefined items returned
    
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

Search for documents owned by undefined
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
from julep import DocsDocSearchRequest_Vector
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.agents_docs_search_route_search(
    id="string",
    limit=1,
    offset=1,
    sort_by="created_at",
    direction="asc",
    metadata_filter="string",
    body=DocsDocSearchRequest_Vector(
        text="string",
        vector=[1.1],
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

**id:** `CommonUuid` — ID of the undefined
    
</dd>
</dl>

<dl>
<dd>

**limit:** `CommonLimit` — Limit the number of undefined items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the undefined items returned
    
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

**body:** `DocsDocSearchRequest` 
    
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

List undefined items of parent undefined
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

**id:** `CommonUuid` — ID of parent undefined
    
</dd>
</dl>

<dl>
<dd>

**limit:** `CommonLimit` — Limit the number of undefined items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the undefined items returned
    
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

Create new undefined
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
    docs=[],
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

**id:** `CommonUuid` — ID of parent undefined
    
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

**docs:** `typing.Sequence[typing.Any]` — Documents to index for this agent. (Max: 100 items)
    
</dd>
</dl>

<dl>
<dd>

**metadata:** `typing.Optional[typing.Dict[str, typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**default_settings:** `typing.Optional[AgentsCreateAgentRequestDefaultSettings]` — Default settings for all sessions created by this agent
    
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

Get undefined by id
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

**id:** `CommonUuid` — ID of the undefined
    
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

Delete undefined by id
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

**id:** `CommonUuid` — ID of the undefined
    
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

Get undefined by id
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

**id:** `CommonUuid` — ID of the undefined
    
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

Update undefined by id (overwrite)
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

**id:** `CommonUuid` — ID of the undefined
    
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

List undefined items of parent undefined
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

**id:** `CommonUuid` — ID of parent undefined
    
</dd>
</dl>

<dl>
<dd>

**limit:** `CommonLimit` — Limit the number of undefined items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the undefined items returned
    
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

Get undefined by id
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

**id:** `CommonUuid` — ID of the undefined
    
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

List undefined items
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

**limit:** `CommonLimit` — Limit the number of undefined items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the undefined items returned
    
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

Create new undefined
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

**context_overflow:** `typing.Optional[str]` — Action to start on context window overflow
    
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

<details><summary><code>client.<a href="src/julep/client.py">sessions_route_create_or_update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create or update undefined (ID is required in payload; existing resource will be overwritten)
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

**context_overflow:** `typing.Optional[str]` — Action to start on context window overflow
    
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

<details><summary><code>client.<a href="src/julep/client.py">history_route_list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List undefined items of parent undefined
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

**id:** `CommonUuid` — ID of parent undefined
    
</dd>
</dl>

<dl>
<dd>

**limit:** `CommonLimit` — Limit the number of undefined items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the undefined items returned
    
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

Delete undefined by id
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

**id:** `CommonUuid` — ID of the undefined
    
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

Get undefined by id
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

**id:** `CommonUuid` — ID of the undefined
    
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

Update undefined by id (overwrite)
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

**id:** `CommonUuid` — ID of the undefined
    
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

**context_overflow:** `typing.Optional[str]` — Action to start on context window overflow
    
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

Delete undefined by id
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

**id:** `CommonUuid` — ID of the undefined
    
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

Patch undefined by id (merge changes)
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

**id:** `CommonUuid` — ID of the undefined
    
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

**context_overflow:** `typing.Optional[str]` — Action to start on context window overflow
    
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

<details><summary><code>client.<a href="src/julep/client.py">tasks_route_list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List undefined items
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

**limit:** `CommonLimit` — Limit the number of undefined items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the undefined items returned
    
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

Create new undefined
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
from julep import ToolsCreateToolRequest
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.tasks_route_create(
    name="name",
    description="description",
    main=[],
    tools=[
        ToolsCreateToolRequest(
            type="function",
            background=True,
            interactive=True,
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

**main:** `typing.Sequence[TasksWorkflowStep]` — The entrypoint of the task.
    
</dd>
</dl>

<dl>
<dd>

**tools:** `typing.Sequence[ToolsCreateToolRequest]` — Tools defined specifically for this task not included in the Agent itself.
    
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

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/julep/client.py">tasks_route_create_or_update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create or update undefined (ID is required in payload; existing resource will be overwritten)
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
from julep import ToolsCreateToolRequest
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.tasks_route_create_or_update(
    id="id",
    name="name",
    description="description",
    main=[],
    tools=[
        ToolsCreateToolRequest(
            type="function",
            background=True,
            interactive=True,
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

**main:** `typing.Sequence[TasksWorkflowStep]` — The entrypoint of the task.
    
</dd>
</dl>

<dl>
<dd>

**tools:** `typing.Sequence[ToolsCreateToolRequest]` — Tools defined specifically for this task not included in the Agent itself.
    
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

Update undefined by id (overwrite)
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
from julep import ToolsCreateToolRequest
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.tasks_route_update(
    id="id",
    description="description",
    main=[],
    tools=[
        ToolsCreateToolRequest(
            type="function",
            background=True,
            interactive=True,
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

**id:** `CommonUuid` — ID of the undefined
    
</dd>
</dl>

<dl>
<dd>

**description:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**main:** `typing.Sequence[TasksWorkflowStep]` — The entrypoint of the task.
    
</dd>
</dl>

<dl>
<dd>

**tools:** `typing.Sequence[ToolsCreateToolRequest]` — Tools defined specifically for this task not included in the Agent itself.
    
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

Delete undefined by id
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

**id:** `CommonUuid` — ID of the undefined
    
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

Patch undefined by id (merge changes)
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

**id:** `CommonUuid` — ID of the undefined
    
</dd>
</dl>

<dl>
<dd>

**description:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**main:** `typing.Optional[typing.Sequence[TasksWorkflowStep]]` — The entrypoint of the task.
    
</dd>
</dl>

<dl>
<dd>

**input_schema:** `typing.Optional[typing.Dict[str, typing.Any]]` — The schema for the input to the task. `null` means all inputs are valid.
    
</dd>
</dl>

<dl>
<dd>

**tools:** `typing.Optional[typing.Sequence[ToolsCreateToolRequest]]` — Tools defined specifically for this task not included in the Agent itself.
    
</dd>
</dl>

<dl>
<dd>

**inherit_tools:** `typing.Optional[bool]` — Whether to inherit tools from the parent agent or not. Defaults to true.
    
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

List undefined items of parent undefined
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

**id:** `CommonUuid` — ID of parent undefined
    
</dd>
</dl>

<dl>
<dd>

**limit:** `CommonLimit` — Limit the number of undefined items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the undefined items returned
    
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

Create new undefined
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
    input={},
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

**id:** `CommonUuid` — ID of parent undefined
    
</dd>
</dl>

<dl>
<dd>

**input:** `typing.Dict[str, typing.Any]` — The input to the execution
    
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

<details><summary><code>client.<a href="src/julep/client.py">tool_route_update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update undefined by id (overwrite)
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
client.tool_route_update(
    id="id",
    type="function",
    background=True,
    interactive=True,
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

**id:** `CommonUuid` — ID of the undefined
    
</dd>
</dl>

<dl>
<dd>

**type:** `ToolsToolType` — Whether this tool is a `function`, `api_call`, `system` etc. (Only `function` tool supported right now)
    
</dd>
</dl>

<dl>
<dd>

**background:** `bool` — The tool should be run in the background (not supported at the moment)
    
</dd>
</dl>

<dl>
<dd>

**interactive:** `bool` — Whether the tool that can be run interactively (response should contain "stop" boolean field)
    
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

<details><summary><code>client.<a href="src/julep/client.py">tool_route_delete</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete undefined by id
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
client.tool_route_delete(
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

**id:** `CommonUuid` — ID of the undefined
    
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

<details><summary><code>client.<a href="src/julep/client.py">tool_route_patch</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Patch undefined by id (merge changes)
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
client.tool_route_patch(
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

**id:** `CommonUuid` — ID of the undefined
    
</dd>
</dl>

<dl>
<dd>

**type:** `typing.Optional[ToolsToolType]` — Whether this tool is a `function`, `api_call`, `system` etc. (Only `function` tool supported right now)
    
</dd>
</dl>

<dl>
<dd>

**background:** `typing.Optional[bool]` — The tool should be run in the background (not supported at the moment)
    
</dd>
</dl>

<dl>
<dd>

**interactive:** `typing.Optional[bool]` — Whether the tool that can be run interactively (response should contain "stop" boolean field)
    
</dd>
</dl>

<dl>
<dd>

**function:** `typing.Optional[ToolsFunctionDefUpdate]` 
    
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

<details><summary><code>client.<a href="src/julep/client.py">users_route_list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List undefined items
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

**limit:** `CommonLimit` — Limit the number of undefined items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the undefined items returned
    
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

Create new undefined
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
    docs=[],
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

**docs:** `typing.Sequence[typing.Any]` — Documents to index for this user. (Max: 100 items)
    
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

<details><summary><code>client.<a href="src/julep/client.py">users_route_create_or_update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create or update undefined (ID is required in payload; existing resource will be overwritten)
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

<details><summary><code>client.<a href="src/julep/client.py">users_route_get</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get undefined by id
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

**id:** `CommonUuid` — ID of the undefined
    
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

Update undefined by id (overwrite)
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

**id:** `CommonUuid` — ID of the undefined
    
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

Delete undefined by id
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

**id:** `CommonUuid` — ID of the undefined
    
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

Patch undefined by id (merge changes)
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

**id:** `CommonUuid` — ID of the undefined
    
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

List undefined items of parent undefined
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

**id:** `CommonUuid` — ID of parent undefined
    
</dd>
</dl>

<dl>
<dd>

**limit:** `CommonLimit` — Limit the number of undefined items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the undefined items returned
    
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

Search for documents owned by undefined
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
from julep import DocsDocSearchRequest_Vector
from julep.client import JulepApi

client = JulepApi(
    auth_key="YOUR_AUTH_KEY",
    api_key="YOUR_API_KEY",
)
client.user_docs_search_route_search(
    id="string",
    limit=1,
    offset=1,
    sort_by="created_at",
    direction="asc",
    metadata_filter="string",
    body=DocsDocSearchRequest_Vector(
        text="string",
        vector=[1.1],
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

**id:** `CommonUuid` — ID of the undefined
    
</dd>
</dl>

<dl>
<dd>

**limit:** `CommonLimit` — Limit the number of undefined items returned
    
</dd>
</dl>

<dl>
<dd>

**offset:** `CommonOffset` — Offset the undefined items returned
    
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

**body:** `DocsDocSearchRequest` 
    
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

