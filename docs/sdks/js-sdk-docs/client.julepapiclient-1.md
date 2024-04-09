# Client

[@julep/sdk](./) / [Modules](modules.md) / [Client](../../js-sdk-docs/modules/Client.md) / JulepApiClient

## Class: JulepApiClient

[Client](../../js-sdk-docs/modules/Client.md).JulepApiClient

### Table of contents

#### Constructors

* [constructor](client.julepapiclient-1.md#constructor)

#### Properties

* [\_options](client.julepapiclient-1.md#\_options)

#### Methods

* [\_getAuthorizationHeader](client.julepapiclient-1.md#\_getauthorizationheader)
* [chat](client.julepapiclient-1.md#chat)
* [createAgent](client.julepapiclient-1.md#createagent)
* [createAgentDoc](client.julepapiclient-1.md#createagentdoc)
* [createAgentTool](client.julepapiclient-1.md#createagenttool)
* [createSession](client.julepapiclient-1.md#createsession)
* [createUser](client.julepapiclient-1.md#createuser)
* [createUserDoc](client.julepapiclient-1.md#createuserdoc)
* [deleteAgent](client.julepapiclient-1.md#deleteagent)
* [deleteAgentDoc](client.julepapiclient-1.md#deleteagentdoc)
* [deleteAgentMemory](client.julepapiclient-1.md#deleteagentmemory)
* [deleteAgentTool](client.julepapiclient-1.md#deleteagenttool)
* [deleteSession](client.julepapiclient-1.md#deletesession)
* [deleteUser](client.julepapiclient-1.md#deleteuser)
* [deleteUserDoc](client.julepapiclient-1.md#deleteuserdoc)
* [getAgent](client.julepapiclient-1.md#getagent)
* [getAgentDocs](client.julepapiclient-1.md#getagentdocs)
* [getAgentMemories](client.julepapiclient-1.md#getagentmemories)
* [getAgentTools](client.julepapiclient-1.md#getagenttools)
* [getHistory](client.julepapiclient-1.md#gethistory)
* [getSession](client.julepapiclient-1.md#getsession)
* [getSuggestions](client.julepapiclient-1.md#getsuggestions)
* [getUser](client.julepapiclient-1.md#getuser)
* [getUserDocs](client.julepapiclient-1.md#getuserdocs)
* [listAgents](client.julepapiclient-1.md#listagents)
* [listSessions](client.julepapiclient-1.md#listsessions)
* [listUsers](client.julepapiclient-1.md#listusers)
* [updateAgent](client.julepapiclient-1.md#updateagent)
* [updateAgentTool](client.julepapiclient-1.md#updateagenttool)
* [updateSession](client.julepapiclient-1.md#updatesession)
* [updateUser](client.julepapiclient-1.md#updateuser)

### Constructors

#### constructor

• **new JulepApiClient**(`_options`): [`JulepApiClient`](client.julepapiclient-1.md)

**Parameters**

| Name       | Type                                                                       |
| ---------- | -------------------------------------------------------------------------- |
| `_options` | [`Options`](../../js-sdk-docs/interfaces/Client.JulepApiClient.Options.md) |

**Returns**

[`JulepApiClient`](client.julepapiclient-1.md)

**Defined in**

[src/api/Client.d.ts:19](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L19)

### Properties

#### \_options

• `Protected` `Readonly` **\_options**: [`Options`](../../js-sdk-docs/interfaces/Client.JulepApiClient.Options.md)

**Defined in**

[src/api/Client.d.ts:18](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L18)

### Methods

#### \_getAuthorizationHeader

▸ **\_getAuthorizationHeader**(): `Promise`<`string`>

**Returns**

`Promise`<`string`>

**Defined in**

[src/api/Client.d.ts:373](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L373)

***

#### chat

▸ **chat**(`sessionId`, `request`, `requestOptions?`): `Promise`<[`ChatResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ChatResponse.md)>

**Parameters**

| Name              | Type                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `sessionId`       | `string`                                                                                 |
| `request`         | [`ChatInput`](../../js-sdk-docs/interfaces/index.JulepApi.ChatInput.md)                  |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md) |

**Returns**

`Promise`<[`ChatResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ChatResponse.md)>

**`Example`**

```ts
await julepApi.chat("session_id", {
        accept: "application/json",
        messages: [{
                role: JulepApi.InputChatMlMessageRole.User,
                content: "content"
            }]
    })
```

**Defined in**

[src/api/Client.d.ts:154](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L154)

***

#### createAgent

▸ **createAgent**(`request`, `requestOptions?`): `Promise`<[`ResourceCreatedResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ResourceCreatedResponse.md)>

Create a new agent

**Parameters**

| Name              | Type                                                                                      |
| ----------------- | ----------------------------------------------------------------------------------------- |
| `request`         | [`CreateAgentRequest`](../../js-sdk-docs/interfaces/index.JulepApi.CreateAgentRequest.md) |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md)  |

**Returns**

`Promise`<[`ResourceCreatedResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ResourceCreatedResponse.md)>

**`Example`**

```ts
await julepApi.createAgent({
        name: "name",
        about: "about",
        model: "model"
    })
```

**Defined in**

[src/api/Client.d.ts:83](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L83)

***

#### createAgentDoc

▸ **createAgentDoc**(`agentId`, `request`, `requestOptions?`): `Promise`<[`ResourceCreatedResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ResourceCreatedResponse.md)>

**Parameters**

| Name              | Type                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `agentId`         | `string`                                                                                 |
| `request`         | [`CreateDoc`](../../js-sdk-docs/interfaces/index.JulepApi.CreateDoc.md)                  |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md) |

**Returns**

`Promise`<[`ResourceCreatedResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ResourceCreatedResponse.md)>

**`Example`**

```ts
await julepApi.createAgentDoc("agent_id", {
        title: "title",
        content: "content"
    })
```

**Defined in**

[src/api/Client.d.ts:254](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L254)

***

#### createAgentTool

▸ **createAgentTool**(`agentId`, `request`, `requestOptions?`): `Promise`<[`ResourceCreatedResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ResourceCreatedResponse.md)>

**Parameters**

| Name              | Type                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `agentId`         | `string`                                                                                 |
| `request`         | [`CreateToolRequest`](../../js-sdk-docs/interfaces/index.JulepApi.CreateToolRequest.md)  |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md) |

**Returns**

`Promise`<[`ResourceCreatedResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ResourceCreatedResponse.md)>

**`Example`**

```ts
await julepApi.createAgentTool("agent_id", {
        type: JulepApi.CreateToolRequestType.Function,
        function: {
            name: "name",
            parameters: {}
        }
    })
```

**Defined in**

[src/api/Client.d.ts:340](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L340)

***

#### createSession

▸ **createSession**(`request`, `requestOptions?`): `Promise`<[`ResourceCreatedResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ResourceCreatedResponse.md)>

Create a session between an agent and a user

**Parameters**

| Name              | Type                                                                                          |
| ----------------- | --------------------------------------------------------------------------------------------- |
| `request`         | [`CreateSessionRequest`](../../js-sdk-docs/interfaces/index.JulepApi.CreateSessionRequest.md) |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md)      |

**Returns**

`Promise`<[`ResourceCreatedResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ResourceCreatedResponse.md)>

**`Example`**

```ts
await julepApi.createSession({
        userId: "user_id",
        agentId: "agent_id"
    })
```

**Defined in**

[src/api/Client.d.ts:39](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L39)

***

#### createUser

▸ **createUser**(`request?`, `requestOptions?`): `Promise`<[`ResourceCreatedResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ResourceCreatedResponse.md)>

Create a new user

**Parameters**

| Name              | Type                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `request?`        | [`CreateUserRequest`](../../js-sdk-docs/interfaces/index.JulepApi.CreateUserRequest.md)  |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md) |

**Returns**

`Promise`<[`ResourceCreatedResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ResourceCreatedResponse.md)>

**`Example`**

```ts
await julepApi.createUser({})
```

**Defined in**

[src/api/Client.d.ts:59](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L59)

***

#### createUserDoc

▸ **createUserDoc**(`userId`, `request`, `requestOptions?`): `Promise`<[`ResourceCreatedResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ResourceCreatedResponse.md)>

**Parameters**

| Name              | Type                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `userId`          | `string`                                                                                 |
| `request`         | [`CreateDoc`](../../js-sdk-docs/interfaces/index.JulepApi.CreateDoc.md)                  |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md) |

**Returns**

`Promise`<[`ResourceCreatedResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ResourceCreatedResponse.md)>

**`Example`**

```ts
await julepApi.createUserDoc("user_id", {
        title: "title",
        content: "content"
    })
```

**Defined in**

[src/api/Client.d.ts:279](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L279)

***

#### deleteAgent

▸ **deleteAgent**(`agentId`, `requestOptions?`): `Promise`<`void`>

**Parameters**

| Name              | Type                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `agentId`         | `string`                                                                                 |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md) |

**Returns**

`Promise`<`void`>

**`Example`**

```ts
await julepApi.deleteAgent("agent_id")
```

**Defined in**

[src/api/Client.d.ts:230](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L230)

***

#### deleteAgentDoc

▸ **deleteAgentDoc**(`agentId`, `docId`, `requestOptions?`): `Promise`<`void`>

**Parameters**

| Name              | Type                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `agentId`         | `string`                                                                                 |
| `docId`           | `string`                                                                                 |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md) |

**Returns**

`Promise`<`void`>

**`Example`**

```ts
await julepApi.deleteAgentDoc("agent_id", "doc_id")
```

**Defined in**

[src/api/Client.d.ts:301](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L301)

***

#### deleteAgentMemory

▸ **deleteAgentMemory**(`agentId`, `memoryId`, `requestOptions?`): `Promise`<`void`>

**Parameters**

| Name              | Type                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `agentId`         | `string`                                                                                 |
| `memoryId`        | `string`                                                                                 |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md) |

**Returns**

`Promise`<`void`>

**`Example`**

```ts
await julepApi.deleteAgentMemory("agent_id", "memory_id")
```

**Defined in**

[src/api/Client.d.ts:312](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L312)

***

#### deleteAgentTool

▸ **deleteAgentTool**(`agentId`, `toolId`, `requestOptions?`): `Promise`<`void`>

**Parameters**

| Name              | Type                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `agentId`         | `string`                                                                                 |
| `toolId`          | `string`                                                                                 |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md) |

**Returns**

`Promise`<`void`>

**`Example`**

```ts
await julepApi.deleteAgentTool("agent_id", "tool_id")
```

**Defined in**

[src/api/Client.d.ts:368](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L368)

***

#### deleteSession

▸ **deleteSession**(`sessionId`, `requestOptions?`): `Promise`<`void`>

**Parameters**

| Name              | Type                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `sessionId`       | `string`                                                                                 |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md) |

**Returns**

`Promise`<`void`>

**`Example`**

```ts
await julepApi.deleteSession("session_id")
```

**Defined in**

[src/api/Client.d.ts:116](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L116)

***

#### deleteUser

▸ **deleteUser**(`userId`, `requestOptions?`): `Promise`<`void`>

**Parameters**

| Name              | Type                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `userId`          | `string`                                                                                 |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md) |

**Returns**

`Promise`<`void`>

**`Example`**

```ts
await julepApi.deleteUser("user_id")
```

**Defined in**

[src/api/Client.d.ts:199](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L199)

***

#### deleteUserDoc

▸ **deleteUserDoc**(`userId`, `docId`, `requestOptions?`): `Promise`<`void`>

**Parameters**

| Name              | Type                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `userId`          | `string`                                                                                 |
| `docId`           | `string`                                                                                 |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md) |

**Returns**

`Promise`<`void`>

**`Example`**

```ts
await julepApi.deleteUserDoc("user_id", "doc_id")
```

**Defined in**

[src/api/Client.d.ts:290](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L290)

***

#### getAgent

▸ **getAgent**(`agentId`, `requestOptions?`): `Promise`<[`Agent`](../../js-sdk-docs/interfaces/index.JulepApi.Agent.md)>

**Parameters**

| Name              | Type                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `agentId`         | `string`                                                                                 |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md) |

**Returns**

`Promise`<[`Agent`](../../js-sdk-docs/interfaces/index.JulepApi.Agent.md)>

**`Example`**

```ts
await julepApi.getAgent("agent_id")
```

**Defined in**

[src/api/Client.d.ts:209](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L209)

***

#### getAgentDocs

▸ **getAgentDocs**(`agentId`, `request?`, `requestOptions?`): `Promise`<[`GetAgentDocsResponse`](../../js-sdk-docs/interfaces/index.JulepApi.GetAgentDocsResponse.md)>

Sorted (created\_at descending)

**Parameters**

| Name              | Type                                                                                        |
| ----------------- | ------------------------------------------------------------------------------------------- |
| `agentId`         | `string`                                                                                    |
| `request?`        | [`GetAgentDocsRequest`](../../js-sdk-docs/interfaces/index.JulepApi.GetAgentDocsRequest.md) |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md)    |

**Returns**

`Promise`<[`GetAgentDocsResponse`](../../js-sdk-docs/interfaces/index.JulepApi.GetAgentDocsResponse.md)>

**`Example`**

```ts
await julepApi.getAgentDocs("agent_id", {})
```

**Defined in**

[src/api/Client.d.ts:240](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L240)

***

#### getAgentMemories

▸ **getAgentMemories**(`agentId`, `request`, `requestOptions?`): `Promise`<[`GetAgentMemoriesResponse`](../../js-sdk-docs/interfaces/index.JulepApi.GetAgentMemoriesResponse.md)>

Sorted (created\_at descending)

**Parameters**

| Name              | Type                                                                                                |
| ----------------- | --------------------------------------------------------------------------------------------------- |
| `agentId`         | `string`                                                                                            |
| `request`         | [`GetAgentMemoriesRequest`](../../js-sdk-docs/interfaces/index.JulepApi.GetAgentMemoriesRequest.md) |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md)            |

**Returns**

`Promise`<[`GetAgentMemoriesResponse`](../../js-sdk-docs/interfaces/index.JulepApi.GetAgentMemoriesResponse.md)>

**`Example`**

```ts
await julepApi.getAgentMemories("agent_id", {
        query: "query"
    })
```

**Defined in**

[src/api/Client.d.ts:167](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L167)

***

#### getAgentTools

▸ **getAgentTools**(`agentId`, `request?`, `requestOptions?`): `Promise`<[`GetAgentToolsResponse`](../../js-sdk-docs/interfaces/index.JulepApi.GetAgentToolsResponse.md)>

Sorted (created\_at descending)

**Parameters**

| Name              | Type                                                                                          |
| ----------------- | --------------------------------------------------------------------------------------------- |
| `agentId`         | `string`                                                                                      |
| `request?`        | [`GetAgentToolsRequest`](../../js-sdk-docs/interfaces/index.JulepApi.GetAgentToolsRequest.md) |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md)      |

**Returns**

`Promise`<[`GetAgentToolsResponse`](../../js-sdk-docs/interfaces/index.JulepApi.GetAgentToolsResponse.md)>

**`Example`**

```ts
await julepApi.getAgentTools("agent_id", {})
```

**Defined in**

[src/api/Client.d.ts:323](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L323)

***

#### getHistory

▸ **getHistory**(`sessionId`, `request?`, `requestOptions?`): `Promise`<[`GetHistoryResponse`](../../js-sdk-docs/interfaces/index.JulepApi.GetHistoryResponse.md)>

Sorted (created\_at ascending)

**Parameters**

| Name              | Type                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `sessionId`       | `string`                                                                                 |
| `request?`        | [`GetHistoryRequest`](../../js-sdk-docs/interfaces/index.JulepApi.GetHistoryRequest.md)  |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md) |

**Returns**

`Promise`<[`GetHistoryResponse`](../../js-sdk-docs/interfaces/index.JulepApi.GetHistoryResponse.md)>

**`Example`**

```ts
await julepApi.getHistory("session_id", {})
```

**Defined in**

[src/api/Client.d.ts:137](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L137)

***

#### getSession

▸ **getSession**(`sessionId`, `requestOptions?`): `Promise`<[`Session`](../../js-sdk-docs/interfaces/index.JulepApi.Session.md)>

**Parameters**

| Name              | Type                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `sessionId`       | `string`                                                                                 |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md) |

**Returns**

`Promise`<[`Session`](../../js-sdk-docs/interfaces/index.JulepApi.Session.md)>

**`Example`**

```ts
await julepApi.getSession("session_id")
```

**Defined in**

[src/api/Client.d.ts:93](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L93)

***

#### getSuggestions

▸ **getSuggestions**(`sessionId`, `request?`, `requestOptions?`): `Promise`<[`GetSuggestionsResponse`](../../js-sdk-docs/interfaces/index.JulepApi.GetSuggestionsResponse.md)>

Sorted (created\_at descending)

**Parameters**

| Name              | Type                                                                                            |
| ----------------- | ----------------------------------------------------------------------------------------------- |
| `sessionId`       | `string`                                                                                        |
| `request?`        | [`GetSuggestionsRequest`](../../js-sdk-docs/interfaces/index.JulepApi.GetSuggestionsRequest.md) |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md)        |

**Returns**

`Promise`<[`GetSuggestionsResponse`](../../js-sdk-docs/interfaces/index.JulepApi.GetSuggestionsResponse.md)>

**`Example`**

```ts
await julepApi.getSuggestions("session_id", {})
```

**Defined in**

[src/api/Client.d.ts:126](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L126)

***

#### getUser

▸ **getUser**(`userId`, `requestOptions?`): `Promise`<[`User`](../../js-sdk-docs/interfaces/index.JulepApi.User.md)>

**Parameters**

| Name              | Type                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `userId`          | `string`                                                                                 |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md) |

**Returns**

`Promise`<[`User`](../../js-sdk-docs/interfaces/index.JulepApi.User.md)>

**`Example`**

```ts
await julepApi.getUser("user_id")
```

**Defined in**

[src/api/Client.d.ts:178](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L178)

***

#### getUserDocs

▸ **getUserDocs**(`userId`, `request?`, `requestOptions?`): `Promise`<[`GetUserDocsResponse`](../../js-sdk-docs/interfaces/index.JulepApi.GetUserDocsResponse.md)>

Sorted (created\_at descending)

**Parameters**

| Name              | Type                                                                                      |
| ----------------- | ----------------------------------------------------------------------------------------- |
| `userId`          | `string`                                                                                  |
| `request?`        | [`GetUserDocsRequest`](../../js-sdk-docs/interfaces/index.JulepApi.GetUserDocsRequest.md) |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md)  |

**Returns**

`Promise`<[`GetUserDocsResponse`](../../js-sdk-docs/interfaces/index.JulepApi.GetUserDocsResponse.md)>

**`Example`**

```ts
await julepApi.getUserDocs("user_id", {})
```

**Defined in**

[src/api/Client.d.ts:265](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L265)

***

#### listAgents

▸ **listAgents**(`request?`, `requestOptions?`): `Promise`<[`ListAgentsResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ListAgentsResponse.md)>

List agents created (use limit/offset pagination to get large number of sessions; sorted by descending order of `created_at`)

**Parameters**

| Name              | Type                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `request?`        | [`ListAgentsRequest`](../../js-sdk-docs/interfaces/index.JulepApi.ListAgentsRequest.md)  |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md) |

**Returns**

`Promise`<[`ListAgentsResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ListAgentsResponse.md)>

**`Example`**

```ts
await julepApi.listAgents({})
```

**Defined in**

[src/api/Client.d.ts:69](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L69)

***

#### listSessions

▸ **listSessions**(`request?`, `requestOptions?`): `Promise`<[`ListSessionsResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ListSessionsResponse.md)>

List sessions created (use limit/offset pagination to get large number of sessions; sorted by descending order of `created_at`)

**Parameters**

| Name              | Type                                                                                        |
| ----------------- | ------------------------------------------------------------------------------------------- |
| `request?`        | [`ListSessionsRequest`](../../js-sdk-docs/interfaces/index.JulepApi.ListSessionsRequest.md) |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md)    |

**Returns**

`Promise`<[`ListSessionsResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ListSessionsResponse.md)>

**`Example`**

```ts
await julepApi.listSessions({})
```

**Defined in**

[src/api/Client.d.ts:26](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L26)

***

#### listUsers

▸ **listUsers**(`request?`, `requestOptions?`): `Promise`<[`ListUsersResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ListUsersResponse.md)>

List users created (use limit/offset pagination to get large number of sessions; sorted by descending order of `created_at`)

**Parameters**

| Name              | Type                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `request?`        | [`ListUsersRequest`](../../js-sdk-docs/interfaces/index.JulepApi.ListUsersRequest.md)    |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md) |

**Returns**

`Promise`<[`ListUsersResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ListUsersResponse.md)>

**`Example`**

```ts
await julepApi.listUsers({})
```

**Defined in**

[src/api/Client.d.ts:49](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L49)

***

#### updateAgent

▸ **updateAgent**(`agentId`, `request?`, `requestOptions?`): `Promise`<[`ResourceUpdatedResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ResourceUpdatedResponse.md)>

**Parameters**

| Name              | Type                                                                                      |
| ----------------- | ----------------------------------------------------------------------------------------- |
| `agentId`         | `string`                                                                                  |
| `request?`        | [`UpdateAgentRequest`](../../js-sdk-docs/interfaces/index.JulepApi.UpdateAgentRequest.md) |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md)  |

**Returns**

`Promise`<[`ResourceUpdatedResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ResourceUpdatedResponse.md)>

**`Example`**

```ts
await julepApi.updateAgent("agent_id", {})
```

**Defined in**

[src/api/Client.d.ts:219](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L219)

***

#### updateAgentTool

▸ **updateAgentTool**(`agentId`, `toolId`, `request`, `requestOptions?`): `Promise`<[`ResourceUpdatedResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ResourceUpdatedResponse.md)>

**Parameters**

| Name              | Type                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `agentId`         | `string`                                                                                 |
| `toolId`          | `string`                                                                                 |
| `request`         | [`UpdateToolRequest`](../../js-sdk-docs/interfaces/index.JulepApi.UpdateToolRequest.md)  |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md) |

**Returns**

`Promise`<[`ResourceUpdatedResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ResourceUpdatedResponse.md)>

**`Example`**

```ts
await julepApi.updateAgentTool("agent_id", "tool_id", {
        function: {
            name: "name",
            parameters: {}
        }
    })
```

**Defined in**

[src/api/Client.d.ts:356](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L356)

***

#### updateSession

▸ **updateSession**(`sessionId`, `request`, `requestOptions?`): `Promise`<[`ResourceUpdatedResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ResourceUpdatedResponse.md)>

**Parameters**

| Name              | Type                                                                                          |
| ----------------- | --------------------------------------------------------------------------------------------- |
| `sessionId`       | `string`                                                                                      |
| `request`         | [`UpdateSessionRequest`](../../js-sdk-docs/interfaces/index.JulepApi.UpdateSessionRequest.md) |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md)      |

**Returns**

`Promise`<[`ResourceUpdatedResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ResourceUpdatedResponse.md)>

**`Example`**

```ts
await julepApi.updateSession("session_id", {
        situation: "situation"
    })
```

**Defined in**

[src/api/Client.d.ts:105](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L105)

***

#### updateUser

▸ **updateUser**(`userId`, `request?`, `requestOptions?`): `Promise`<[`ResourceUpdatedResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ResourceUpdatedResponse.md)>

**Parameters**

| Name              | Type                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `userId`          | `string`                                                                                 |
| `request?`        | [`UpdateUserRequest`](../../js-sdk-docs/interfaces/index.JulepApi.UpdateUserRequest.md)  |
| `requestOptions?` | [`RequestOptions`](../../js-sdk-docs/interfaces/Client.JulepApiClient.RequestOptions.md) |

**Returns**

`Promise`<[`ResourceUpdatedResponse`](../../js-sdk-docs/interfaces/index.JulepApi.ResourceUpdatedResponse.md)>

**`Example`**

```ts
await julepApi.updateUser("user_id", {})
```

**Defined in**

[src/api/Client.d.ts:188](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/Client.d.ts#L188)
