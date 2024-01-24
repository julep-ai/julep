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
- [createAgentAdditionalInfo](Client.JulepApiClient-1.md#createagentadditionalinfo)
- [createAgentTool](Client.JulepApiClient-1.md#createagenttool)
- [createSession](Client.JulepApiClient-1.md#createsession)
- [createUser](Client.JulepApiClient-1.md#createuser)
- [createUserAdditionalInfo](Client.JulepApiClient-1.md#createuseradditionalinfo)
- [deleteAgent](Client.JulepApiClient-1.md#deleteagent)
- [deleteAgentAdditionalInfo](Client.JulepApiClient-1.md#deleteagentadditionalinfo)
- [deleteAgentMemory](Client.JulepApiClient-1.md#deleteagentmemory)
- [deleteAgentTool](Client.JulepApiClient-1.md#deleteagenttool)
- [deleteSession](Client.JulepApiClient-1.md#deletesession)
- [deleteUser](Client.JulepApiClient-1.md#deleteuser)
- [deleteUserAdditionalInfo](Client.JulepApiClient-1.md#deleteuseradditionalinfo)
- [getAgent](Client.JulepApiClient-1.md#getagent)
- [getAgentAdditionalInfo](Client.JulepApiClient-1.md#getagentadditionalinfo)
- [getAgentMemories](Client.JulepApiClient-1.md#getagentmemories)
- [getAgentTools](Client.JulepApiClient-1.md#getagenttools)
- [getHistory](Client.JulepApiClient-1.md#gethistory)
- [getSession](Client.JulepApiClient-1.md#getsession)
- [getSuggestions](Client.JulepApiClient-1.md#getsuggestions)
- [getUser](Client.JulepApiClient-1.md#getuser)
- [getUserAdditionalInfo](Client.JulepApiClient-1.md#getuseradditionalinfo)
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

[src/api/Client.d.ts:19](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L19)

## Properties

### \_options

• `Protected` `Readonly` **\_options**: [`Options`](../interfaces/Client.JulepApiClient.Options.md)

#### Defined in

[src/api/Client.d.ts:18](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L18)

## Methods

### \_getAuthorizationHeader

▸ **_getAuthorizationHeader**(): `Promise`\<`string`\>

#### Returns

`Promise`\<`string`\>

#### Defined in

[src/api/Client.d.ts:425](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L425)

___

### chat

▸ **chat**(`sessionId`, `request`, `requestOptions?`): `Promise`\<[`ChatResponse`](../interfaces/api_types_ChatResponse.ChatResponse.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `sessionId` | `string` |
| `request` | [`ChatInput`](../interfaces/api_client_requests_ChatInput.ChatInput.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ChatResponse`](../interfaces/api_types_ChatResponse.ChatResponse.md)\>

**`Example`**

```ts
await julepApi.chat("string", {
        accept: "application/json",
        responseFormat: {
            type: JulepApi.ChatSettingsResponseFormatType.Text
        },
        temperature: 1,
        topP: 1,
        messages: [{
                role: JulepApi.InputChatMlMessageRole.User,
                content: "string"
            }],
        tools: [{
                type: JulepApi.ToolType.Function,
                definition: {
                    name: "string",
                    parameters: {
                        "string": "string"
                    }
                },
                id: "string"
            }]
    })
```

#### Defined in

[src/api/Client.d.ts:194](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L194)

___

### createAgent

▸ **createAgent**(`request`, `requestOptions?`): `Promise`\<[`ResourceCreatedResponse`](../interfaces/api_types_ResourceCreatedResponse.ResourceCreatedResponse.md)\>

Create a new agent

#### Parameters

| Name | Type |
| :------ | :------ |
| `request` | [`CreateAgentRequest`](../interfaces/api_client_requests_CreateAgentRequest.CreateAgentRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ResourceCreatedResponse`](../interfaces/api_types_ResourceCreatedResponse.ResourceCreatedResponse.md)\>

**`Example`**

```ts
await julepApi.createAgent({
        name: "string",
        about: "string",
        instructions: [{
                content: "string"
            }],
        tools: [{
                type: JulepApi.CreateToolRequestType.Function,
                definition: {
                    name: "string",
                    parameters: {
                        "string": "string"
                    }
                }
            }],
        defaultSettings: {
            temperature: 1,
            topP: 1
        },
        model: "string",
        additionalInfo: [{
                title: "string",
                content: "string"
            }]
    })
```

#### Defined in

[src/api/Client.d.ts:108](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L108)

___

### createAgentAdditionalInfo

▸ **createAgentAdditionalInfo**(`agentId`, `request`, `requestOptions?`): `Promise`\<[`ResourceCreatedResponse`](../interfaces/api_types_ResourceCreatedResponse.ResourceCreatedResponse.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `request` | [`CreateAdditionalInfoRequest`](../interfaces/api_types_CreateAdditionalInfoRequest.CreateAdditionalInfoRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ResourceCreatedResponse`](../interfaces/api_types_ResourceCreatedResponse.ResourceCreatedResponse.md)\>

**`Example`**

```ts
await julepApi.createAgentAdditionalInfo("string", {
        title: "string",
        content: "string"
    })
```

#### Defined in

[src/api/Client.d.ts:302](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L302)

___

### createAgentTool

▸ **createAgentTool**(`agentId`, `request`, `requestOptions?`): `Promise`\<[`ResourceCreatedResponse`](../interfaces/api_types_ResourceCreatedResponse.ResourceCreatedResponse.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `request` | [`CreateToolRequest`](../interfaces/api_types_CreateToolRequest.CreateToolRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ResourceCreatedResponse`](../interfaces/api_types_ResourceCreatedResponse.ResourceCreatedResponse.md)\>

**`Example`**

```ts
await julepApi.createAgentTool("string", {
        type: JulepApi.CreateToolRequestType.Function,
        definition: {
            name: "string",
            parameters: {
                "string": "string"
            }
        }
    })
```

#### Defined in

[src/api/Client.d.ts:390](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L390)

___

### createSession

▸ **createSession**(`request`, `requestOptions?`): `Promise`\<[`ResourceCreatedResponse`](../interfaces/api_types_ResourceCreatedResponse.ResourceCreatedResponse.md)\>

Create a session between an agent and a user

#### Parameters

| Name | Type |
| :------ | :------ |
| `request` | [`CreateSessionRequest`](../interfaces/api_client_requests_CreateSessionRequest.CreateSessionRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ResourceCreatedResponse`](../interfaces/api_types_ResourceCreatedResponse.ResourceCreatedResponse.md)\>

**`Example`**

```ts
await julepApi.createSession({
        userId: "string",
        agentId: "string"
    })
```

#### Defined in

[src/api/Client.d.ts:39](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L39)

___

### createUser

▸ **createUser**(`request?`, `requestOptions?`): `Promise`\<[`ResourceCreatedResponse`](../interfaces/api_types_ResourceCreatedResponse.ResourceCreatedResponse.md)\>

Create a new user

#### Parameters

| Name | Type |
| :------ | :------ |
| `request?` | [`CreateUserRequest`](../interfaces/api_client_requests_CreateUserRequest.CreateUserRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ResourceCreatedResponse`](../interfaces/api_types_ResourceCreatedResponse.ResourceCreatedResponse.md)\>

**`Example`**

```ts
await julepApi.createUser({
        additionalInformation: [{
                title: "string",
                content: "string"
            }]
    })
```

#### Defined in

[src/api/Client.d.ts:64](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L64)

___

### createUserAdditionalInfo

▸ **createUserAdditionalInfo**(`userId`, `request`, `requestOptions?`): `Promise`\<[`ResourceCreatedResponse`](../interfaces/api_types_ResourceCreatedResponse.ResourceCreatedResponse.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `userId` | `string` |
| `request` | [`CreateAdditionalInfoRequest`](../interfaces/api_types_CreateAdditionalInfoRequest.CreateAdditionalInfoRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ResourceCreatedResponse`](../interfaces/api_types_ResourceCreatedResponse.ResourceCreatedResponse.md)\>

**`Example`**

```ts
await julepApi.createUserAdditionalInfo("string", {
        title: "string",
        content: "string"
    })
```

#### Defined in

[src/api/Client.d.ts:327](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L327)

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
await julepApi.deleteAgent("string")
```

#### Defined in

[src/api/Client.d.ts:278](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L278)

___

### deleteAgentAdditionalInfo

▸ **deleteAgentAdditionalInfo**(`agentId`, `additionalInfoId`, `requestOptions?`): `Promise`\<`void`\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `additionalInfoId` | `string` |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<`void`\>

**`Example`**

```ts
await julepApi.deleteAgentAdditionalInfo("string", "string")
```

#### Defined in

[src/api/Client.d.ts:349](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L349)

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
await julepApi.deleteAgentMemory("string", "string")
```

#### Defined in

[src/api/Client.d.ts:360](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L360)

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
await julepApi.deleteAgentTool("string", "string")
```

#### Defined in

[src/api/Client.d.ts:420](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L420)

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
await julepApi.deleteSession("string")
```

#### Defined in

[src/api/Client.d.ts:141](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L141)

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
await julepApi.deleteUser("string")
```

#### Defined in

[src/api/Client.d.ts:239](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L239)

___

### deleteUserAdditionalInfo

▸ **deleteUserAdditionalInfo**(`userId`, `additionalInfoId`, `requestOptions?`): `Promise`\<`void`\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `userId` | `string` |
| `additionalInfoId` | `string` |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<`void`\>

**`Example`**

```ts
await julepApi.deleteUserAdditionalInfo("string", "string")
```

#### Defined in

[src/api/Client.d.ts:338](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L338)

___

### getAgent

▸ **getAgent**(`agentId`, `requestOptions?`): `Promise`\<[`Agent`](../interfaces/api_types_Agent.Agent.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`Agent`](../interfaces/api_types_Agent.Agent.md)\>

**`Example`**

```ts
await julepApi.getAgent("string")
```

#### Defined in

[src/api/Client.d.ts:249](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L249)

___

### getAgentAdditionalInfo

▸ **getAgentAdditionalInfo**(`agentId`, `request?`, `requestOptions?`): `Promise`\<[`GetAgentAdditionalInfoResponse`](../interfaces/api_types_GetAgentAdditionalInfoResponse.GetAgentAdditionalInfoResponse.md)\>

Sorted (created_at descending)

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `request?` | [`GetAgentAdditionalInfoRequest`](../interfaces/api_client_requests_GetAgentAdditionalInfoRequest.GetAgentAdditionalInfoRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`GetAgentAdditionalInfoResponse`](../interfaces/api_types_GetAgentAdditionalInfoResponse.GetAgentAdditionalInfoResponse.md)\>

**`Example`**

```ts
await julepApi.getAgentAdditionalInfo("string", {})
```

#### Defined in

[src/api/Client.d.ts:288](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L288)

___

### getAgentMemories

▸ **getAgentMemories**(`agentId`, `request`, `requestOptions?`): `Promise`\<[`GetAgentMemoriesResponse`](../interfaces/api_types_GetAgentMemoriesResponse.GetAgentMemoriesResponse.md)\>

Sorted (created_at descending)

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `request` | [`GetAgentMemoriesRequest`](../interfaces/api_client_requests_GetAgentMemoriesRequest.GetAgentMemoriesRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`GetAgentMemoriesResponse`](../interfaces/api_types_GetAgentMemoriesResponse.GetAgentMemoriesResponse.md)\>

**`Example`**

```ts
await julepApi.getAgentMemories("string", {
        query: "string"
    })
```

#### Defined in

[src/api/Client.d.ts:207](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L207)

___

### getAgentTools

▸ **getAgentTools**(`agentId`, `request?`, `requestOptions?`): `Promise`\<[`GetAgentToolsResponse`](../interfaces/api_types_GetAgentToolsResponse.GetAgentToolsResponse.md)\>

Sorted (created_at descending)

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `request?` | [`GetAgentToolsRequest`](../interfaces/api_client_requests_GetAgentToolsRequest.GetAgentToolsRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`GetAgentToolsResponse`](../interfaces/api_types_GetAgentToolsResponse.GetAgentToolsResponse.md)\>

**`Example`**

```ts
await julepApi.getAgentTools("string", {})
```

#### Defined in

[src/api/Client.d.ts:371](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L371)

___

### getHistory

▸ **getHistory**(`sessionId`, `request?`, `requestOptions?`): `Promise`\<[`GetHistoryResponse`](../interfaces/api_types_GetHistoryResponse.GetHistoryResponse.md)\>

Sorted (created_at ascending)

#### Parameters

| Name | Type |
| :------ | :------ |
| `sessionId` | `string` |
| `request?` | [`GetHistoryRequest`](../interfaces/api_client_requests_GetHistoryRequest.GetHistoryRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`GetHistoryResponse`](../interfaces/api_types_GetHistoryResponse.GetHistoryResponse.md)\>

**`Example`**

```ts
await julepApi.getHistory("string", {})
```

#### Defined in

[src/api/Client.d.ts:162](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L162)

___

### getSession

▸ **getSession**(`sessionId`, `requestOptions?`): `Promise`\<[`Session`](../interfaces/api_types_Session.Session.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `sessionId` | `string` |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`Session`](../interfaces/api_types_Session.Session.md)\>

**`Example`**

```ts
await julepApi.getSession("string")
```

#### Defined in

[src/api/Client.d.ts:118](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L118)

___

### getSuggestions

▸ **getSuggestions**(`sessionId`, `request?`, `requestOptions?`): `Promise`\<[`GetSuggestionsResponse`](../interfaces/api_types_GetSuggestionsResponse.GetSuggestionsResponse.md)\>

Sorted (created_at descending)

#### Parameters

| Name | Type |
| :------ | :------ |
| `sessionId` | `string` |
| `request?` | [`GetSuggestionsRequest`](../interfaces/api_client_requests_GetSuggestionsRequest.GetSuggestionsRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`GetSuggestionsResponse`](../interfaces/api_types_GetSuggestionsResponse.GetSuggestionsResponse.md)\>

**`Example`**

```ts
await julepApi.getSuggestions("string", {})
```

#### Defined in

[src/api/Client.d.ts:151](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L151)

___

### getUser

▸ **getUser**(`userId`, `requestOptions?`): `Promise`\<[`User`](../interfaces/api_types_User.User.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `userId` | `string` |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`User`](../interfaces/api_types_User.User.md)\>

**`Example`**

```ts
await julepApi.getUser("string")
```

#### Defined in

[src/api/Client.d.ts:218](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L218)

___

### getUserAdditionalInfo

▸ **getUserAdditionalInfo**(`userId`, `request?`, `requestOptions?`): `Promise`\<[`GetUserAdditionalInfoResponse`](../interfaces/api_types_GetUserAdditionalInfoResponse.GetUserAdditionalInfoResponse.md)\>

Sorted (created_at descending)

#### Parameters

| Name | Type |
| :------ | :------ |
| `userId` | `string` |
| `request?` | [`GetUserAdditionalInfoRequest`](../interfaces/api_client_requests_GetUserAdditionalInfoRequest.GetUserAdditionalInfoRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`GetUserAdditionalInfoResponse`](../interfaces/api_types_GetUserAdditionalInfoResponse.GetUserAdditionalInfoResponse.md)\>

**`Example`**

```ts
await julepApi.getUserAdditionalInfo("string", {})
```

#### Defined in

[src/api/Client.d.ts:313](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L313)

___

### listAgents

▸ **listAgents**(`request?`, `requestOptions?`): `Promise`\<[`ListAgentsResponse`](../interfaces/api_types_ListAgentsResponse.ListAgentsResponse.md)\>

List agents created (use limit/offset pagination to get large number of sessions; sorted by descending order of `created_at`)

#### Parameters

| Name | Type |
| :------ | :------ |
| `request?` | [`ListAgentsRequest`](../interfaces/api_client_requests_ListAgentsRequest.ListAgentsRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ListAgentsResponse`](../interfaces/api_types_ListAgentsResponse.ListAgentsResponse.md)\>

**`Example`**

```ts
await julepApi.listAgents({})
```

#### Defined in

[src/api/Client.d.ts:74](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L74)

___

### listSessions

▸ **listSessions**(`request?`, `requestOptions?`): `Promise`\<[`ListSessionsResponse`](../interfaces/api_types_ListSessionsResponse.ListSessionsResponse.md)\>

List sessions created (use limit/offset pagination to get large number of sessions; sorted by descending order of `created_at`)

#### Parameters

| Name | Type |
| :------ | :------ |
| `request?` | [`ListSessionsRequest`](../interfaces/api_client_requests_ListSessionsRequest.ListSessionsRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ListSessionsResponse`](../interfaces/api_types_ListSessionsResponse.ListSessionsResponse.md)\>

**`Example`**

```ts
await julepApi.listSessions({})
```

#### Defined in

[src/api/Client.d.ts:26](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L26)

___

### listUsers

▸ **listUsers**(`request?`, `requestOptions?`): `Promise`\<[`ListUsersResponse`](../interfaces/api_types_ListUsersResponse.ListUsersResponse.md)\>

List users created (use limit/offset pagination to get large number of sessions; sorted by descending order of `created_at`)

#### Parameters

| Name | Type |
| :------ | :------ |
| `request?` | [`ListUsersRequest`](../interfaces/api_client_requests_ListUsersRequest.ListUsersRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ListUsersResponse`](../interfaces/api_types_ListUsersResponse.ListUsersResponse.md)\>

**`Example`**

```ts
await julepApi.listUsers({})
```

#### Defined in

[src/api/Client.d.ts:49](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L49)

___

### updateAgent

▸ **updateAgent**(`agentId`, `request?`, `requestOptions?`): `Promise`\<[`ResourceUpdatedResponse`](../interfaces/api_types_ResourceUpdatedResponse.ResourceUpdatedResponse.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `request?` | [`UpdateAgentRequest`](../interfaces/api_client_requests_UpdateAgentRequest.UpdateAgentRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ResourceUpdatedResponse`](../interfaces/api_types_ResourceUpdatedResponse.ResourceUpdatedResponse.md)\>

**`Example`**

```ts
await julepApi.updateAgent("string", {
        instructions: [{
                content: "string"
            }],
        defaultSettings: {
            temperature: 1,
            topP: 1
        }
    })
```

#### Defined in

[src/api/Client.d.ts:267](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L267)

___

### updateAgentTool

▸ **updateAgentTool**(`agentId`, `toolId`, `request`, `requestOptions?`): `Promise`\<[`ResourceUpdatedResponse`](../interfaces/api_types_ResourceUpdatedResponse.ResourceUpdatedResponse.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `toolId` | `string` |
| `request` | [`UpdateToolRequest`](../interfaces/api_client_requests_UpdateToolRequest.UpdateToolRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ResourceUpdatedResponse`](../interfaces/api_types_ResourceUpdatedResponse.ResourceUpdatedResponse.md)\>

**`Example`**

```ts
await julepApi.updateAgentTool("string", "string", {
        definition: {
            name: "string",
            parameters: {
                "string": "string"
            }
        }
    })
```

#### Defined in

[src/api/Client.d.ts:408](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L408)

___

### updateSession

▸ **updateSession**(`sessionId`, `request`, `requestOptions?`): `Promise`\<[`ResourceUpdatedResponse`](../interfaces/api_types_ResourceUpdatedResponse.ResourceUpdatedResponse.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `sessionId` | `string` |
| `request` | [`UpdateSessionRequest`](../interfaces/api_client_requests_UpdateSessionRequest.UpdateSessionRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ResourceUpdatedResponse`](../interfaces/api_types_ResourceUpdatedResponse.ResourceUpdatedResponse.md)\>

**`Example`**

```ts
await julepApi.updateSession("string", {
        situation: "string"
    })
```

#### Defined in

[src/api/Client.d.ts:130](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L130)

___

### updateUser

▸ **updateUser**(`userId`, `request?`, `requestOptions?`): `Promise`\<[`ResourceUpdatedResponse`](../interfaces/api_types_ResourceUpdatedResponse.ResourceUpdatedResponse.md)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `userId` | `string` |
| `request?` | [`UpdateUserRequest`](../interfaces/api_client_requests_UpdateUserRequest.UpdateUserRequest.md) |
| `requestOptions?` | [`RequestOptions`](../interfaces/Client.JulepApiClient.RequestOptions.md) |

#### Returns

`Promise`\<[`ResourceUpdatedResponse`](../interfaces/api_types_ResourceUpdatedResponse.ResourceUpdatedResponse.md)\>

**`Example`**

```ts
await julepApi.updateUser("string", {})
```

#### Defined in

[src/api/Client.d.ts:228](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/Client.d.ts#L228)
