[@julep/sdk](../README.md) / [Modules](../modules.md) / [Client](../modules/Client.md) / JulepApiClient

# Class: JulepApiClient

[Client](../modules/Client.md).JulepApiClient

## Table of contents

### Constructors

- [constructor](Client.JulepApiClient-1.md#constructor)

### Properties

- [\_options](Client.JulepApiClient-1.md#_options)

### Methods

- [\_getAuthorizationHeader](Client.JulepApiClient-1.md#_getauthorizationheader)
- [chat](Client.JulepApiClient-1.md#chat)
- [createAgent](Client.JulepApiClient-1.md#createagent)
- [createAgentDoc](Client.JulepApiClient-1.md#createagentdoc)
- [createAgentTool](Client.JulepApiClient-1.md#createagenttool)
- [createSession](Client.JulepApiClient-1.md#createsession)
- [createUser](Client.JulepApiClient-1.md#createuser)
- [createUserDoc](Client.JulepApiClient-1.md#createuserdoc)
- [deleteAgent](Client.JulepApiClient-1.md#deleteagent)
- [deleteAgentDoc](Client.JulepApiClient-1.md#deleteagentdoc)
- [deleteAgentMemory](Client.JulepApiClient-1.md#deleteagentmemory)
- [deleteAgentTool](Client.JulepApiClient-1.md#deleteagenttool)
- [deleteSession](Client.JulepApiClient-1.md#deletesession)
- [deleteUser](Client.JulepApiClient-1.md#deleteuser)
- [deleteUserDoc](Client.JulepApiClient-1.md#deleteuserdoc)
- [getAgent](Client.JulepApiClient-1.md#getagent)
- [getAgentDocs](Client.JulepApiClient-1.md#getagentdocs)
- [getAgentMemories](Client.JulepApiClient-1.md#getagentmemories)
- [getAgentTools](Client.JulepApiClient-1.md#getagenttools)
- [getHistory](Client.JulepApiClient-1.md#gethistory)
- [getJobStatus](Client.JulepApiClient-1.md#getjobstatus)
- [getSession](Client.JulepApiClient-1.md#getsession)
- [getSuggestions](Client.JulepApiClient-1.md#getsuggestions)
- [getUser](Client.JulepApiClient-1.md#getuser)
- [getUserDocs](Client.JulepApiClient-1.md#getuserdocs)
- [listAgents](Client.JulepApiClient-1.md#listagents)
- [listSessions](Client.JulepApiClient-1.md#listsessions)
- [listUsers](Client.JulepApiClient-1.md#listusers)
- [updateAgent](Client.JulepApiClient-1.md#updateagent)
- [updateAgentTool](Client.JulepApiClient-1.md#updateagenttool)
- [updateSession](Client.JulepApiClient-1.md#updatesession)
- [updateUser](Client.JulepApiClient-1.md#updateuser)

## Constructors

### constructor

• **new JulepApiClient**(`_options`): [`JulepApiClient`](Client.JulepApiClient-1.md)

#### Parameters

| Name | Type |
| :------ | :------ |
| `_options` | [`Options`](../interfaces/Client.JulepApiClient.Options.md) |

#### Returns

[`JulepApiClient`](Client.JulepApiClient-1.md)

#### Defined in

[src/api/Client.d.ts:20](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L20)

## Properties

### \_options

• `Protected` `Readonly` **\_options**: [`Options`](../interfaces/Client.JulepApiClient.Options.md)

#### Defined in

[src/api/Client.d.ts:19](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L19)

## Methods

### \_getAuthorizationHeader

▸ **_getAuthorizationHeader**(): `Promise`\<`string`\>

#### Returns

`Promise`\<`string`\>

#### Defined in

[src/api/Client.d.ts:385](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L385)

___

### chat

▸ **chat**(`sessionId`, `request`, `requestOptions?`): `Promise`\<[`ChatResponse`](../interfaces/index.JulepApi.ChatResponse.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `sessionId` | `string` |
| `request` | [`ChatInput`](../interfaces/index.JulepApi.ChatInput.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ChatResponse`](../interfaces/index.JulepApi.ChatResponse.md)\>

**`Example`**

```ts
await julepApi.chat("session_id", {
        accept: "application/json",
        minP: 0.01,
        messages: [{
                role: JulepApi.InputChatMlMessageRole.User,
                content: "content"
            }]
    })
```

#### Defined in

[src/api/Client.d.ts:156](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L156)

___

### createAgent

▸ **createAgent**(`request`, `requestOptions?`): `Promise`\<[`ResourceCreatedResponse`](../interfaces/index.JulepApi.ResourceCreatedResponse.md)\>

Create a new agent

#### Parameters

| Name | Type |
| :------ | :------ |
| `request` | [`CreateAgentRequest`](../interfaces/index.JulepApi.CreateAgentRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ResourceCreatedResponse`](../interfaces/index.JulepApi.ResourceCreatedResponse.md)\>

**`Example`**

```ts
await julepApi.createAgent({
        name: "name",
        about: "about",
        model: "model"
    })
```

#### Defined in

[src/api/Client.d.ts:84](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L84)

___

### createAgentDoc

▸ **createAgentDoc**(`agentId`, `request`, `requestOptions?`): `Promise`\<[`ResourceCreatedResponse`](../interfaces/index.JulepApi.ResourceCreatedResponse.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `request` | [`CreateDoc`](../interfaces/index.JulepApi.CreateDoc.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ResourceCreatedResponse`](../interfaces/index.JulepApi.ResourceCreatedResponse.md)\>

**`Example`**

```ts
await julepApi.createAgentDoc("agent_id", {
        title: "title",
        content: "content"
    })
```

#### Defined in

[src/api/Client.d.ts:256](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L256)

___

### createAgentTool

▸ **createAgentTool**(`agentId`, `request`, `requestOptions?`): `Promise`\<[`ResourceCreatedResponse`](../interfaces/index.JulepApi.ResourceCreatedResponse.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `request` | [`CreateToolRequest`](../interfaces/index.JulepApi.CreateToolRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ResourceCreatedResponse`](../interfaces/index.JulepApi.ResourceCreatedResponse.md)\>

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

#### Defined in

[src/api/Client.d.ts:342](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L342)

___

### createSession

▸ **createSession**(`request`, `requestOptions?`): `Promise`\<[`ResourceCreatedResponse`](../interfaces/index.JulepApi.ResourceCreatedResponse.md)\>

Create a session between an agent and a user

#### Parameters

| Name | Type |
| :------ | :------ |
| `request` | [`CreateSessionRequest`](../interfaces/index.JulepApi.CreateSessionRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ResourceCreatedResponse`](../interfaces/index.JulepApi.ResourceCreatedResponse.md)\>

**`Example`**

```ts
await julepApi.createSession({
        userId: "user_id",
        agentId: "agent_id"
    })
```

#### Defined in

[src/api/Client.d.ts:40](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L40)

___

### createUser

▸ **createUser**(`request?`, `requestOptions?`): `Promise`\<[`ResourceCreatedResponse`](../interfaces/index.JulepApi.ResourceCreatedResponse.md)\>

Create a new user

#### Parameters

| Name | Type |
| :------ | :------ |
| `request?` | [`CreateUserRequest`](../interfaces/index.JulepApi.CreateUserRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ResourceCreatedResponse`](../interfaces/index.JulepApi.ResourceCreatedResponse.md)\>

**`Example`**

```ts
await julepApi.createUser()
```

#### Defined in

[src/api/Client.d.ts:60](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L60)

___

### createUserDoc

▸ **createUserDoc**(`userId`, `request`, `requestOptions?`): `Promise`\<[`ResourceCreatedResponse`](../interfaces/index.JulepApi.ResourceCreatedResponse.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `userId` | `string` |
| `request` | [`CreateDoc`](../interfaces/index.JulepApi.CreateDoc.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ResourceCreatedResponse`](../interfaces/index.JulepApi.ResourceCreatedResponse.md)\>

**`Example`**

```ts
await julepApi.createUserDoc("user_id", {
        title: "title",
        content: "content"
    })
```

#### Defined in

[src/api/Client.d.ts:281](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L281)

___

### deleteAgent

▸ **deleteAgent**(`agentId`, `requestOptions?`): `Promise`\<`void`\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<`void`\>

**`Example`**

```ts
await julepApi.deleteAgent("agent_id")
```

#### Defined in

[src/api/Client.d.ts:232](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L232)

___

### deleteAgentDoc

▸ **deleteAgentDoc**(`agentId`, `docId`, `requestOptions?`): `Promise`\<`void`\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `docId` | `string` |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<`void`\>

**`Example`**

```ts
await julepApi.deleteAgentDoc("agent_id", "doc_id")
```

#### Defined in

[src/api/Client.d.ts:303](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L303)

___

### deleteAgentMemory

▸ **deleteAgentMemory**(`agentId`, `memoryId`, `requestOptions?`): `Promise`\<`void`\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `memoryId` | `string` |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<`void`\>

**`Example`**

```ts
await julepApi.deleteAgentMemory("agent_id", "memory_id")
```

#### Defined in

[src/api/Client.d.ts:314](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L314)

___

### deleteAgentTool

▸ **deleteAgentTool**(`agentId`, `toolId`, `requestOptions?`): `Promise`\<`void`\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `toolId` | `string` |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<`void`\>

**`Example`**

```ts
await julepApi.deleteAgentTool("agent_id", "tool_id")
```

#### Defined in

[src/api/Client.d.ts:370](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L370)

___

### deleteSession

▸ **deleteSession**(`sessionId`, `requestOptions?`): `Promise`\<`void`\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `sessionId` | `string` |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<`void`\>

**`Example`**

```ts
await julepApi.deleteSession("session_id")
```

#### Defined in

[src/api/Client.d.ts:117](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L117)

___

### deleteUser

▸ **deleteUser**(`userId`, `requestOptions?`): `Promise`\<`void`\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `userId` | `string` |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<`void`\>

**`Example`**

```ts
await julepApi.deleteUser("user_id")
```

#### Defined in

[src/api/Client.d.ts:201](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L201)

___

### deleteUserDoc

▸ **deleteUserDoc**(`userId`, `docId`, `requestOptions?`): `Promise`\<`void`\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `userId` | `string` |
| `docId` | `string` |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<`void`\>

**`Example`**

```ts
await julepApi.deleteUserDoc("user_id", "doc_id")
```

#### Defined in

[src/api/Client.d.ts:292](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L292)

___

### getAgent

▸ **getAgent**(`agentId`, `requestOptions?`): `Promise`\<[`Agent`](../interfaces/index.JulepApi.Agent.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`Agent`](../interfaces/index.JulepApi.Agent.md)\>

**`Example`**

```ts
await julepApi.getAgent("agent_id")
```

#### Defined in

[src/api/Client.d.ts:211](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L211)

___

### getAgentDocs

▸ **getAgentDocs**(`agentId`, `request?`, `requestOptions?`): `Promise`\<[`GetAgentDocsResponse`](../interfaces/index.JulepApi.GetAgentDocsResponse.md)\>

Sorted (created_at descending)

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `request?` | [`GetAgentDocsRequest`](../interfaces/index.JulepApi.GetAgentDocsRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`GetAgentDocsResponse`](../interfaces/index.JulepApi.GetAgentDocsResponse.md)\>

**`Example`**

```ts
await julepApi.getAgentDocs("agent_id")
```

#### Defined in

[src/api/Client.d.ts:242](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L242)

___

### getAgentMemories

▸ **getAgentMemories**(`agentId`, `request`, `requestOptions?`): `Promise`\<[`GetAgentMemoriesResponse`](../interfaces/index.JulepApi.GetAgentMemoriesResponse.md)\>

Sorted (created_at descending)

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `request` | [`GetAgentMemoriesRequest`](../interfaces/index.JulepApi.GetAgentMemoriesRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`GetAgentMemoriesResponse`](../interfaces/index.JulepApi.GetAgentMemoriesResponse.md)\>

**`Example`**

```ts
await julepApi.getAgentMemories("agent_id", {
        query: "query"
    })
```

#### Defined in

[src/api/Client.d.ts:169](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L169)

___

### getAgentTools

▸ **getAgentTools**(`agentId`, `request?`, `requestOptions?`): `Promise`\<[`GetAgentToolsResponse`](../interfaces/index.JulepApi.GetAgentToolsResponse.md)\>

Sorted (created_at descending)

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `request?` | [`GetAgentToolsRequest`](../interfaces/index.JulepApi.GetAgentToolsRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`GetAgentToolsResponse`](../interfaces/index.JulepApi.GetAgentToolsResponse.md)\>

**`Example`**

```ts
await julepApi.getAgentTools("agent_id")
```

#### Defined in

[src/api/Client.d.ts:325](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L325)

___

### getHistory

▸ **getHistory**(`sessionId`, `request?`, `requestOptions?`): `Promise`\<[`GetHistoryResponse`](../interfaces/index.JulepApi.GetHistoryResponse.md)\>

Sorted (created_at ascending)

#### Parameters

| Name | Type |
| :------ | :------ |
| `sessionId` | `string` |
| `request?` | [`GetHistoryRequest`](../interfaces/index.JulepApi.GetHistoryRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`GetHistoryResponse`](../interfaces/index.JulepApi.GetHistoryResponse.md)\>

**`Example`**

```ts
await julepApi.getHistory("session_id")
```

#### Defined in

[src/api/Client.d.ts:138](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L138)

___

### getJobStatus

▸ **getJobStatus**(`jobId`, `requestOptions?`): `Promise`\<[`JobStatus`](../interfaces/index.JulepApi.JobStatus.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `jobId` | `string` |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`JobStatus`](../interfaces/index.JulepApi.JobStatus.md)\>

**`Example`**

```ts
await julepApi.getJobStatus("job_id")
```

#### Defined in

[src/api/Client.d.ts:381](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L381)

___

### getSession

▸ **getSession**(`sessionId`, `requestOptions?`): `Promise`\<[`Session`](../interfaces/index.JulepApi.Session.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `sessionId` | `string` |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`Session`](../interfaces/index.JulepApi.Session.md)\>

**`Example`**

```ts
await julepApi.getSession("session_id")
```

#### Defined in

[src/api/Client.d.ts:94](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L94)

___

### getSuggestions

▸ **getSuggestions**(`sessionId`, `request?`, `requestOptions?`): `Promise`\<[`GetSuggestionsResponse`](../interfaces/index.JulepApi.GetSuggestionsResponse.md)\>

Sorted (created_at descending)

#### Parameters

| Name | Type |
| :------ | :------ |
| `sessionId` | `string` |
| `request?` | [`GetSuggestionsRequest`](../interfaces/index.JulepApi.GetSuggestionsRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`GetSuggestionsResponse`](../interfaces/index.JulepApi.GetSuggestionsResponse.md)\>

**`Example`**

```ts
await julepApi.getSuggestions("session_id")
```

#### Defined in

[src/api/Client.d.ts:127](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L127)

___

### getUser

▸ **getUser**(`userId`, `requestOptions?`): `Promise`\<[`User`](../interfaces/index.JulepApi.User.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `userId` | `string` |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`User`](../interfaces/index.JulepApi.User.md)\>

**`Example`**

```ts
await julepApi.getUser("user_id")
```

#### Defined in

[src/api/Client.d.ts:180](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L180)

___

### getUserDocs

▸ **getUserDocs**(`userId`, `request?`, `requestOptions?`): `Promise`\<[`GetUserDocsResponse`](../interfaces/index.JulepApi.GetUserDocsResponse.md)\>

Sorted (created_at descending)

#### Parameters

| Name | Type |
| :------ | :------ |
| `userId` | `string` |
| `request?` | [`GetUserDocsRequest`](../interfaces/index.JulepApi.GetUserDocsRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`GetUserDocsResponse`](../interfaces/index.JulepApi.GetUserDocsResponse.md)\>

**`Example`**

```ts
await julepApi.getUserDocs("user_id")
```

#### Defined in

[src/api/Client.d.ts:267](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L267)

___

### listAgents

▸ **listAgents**(`request?`, `requestOptions?`): `Promise`\<[`ListAgentsResponse`](../interfaces/index.JulepApi.ListAgentsResponse.md)\>

List agents created (use limit/offset pagination to get large number of sessions; sorted by descending order of `created_at`)

#### Parameters

| Name | Type |
| :------ | :------ |
| `request?` | [`ListAgentsRequest`](../interfaces/index.JulepApi.ListAgentsRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ListAgentsResponse`](../interfaces/index.JulepApi.ListAgentsResponse.md)\>

**`Example`**

```ts
await julepApi.listAgents()
```

#### Defined in

[src/api/Client.d.ts:70](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L70)

___

### listSessions

▸ **listSessions**(`request?`, `requestOptions?`): `Promise`\<[`ListSessionsResponse`](../interfaces/index.JulepApi.ListSessionsResponse.md)\>

List sessions created (use limit/offset pagination to get large number of sessions; sorted by descending order of `created_at`)

#### Parameters

| Name | Type |
| :------ | :------ |
| `request?` | [`ListSessionsRequest`](../interfaces/index.JulepApi.ListSessionsRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ListSessionsResponse`](../interfaces/index.JulepApi.ListSessionsResponse.md)\>

**`Example`**

```ts
await julepApi.listSessions()
```

#### Defined in

[src/api/Client.d.ts:27](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L27)

___

### listUsers

▸ **listUsers**(`request?`, `requestOptions?`): `Promise`\<[`ListUsersResponse`](../interfaces/index.JulepApi.ListUsersResponse.md)\>

List users created (use limit/offset pagination to get large number of sessions; sorted by descending order of `created_at`)

#### Parameters

| Name | Type |
| :------ | :------ |
| `request?` | [`ListUsersRequest`](../interfaces/index.JulepApi.ListUsersRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ListUsersResponse`](../interfaces/index.JulepApi.ListUsersResponse.md)\>

**`Example`**

```ts
await julepApi.listUsers()
```

#### Defined in

[src/api/Client.d.ts:50](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L50)

___

### updateAgent

▸ **updateAgent**(`agentId`, `request?`, `requestOptions?`): `Promise`\<[`ResourceUpdatedResponse`](../interfaces/index.JulepApi.ResourceUpdatedResponse.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `request?` | [`UpdateAgentRequest`](../interfaces/index.JulepApi.UpdateAgentRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ResourceUpdatedResponse`](../interfaces/index.JulepApi.ResourceUpdatedResponse.md)\>

**`Example`**

```ts
await julepApi.updateAgent("agent_id")
```

#### Defined in

[src/api/Client.d.ts:221](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L221)

___

### updateAgentTool

▸ **updateAgentTool**(`agentId`, `toolId`, `request`, `requestOptions?`): `Promise`\<[`ResourceUpdatedResponse`](../interfaces/index.JulepApi.ResourceUpdatedResponse.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `toolId` | `string` |
| `request` | [`UpdateToolRequest`](../interfaces/index.JulepApi.UpdateToolRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ResourceUpdatedResponse`](../interfaces/index.JulepApi.ResourceUpdatedResponse.md)\>

**`Example`**

```ts
await julepApi.updateAgentTool("agent_id", "tool_id", {
        function: {
            name: "name",
            parameters: {}
        }
    })
```

#### Defined in

[src/api/Client.d.ts:358](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L358)

___

### updateSession

▸ **updateSession**(`sessionId`, `request`, `requestOptions?`): `Promise`\<[`ResourceUpdatedResponse`](../interfaces/index.JulepApi.ResourceUpdatedResponse.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `sessionId` | `string` |
| `request` | [`UpdateSessionRequest`](../interfaces/index.JulepApi.UpdateSessionRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ResourceUpdatedResponse`](../interfaces/index.JulepApi.ResourceUpdatedResponse.md)\>

**`Example`**

```ts
await julepApi.updateSession("session_id", {
        situation: "situation"
    })
```

#### Defined in

[src/api/Client.d.ts:106](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L106)

___

### updateUser

▸ **updateUser**(`userId`, `request?`, `requestOptions?`): `Promise`\<[`ResourceUpdatedResponse`](../interfaces/index.JulepApi.ResourceUpdatedResponse.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `userId` | `string` |
| `request?` | [`UpdateUserRequest`](../interfaces/index.JulepApi.UpdateUserRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ResourceUpdatedResponse`](../interfaces/index.JulepApi.ResourceUpdatedResponse.md)\>

**`Example`**

```ts
await julepApi.updateUser("user_id")
```

#### Defined in

[src/api/Client.d.ts:190](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/Client.d.ts#L190)
