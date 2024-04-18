[@julep/sdk](../README.md) / [Modules](../modules.md) / [api](../modules/api.md) / DefaultService

# Class: DefaultService

[api](../modules/api.md).DefaultService

## Table of contents

### Constructors

- [constructor](api.DefaultService.md#constructor)

### Properties

- [httpRequest](api.DefaultService.md#httprequest)

### Methods

- [chat](api.DefaultService.md#chat)
- [createAgent](api.DefaultService.md#createagent)
- [createAgentDoc](api.DefaultService.md#createagentdoc)
- [createAgentTool](api.DefaultService.md#createagenttool)
- [createSession](api.DefaultService.md#createsession)
- [createUser](api.DefaultService.md#createuser)
- [createUserDoc](api.DefaultService.md#createuserdoc)
- [deleteAgent](api.DefaultService.md#deleteagent)
- [deleteAgentDoc](api.DefaultService.md#deleteagentdoc)
- [deleteAgentMemory](api.DefaultService.md#deleteagentmemory)
- [deleteAgentTool](api.DefaultService.md#deleteagenttool)
- [deleteSession](api.DefaultService.md#deletesession)
- [deleteSessionHistory](api.DefaultService.md#deletesessionhistory)
- [deleteUser](api.DefaultService.md#deleteuser)
- [deleteUserDoc](api.DefaultService.md#deleteuserdoc)
- [getAgent](api.DefaultService.md#getagent)
- [getAgentDocs](api.DefaultService.md#getagentdocs)
- [getAgentMemories](api.DefaultService.md#getagentmemories)
- [getAgentTools](api.DefaultService.md#getagenttools)
- [getHistory](api.DefaultService.md#gethistory)
- [getJobStatus](api.DefaultService.md#getjobstatus)
- [getSession](api.DefaultService.md#getsession)
- [getSuggestions](api.DefaultService.md#getsuggestions)
- [getUser](api.DefaultService.md#getuser)
- [getUserDocs](api.DefaultService.md#getuserdocs)
- [listAgents](api.DefaultService.md#listagents)
- [listSessions](api.DefaultService.md#listsessions)
- [listUsers](api.DefaultService.md#listusers)
- [patchAgent](api.DefaultService.md#patchagent)
- [patchAgentTool](api.DefaultService.md#patchagenttool)
- [patchSession](api.DefaultService.md#patchsession)
- [patchUser](api.DefaultService.md#patchuser)
- [updateAgent](api.DefaultService.md#updateagent)
- [updateAgentTool](api.DefaultService.md#updateagenttool)
- [updateSession](api.DefaultService.md#updatesession)
- [updateUser](api.DefaultService.md#updateuser)

## Constructors

### constructor

• **new DefaultService**(`httpRequest`): [`DefaultService`](api.DefaultService.md)

#### Parameters

| Name | Type |
| :------ | :------ |
| `httpRequest` | [`BaseHttpRequest`](api.BaseHttpRequest.md) |

#### Returns

[`DefaultService`](api.DefaultService.md)

#### Defined in

[src/api/services/DefaultService.ts:35](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L35)

## Properties

### httpRequest

• `Readonly` **httpRequest**: [`BaseHttpRequest`](api.BaseHttpRequest.md)

#### Defined in

[src/api/services/DefaultService.ts:35](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L35)

## Methods

### chat

▸ **chat**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ChatResponse`](../modules/api.md#chatresponse)\>

Interact with the session

#### Parameters

| Name | Type | Default value |
| :------ | :------ | :------ |
| `«destructured»` | `Object` | `undefined` |
| › `accept?` | ``"application/json"`` \| ``"text/event-stream"`` | `"application/json"` |
| › `requestBody?` | [`ChatInput`](../modules/api.md#chatinput) | `undefined` |
| › `sessionId` | `string` | `undefined` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ChatResponse`](../modules/api.md#chatresponse)\>

ChatResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:404](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L404)

___

### createAgent

▸ **createAgent**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api.md#resourcecreatedresponse)\>

Create a new agent
Create a new agent

#### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `«destructured»` | `Object` | - |
| › `requestBody?` | [`CreateAgentRequest`](../modules/api.md#createagentrequest) | Agent create options |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api.md#resourcecreatedresponse)\>

ResourceCreatedResponse Agent successfully created

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:180](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L180)

___

### createAgentDoc

▸ **createAgentDoc**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api.md#resourcecreatedresponse)\>

Create doc of the agent

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `requestBody?` | [`CreateDoc`](../modules/api.md#createdoc) |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api.md#resourcecreatedresponse)\>

ResourceCreatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:668](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L668)

___

### createAgentTool

▸ **createAgentTool**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api.md#resourcecreatedresponse)\>

Create tool for the agent

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `requestBody?` | [`CreateToolRequest`](../modules/api.md#createtoolrequest) |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api.md#resourcecreatedresponse)\>

ResourceCreatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:857](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L857)

___

### createSession

▸ **createSession**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api.md#resourcecreatedresponse)\>

Create a new session
Create a session between an agent and a user

#### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `«destructured»` | `Object` | - |
| › `requestBody?` | [`CreateSessionRequest`](../modules/api.md#createsessionrequest) | Session initialization options |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api.md#resourcecreatedresponse)\>

ResourceCreatedResponse Session successfully created

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:42](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L42)

___

### createUser

▸ **createUser**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api.md#resourcecreatedresponse)\>

Create a new user
Create a new user

#### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `«destructured»` | `Object` | - |
| › `requestBody?` | [`CreateUserRequest`](../modules/api.md#createuserrequest) | User create options |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api.md#resourcecreatedresponse)\>

ResourceCreatedResponse User successfully created

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:111](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L111)

___

### createUserDoc

▸ **createUserDoc**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api.md#resourcecreatedresponse)\>

Create doc of the user

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `requestBody?` | [`CreateDoc`](../modules/api.md#createdoc) |
| › `userId` | `string` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api.md#resourcecreatedresponse)\>

ResourceCreatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:740](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L740)

___

### deleteAgent

▸ **deleteAgent**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api.md#resourcedeletedresponse)\>

Delete agent

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api.md#resourcedeletedresponse)\>

ResourceDeletedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:556](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L556)

___

### deleteAgentDoc

▸ **deleteAgentDoc**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api.md#resourcedeletedresponse)\>

Delete doc by id

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `docId` | `string` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api.md#resourcedeletedresponse)\>

ResourceDeletedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:783](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L783)

___

### deleteAgentMemory

▸ **deleteAgentMemory**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api.md#resourcedeletedresponse)\>

Delete memory of the agent by id

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `memoryId` | `string` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api.md#resourcedeletedresponse)\>

ResourceDeletedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:804](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L804)

___

### deleteAgentTool

▸ **deleteAgentTool**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api.md#resourcedeletedresponse)\>

Delete tool by id

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `toolId` | `string` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api.md#resourcedeletedresponse)\>

ResourceDeletedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:879](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L879)

___

### deleteSession

▸ **deleteSession**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api.md#resourcedeletedresponse)\>

Delete session

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `sessionId` | `string` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api.md#resourcedeletedresponse)\>

ResourceDeletedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:266](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L266)

___

### deleteSessionHistory

▸ **deleteSessionHistory**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api.md#resourcedeletedresponse)\>

Delete session history (does NOT delete related memories)

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `sessionId` | `string` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api.md#resourcedeletedresponse)\>

ResourceDeletedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:386](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L386)

___

### deleteUser

▸ **deleteUser**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api.md#resourcedeletedresponse)\>

Delete user

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `userId` | `string` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api.md#resourcedeletedresponse)\>

ResourceDeletedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:480](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L480)

___

### deleteUserDoc

▸ **deleteUserDoc**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api.md#resourcedeletedresponse)\>

Delete doc by id

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `docId` | `string` |
| › `userId` | `string` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api.md#resourcedeletedresponse)\>

ResourceDeletedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:762](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L762)

___

### getAgent

▸ **getAgent**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`Agent`](../modules/api.md#agent)\>

Get details of the agent

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`Agent`](../modules/api.md#agent)\>

Agent

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:542](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L542)

___

### getAgentDocs

▸ **getAgentDocs**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<\{ `items?`: [`Doc`](../modules/api.md#doc)[]  }\>

Get docs of the agent
Sorted (created_at descending)

#### Parameters

| Name | Type | Default value | Description |
| :------ | :------ | :------ | :------ |
| `«destructured»` | `Object` | `undefined` | - |
| › `agentId` | `string` | `undefined` | - |
| › `limit?` | `number` | `undefined` | - |
| › `metadataFilter?` | `string` | `"{}"` | JSON object that should be used to filter objects by metadata |
| › `offset?` | `number` | `undefined` | - |
| › `order?` | ``"desc"`` \| ``"asc"`` | `"desc"` | Which order should the sort be: `asc` (ascending) or `desc` (descending) |
| › `requestBody?` | `any` | `undefined` | - |
| › `sortBy?` | ``"created_at"`` \| ``"updated_at"`` | `"created_at"` | Which field to sort by: `created_at` or `updated_at` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<\{ `items?`: [`Doc`](../modules/api.md#doc)[]  }\>

any

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:619](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L619)

___

### getAgentMemories

▸ **getAgentMemories**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<\{ `items?`: [`Memory`](../modules/api.md#memory)[]  }\>

Get memories of the agent
Sorted (created_at descending)

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `limit?` | `number` |
| › `offset?` | `number` |
| › `query` | `string` |
| › `userId?` | `string` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<\{ `items?`: [`Memory`](../modules/api.md#memory)[]  }\>

any

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:432](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L432)

___

### getAgentTools

▸ **getAgentTools**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<\{ `items?`: [`Tool`](../modules/api.md#tool)[]  }\>

Get tools of the agent
Sorted (created_at descending)

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `limit?` | `number` |
| › `offset?` | `number` |
| › `requestBody?` | `any` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<\{ `items?`: [`Tool`](../modules/api.md#tool)[]  }\>

any

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:826](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L826)

___

### getHistory

▸ **getHistory**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<\{ `items?`: [`ChatMLMessage`](../modules/api.md#chatmlmessage)[]  }\>

Get all messages in a session
Sorted (created_at ascending)

#### Parameters

| Name | Type | Default value |
| :------ | :------ | :------ |
| `«destructured»` | `Object` | `undefined` |
| › `limit?` | `number` | `100` |
| › `offset?` | `number` | `undefined` |
| › `sessionId` | `string` | `undefined` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<\{ `items?`: [`ChatMLMessage`](../modules/api.md#chatmlmessage)[]  }\>

any

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:358](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L358)

___

### getJobStatus

▸ **getJobStatus**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`JobStatus`](../modules/api.md#jobstatus)\>

Get status of the job

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `jobId` | `string` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`JobStatus`](../modules/api.md#jobstatus)\>

JobStatus

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:950](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L950)

___

### getSession

▸ **getSession**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`Session`](../modules/api.md#session)\>

Get details of the session

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `sessionId` | `string` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`Session`](../modules/api.md#session)\>

Session

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:248](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L248)

___

### getSuggestions

▸ **getSuggestions**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<\{ `items?`: [`Suggestion`](../modules/api.md#suggestion)[]  }\>

Get autogenerated suggestions for session user and agent
Sorted (created_at descending)

#### Parameters

| Name | Type | Default value |
| :------ | :------ | :------ |
| `«destructured»` | `Object` | `undefined` |
| › `limit?` | `number` | `100` |
| › `offset?` | `number` | `undefined` |
| › `sessionId` | `string` | `undefined` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<\{ `items?`: [`Suggestion`](../modules/api.md#suggestion)[]  }\>

any

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:329](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L329)

___

### getUser

▸ **getUser**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`User`](../modules/api.md#user)\>

Get details of the user

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `userId` | `string` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`User`](../modules/api.md#user)\>

User

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:466](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L466)

___

### getUserDocs

▸ **getUserDocs**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<\{ `items?`: [`Doc`](../modules/api.md#doc)[]  }\>

Get docs of the user
Sorted (created_at descending)

#### Parameters

| Name | Type | Default value | Description |
| :------ | :------ | :------ | :------ |
| `«destructured»` | `Object` | `undefined` | - |
| › `limit?` | `number` | `undefined` | - |
| › `metadataFilter?` | `string` | `"{}"` | JSON object that should be used to filter objects by metadata |
| › `offset?` | `number` | `undefined` | - |
| › `order?` | ``"desc"`` \| ``"asc"`` | `"desc"` | Which order should the sort be: `asc` (ascending) or `desc` (descending) |
| › `requestBody?` | `any` | `undefined` | - |
| › `sortBy?` | ``"created_at"`` \| ``"updated_at"`` | `"created_at"` | Which field to sort by: `created_at` or `updated_at` |
| › `userId` | `string` | `undefined` | - |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<\{ `items?`: [`Doc`](../modules/api.md#doc)[]  }\>

any

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:691](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L691)

___

### listAgents

▸ **listAgents**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<\{ `items`: [`Agent`](../modules/api.md#agent)[]  }\>

List agents
List agents created (use limit/offset pagination to get large number of sessions; sorted by descending order of `created_at` by default)

#### Parameters

| Name | Type | Default value | Description |
| :------ | :------ | :------ | :------ |
| `«destructured»` | `Object` | `undefined` | - |
| › `limit?` | `number` | `100` | Number of items to return |
| › `metadataFilter?` | `string` | `"{}"` | JSON object that should be used to filter objects by metadata |
| › `offset?` | `number` | `undefined` | Number of items to skip (sorted created_at descending order) |
| › `order?` | ``"desc"`` \| ``"asc"`` | `"desc"` | Which order should the sort be: `asc` (ascending) or `desc` (descending) |
| › `sortBy?` | ``"created_at"`` \| ``"updated_at"`` | `"created_at"` | Which field to sort by: `created_at` or `updated_at` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<\{ `items`: [`Agent`](../modules/api.md#agent)[]  }\>

any List of agents (sorted created_at descending order) with limit+offset pagination

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:201](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L201)

___

### listSessions

▸ **listSessions**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<\{ `items`: [`Session`](../modules/api.md#session)[]  }\>

List sessions
List sessions created (use limit/offset pagination to get large number of sessions; sorted by descending order of `created_at` by default)

#### Parameters

| Name | Type | Default value | Description |
| :------ | :------ | :------ | :------ |
| `«destructured»` | `Object` | `undefined` | - |
| › `limit?` | `number` | `100` | Number of sessions to return |
| › `metadataFilter?` | `string` | `"{}"` | JSON object that should be used to filter objects by metadata |
| › `offset?` | `number` | `undefined` | Number of sessions to skip (sorted created_at descending order) |
| › `order?` | ``"desc"`` \| ``"asc"`` | `"desc"` | Which order should the sort be: `asc` (ascending) or `desc` (descending) |
| › `sortBy?` | ``"created_at"`` \| ``"updated_at"`` | `"created_at"` | Which field to sort by: `created_at` or `updated_at` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<\{ `items`: [`Session`](../modules/api.md#session)[]  }\>

any List of sessions (sorted created_at descending order) with limit+offset pagination

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:63](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L63)

___

### listUsers

▸ **listUsers**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<\{ `items`: [`User`](../modules/api.md#user)[]  }\>

List users
List users created (use limit/offset pagination to get large number of sessions; sorted by descending order of `created_at` by default)

#### Parameters

| Name | Type | Default value | Description |
| :------ | :------ | :------ | :------ |
| `«destructured»` | `Object` | `undefined` | - |
| › `limit?` | `number` | `100` | Number of items to return |
| › `metadataFilter?` | `string` | `"{}"` | JSON object that should be used to filter objects by metadata |
| › `offset?` | `number` | `undefined` | Number of items to skip (sorted created_at descending order) |
| › `order?` | ``"desc"`` \| ``"asc"`` | `"desc"` | Which order should the sort be: `asc` (ascending) or `desc` (descending) |
| › `sortBy?` | ``"created_at"`` \| ``"updated_at"`` | `"created_at"` | Which field to sort by: `created_at` or `updated_at` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<\{ `items`: [`User`](../modules/api.md#user)[]  }\>

any List of users (sorted created_at descending order) with limit+offset pagination

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:132](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L132)

___

### patchAgent

▸ **patchAgent**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api.md#resourceupdatedresponse)\>

Patch Agent parameters (merge instead of replace)

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `requestBody?` | [`PatchAgentRequest`](../modules/api.md#patchagentrequest) |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api.md#resourceupdatedresponse)\>

ResourceUpdatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:596](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L596)

___

### patchAgentTool

▸ **patchAgentTool**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api.md#resourceupdatedresponse)\>

Patch Agent tool parameters (merge instead of replace)

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `requestBody?` | [`PatchToolRequest`](../modules/api.md#patchtoolrequest) |
| › `toolId` | `string` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api.md#resourceupdatedresponse)\>

ResourceUpdatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:925](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L925)

___

### patchSession

▸ **patchSession**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api.md#resourceupdatedresponse)\>

Patch Session parameters (merge instead of replace)

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `requestBody?` | [`PatchSessionRequest`](../modules/api.md#patchsessionrequest) |
| › `sessionId` | `string` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api.md#resourceupdatedresponse)\>

ResourceUpdatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:306](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L306)

___

### patchUser

▸ **patchUser**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api.md#resourceupdatedresponse)\>

Patch User parameters (merge instead of replace)

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `requestBody?` | [`PatchUserRequest`](../modules/api.md#patchuserrequest) |
| › `userId` | `string` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api.md#resourceupdatedresponse)\>

ResourceUpdatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:520](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L520)

___

### updateAgent

▸ **updateAgent**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api.md#resourceupdatedresponse)\>

Update agent parameters

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `requestBody?` | [`UpdateAgentRequest`](../modules/api.md#updateagentrequest) |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api.md#resourceupdatedresponse)\>

ResourceUpdatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:574](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L574)

___

### updateAgentTool

▸ **updateAgentTool**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api.md#resourceupdatedresponse)\>

Update agent tool definition

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `requestBody?` | [`UpdateToolRequest`](../modules/api.md#updatetoolrequest) |
| › `toolId` | `string` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api.md#resourceupdatedresponse)\>

ResourceUpdatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:900](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L900)

___

### updateSession

▸ **updateSession**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api.md#resourceupdatedresponse)\>

Update session parameters

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `requestBody?` | [`UpdateSessionRequest`](../modules/api.md#updatesessionrequest) |
| › `sessionId` | `string` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api.md#resourceupdatedresponse)\>

ResourceUpdatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:284](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L284)

___

### updateUser

▸ **updateUser**(`«destructured»`): [`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api.md#resourceupdatedresponse)\>

Update user parameters

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `requestBody?` | [`UpdateUserRequest`](../modules/api.md#updateuserrequest) |
| › `userId` | `string` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api.md#resourceupdatedresponse)\>

ResourceUpdatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:498](https://github.com/julep-ai/julep/blob/ecc614a1c46580fb9f57417432058d58202ec6b9/sdks/ts/src/api/services/DefaultService.ts#L498)
