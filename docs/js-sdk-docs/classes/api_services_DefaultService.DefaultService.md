[@julep/sdk](../README.md) / [Exports](../modules.md) / [api/services/DefaultService](../modules/api_services_DefaultService.md) / DefaultService

# Class: DefaultService

[api/services/DefaultService](../modules/api_services_DefaultService.md).DefaultService

## Table of contents

### Constructors

- [constructor](api_services_DefaultService.DefaultService.md#constructor)

### Properties

- [httpRequest](api_services_DefaultService.DefaultService.md#httprequest)

### Methods

- [chat](api_services_DefaultService.DefaultService.md#chat)
- [createAgent](api_services_DefaultService.DefaultService.md#createagent)
- [createAgentDoc](api_services_DefaultService.DefaultService.md#createagentdoc)
- [createAgentTool](api_services_DefaultService.DefaultService.md#createagenttool)
- [createSession](api_services_DefaultService.DefaultService.md#createsession)
- [createUser](api_services_DefaultService.DefaultService.md#createuser)
- [createUserDoc](api_services_DefaultService.DefaultService.md#createuserdoc)
- [deleteAgent](api_services_DefaultService.DefaultService.md#deleteagent)
- [deleteAgentDoc](api_services_DefaultService.DefaultService.md#deleteagentdoc)
- [deleteAgentMemory](api_services_DefaultService.DefaultService.md#deleteagentmemory)
- [deleteAgentTool](api_services_DefaultService.DefaultService.md#deleteagenttool)
- [deleteSession](api_services_DefaultService.DefaultService.md#deletesession)
- [deleteSessionHistory](api_services_DefaultService.DefaultService.md#deletesessionhistory)
- [deleteUser](api_services_DefaultService.DefaultService.md#deleteuser)
- [deleteUserDoc](api_services_DefaultService.DefaultService.md#deleteuserdoc)
- [getAgent](api_services_DefaultService.DefaultService.md#getagent)
- [getAgentDocs](api_services_DefaultService.DefaultService.md#getagentdocs)
- [getAgentMemories](api_services_DefaultService.DefaultService.md#getagentmemories)
- [getAgentTools](api_services_DefaultService.DefaultService.md#getagenttools)
- [getHistory](api_services_DefaultService.DefaultService.md#gethistory)
- [getJobStatus](api_services_DefaultService.DefaultService.md#getjobstatus)
- [getSession](api_services_DefaultService.DefaultService.md#getsession)
- [getSuggestions](api_services_DefaultService.DefaultService.md#getsuggestions)
- [getUser](api_services_DefaultService.DefaultService.md#getuser)
- [getUserDocs](api_services_DefaultService.DefaultService.md#getuserdocs)
- [listAgents](api_services_DefaultService.DefaultService.md#listagents)
- [listSessions](api_services_DefaultService.DefaultService.md#listsessions)
- [listUsers](api_services_DefaultService.DefaultService.md#listusers)
- [patchAgent](api_services_DefaultService.DefaultService.md#patchagent)
- [patchAgentTool](api_services_DefaultService.DefaultService.md#patchagenttool)
- [patchSession](api_services_DefaultService.DefaultService.md#patchsession)
- [patchUser](api_services_DefaultService.DefaultService.md#patchuser)
- [updateAgent](api_services_DefaultService.DefaultService.md#updateagent)
- [updateAgentTool](api_services_DefaultService.DefaultService.md#updateagenttool)
- [updateSession](api_services_DefaultService.DefaultService.md#updatesession)
- [updateUser](api_services_DefaultService.DefaultService.md#updateuser)

## Constructors

### constructor

• **new DefaultService**(`httpRequest`): [`DefaultService`](api_services_DefaultService.DefaultService.md)

#### Parameters

| Name | Type |
| :------ | :------ |
| `httpRequest` | [`BaseHttpRequest`](api_core_BaseHttpRequest.BaseHttpRequest.md) |

#### Returns

[`DefaultService`](api_services_DefaultService.DefaultService.md)

#### Defined in

[src/api/services/DefaultService.ts:35](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L35)

## Properties

### httpRequest

• `Readonly` **httpRequest**: [`BaseHttpRequest`](api_core_BaseHttpRequest.BaseHttpRequest.md)

#### Defined in

[src/api/services/DefaultService.ts:35](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L35)

## Methods

### chat

▸ **chat**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ChatResponse`](../modules/api_models_ChatResponse.md#chatresponse)\>

Interact with the session

#### Parameters

| Name | Type | Default value |
| :------ | :------ | :------ |
| `«destructured»` | `Object` | `undefined` |
| › `accept?` | ``"application/json"`` \| ``"text/event-stream"`` | `"application/json"` |
| › `requestBody?` | [`ChatInput`](../modules/api_models_ChatInput.md#chatinput) | `undefined` |
| › `sessionId` | `string` | `undefined` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ChatResponse`](../modules/api_models_ChatResponse.md#chatresponse)\>

ChatResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:404](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L404)

___

### createAgent

▸ **createAgent**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api_models_ResourceCreatedResponse.md#resourcecreatedresponse)\>

Create a new agent
Create a new agent

#### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `«destructured»` | `Object` | - |
| › `requestBody?` | [`CreateAgentRequest`](../modules/api_models_CreateAgentRequest.md#createagentrequest) | Agent create options |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api_models_ResourceCreatedResponse.md#resourcecreatedresponse)\>

ResourceCreatedResponse Agent successfully created

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:180](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L180)

___

### createAgentDoc

▸ **createAgentDoc**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api_models_ResourceCreatedResponse.md#resourcecreatedresponse)\>

Create doc of the agent

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `requestBody?` | [`CreateDoc`](../modules/api_models_CreateDoc.md#createdoc) |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api_models_ResourceCreatedResponse.md#resourcecreatedresponse)\>

ResourceCreatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:668](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L668)

___

### createAgentTool

▸ **createAgentTool**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api_models_ResourceCreatedResponse.md#resourcecreatedresponse)\>

Create tool for the agent

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `requestBody?` | [`CreateToolRequest`](../modules/api_models_CreateToolRequest.md#createtoolrequest) |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api_models_ResourceCreatedResponse.md#resourcecreatedresponse)\>

ResourceCreatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:857](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L857)

___

### createSession

▸ **createSession**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api_models_ResourceCreatedResponse.md#resourcecreatedresponse)\>

Create a new session
Create a session between an agent and a user

#### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `«destructured»` | `Object` | - |
| › `requestBody?` | [`CreateSessionRequest`](../modules/api_models_CreateSessionRequest.md#createsessionrequest) | Session initialization options |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api_models_ResourceCreatedResponse.md#resourcecreatedresponse)\>

ResourceCreatedResponse Session successfully created

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:42](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L42)

___

### createUser

▸ **createUser**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api_models_ResourceCreatedResponse.md#resourcecreatedresponse)\>

Create a new user
Create a new user

#### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `«destructured»` | `Object` | - |
| › `requestBody?` | [`CreateUserRequest`](../modules/api_models_CreateUserRequest.md#createuserrequest) | User create options |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api_models_ResourceCreatedResponse.md#resourcecreatedresponse)\>

ResourceCreatedResponse User successfully created

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:111](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L111)

___

### createUserDoc

▸ **createUserDoc**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api_models_ResourceCreatedResponse.md#resourcecreatedresponse)\>

Create doc of the user

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `requestBody?` | [`CreateDoc`](../modules/api_models_CreateDoc.md#createdoc) |
| › `userId` | `string` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceCreatedResponse`](../modules/api_models_ResourceCreatedResponse.md#resourcecreatedresponse)\>

ResourceCreatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:740](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L740)

___

### deleteAgent

▸ **deleteAgent**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api_models_ResourceDeletedResponse.md#resourcedeletedresponse)\>

Delete agent

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api_models_ResourceDeletedResponse.md#resourcedeletedresponse)\>

ResourceDeletedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:556](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L556)

___

### deleteAgentDoc

▸ **deleteAgentDoc**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api_models_ResourceDeletedResponse.md#resourcedeletedresponse)\>

Delete doc by id

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `docId` | `string` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api_models_ResourceDeletedResponse.md#resourcedeletedresponse)\>

ResourceDeletedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:783](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L783)

___

### deleteAgentMemory

▸ **deleteAgentMemory**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api_models_ResourceDeletedResponse.md#resourcedeletedresponse)\>

Delete memory of the agent by id

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `memoryId` | `string` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api_models_ResourceDeletedResponse.md#resourcedeletedresponse)\>

ResourceDeletedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:804](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L804)

___

### deleteAgentTool

▸ **deleteAgentTool**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api_models_ResourceDeletedResponse.md#resourcedeletedresponse)\>

Delete tool by id

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `toolId` | `string` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api_models_ResourceDeletedResponse.md#resourcedeletedresponse)\>

ResourceDeletedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:879](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L879)

___

### deleteSession

▸ **deleteSession**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api_models_ResourceDeletedResponse.md#resourcedeletedresponse)\>

Delete session

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `sessionId` | `string` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api_models_ResourceDeletedResponse.md#resourcedeletedresponse)\>

ResourceDeletedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:266](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L266)

___

### deleteSessionHistory

▸ **deleteSessionHistory**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api_models_ResourceDeletedResponse.md#resourcedeletedresponse)\>

Delete session history (does NOT delete related memories)

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `sessionId` | `string` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api_models_ResourceDeletedResponse.md#resourcedeletedresponse)\>

ResourceDeletedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:386](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L386)

___

### deleteUser

▸ **deleteUser**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api_models_ResourceDeletedResponse.md#resourcedeletedresponse)\>

Delete user

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `userId` | `string` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api_models_ResourceDeletedResponse.md#resourcedeletedresponse)\>

ResourceDeletedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:480](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L480)

___

### deleteUserDoc

▸ **deleteUserDoc**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api_models_ResourceDeletedResponse.md#resourcedeletedresponse)\>

Delete doc by id

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `docId` | `string` |
| › `userId` | `string` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceDeletedResponse`](../modules/api_models_ResourceDeletedResponse.md#resourcedeletedresponse)\>

ResourceDeletedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:762](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L762)

___

### getAgent

▸ **getAgent**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`Agent`](../modules/api_models_Agent.md#agent)\>

Get details of the agent

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`Agent`](../modules/api_models_Agent.md#agent)\>

Agent

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:542](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L542)

___

### getAgentDocs

▸ **getAgentDocs**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<\{ `items?`: [`Doc`](../modules/api_models_Doc.md#doc)[]  }\>

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

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<\{ `items?`: [`Doc`](../modules/api_models_Doc.md#doc)[]  }\>

any

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:619](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L619)

___

### getAgentMemories

▸ **getAgentMemories**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<\{ `items?`: [`Memory`](../modules/api_models_Memory.md#memory)[]  }\>

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

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<\{ `items?`: [`Memory`](../modules/api_models_Memory.md#memory)[]  }\>

any

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:432](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L432)

___

### getAgentTools

▸ **getAgentTools**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<\{ `items?`: [`Tool`](../modules/api_models_Tool.md#tool)[]  }\>

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

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<\{ `items?`: [`Tool`](../modules/api_models_Tool.md#tool)[]  }\>

any

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:826](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L826)

___

### getHistory

▸ **getHistory**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<\{ `items?`: [`ChatMLMessage`](../modules/api_models_ChatMLMessage.md#chatmlmessage)[]  }\>

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

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<\{ `items?`: [`ChatMLMessage`](../modules/api_models_ChatMLMessage.md#chatmlmessage)[]  }\>

any

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:358](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L358)

___

### getJobStatus

▸ **getJobStatus**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`JobStatus`](../modules/api_models_JobStatus.md#jobstatus)\>

Get status of the job

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `jobId` | `string` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`JobStatus`](../modules/api_models_JobStatus.md#jobstatus)\>

JobStatus

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:950](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L950)

___

### getSession

▸ **getSession**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`Session`](../modules/api_models_Session.md#session)\>

Get details of the session

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `sessionId` | `string` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`Session`](../modules/api_models_Session.md#session)\>

Session

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:248](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L248)

___

### getSuggestions

▸ **getSuggestions**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<\{ `items?`: [`Suggestion`](../modules/api_models_Suggestion.md#suggestion)[]  }\>

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

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<\{ `items?`: [`Suggestion`](../modules/api_models_Suggestion.md#suggestion)[]  }\>

any

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:329](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L329)

___

### getUser

▸ **getUser**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`User`](../modules/api_models_User.md#user)\>

Get details of the user

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `userId` | `string` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`User`](../modules/api_models_User.md#user)\>

User

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:466](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L466)

___

### getUserDocs

▸ **getUserDocs**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<\{ `items?`: [`Doc`](../modules/api_models_Doc.md#doc)[]  }\>

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

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<\{ `items?`: [`Doc`](../modules/api_models_Doc.md#doc)[]  }\>

any

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:691](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L691)

___

### listAgents

▸ **listAgents**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<\{ `items`: [`Agent`](../modules/api_models_Agent.md#agent)[]  }\>

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

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<\{ `items`: [`Agent`](../modules/api_models_Agent.md#agent)[]  }\>

any List of agents (sorted created_at descending order) with limit+offset pagination

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:201](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L201)

___

### listSessions

▸ **listSessions**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<\{ `items`: [`Session`](../modules/api_models_Session.md#session)[]  }\>

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

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<\{ `items`: [`Session`](../modules/api_models_Session.md#session)[]  }\>

any List of sessions (sorted created_at descending order) with limit+offset pagination

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:63](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L63)

___

### listUsers

▸ **listUsers**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<\{ `items`: [`User`](../modules/api_models_User.md#user)[]  }\>

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

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<\{ `items`: [`User`](../modules/api_models_User.md#user)[]  }\>

any List of users (sorted created_at descending order) with limit+offset pagination

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:132](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L132)

___

### patchAgent

▸ **patchAgent**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api_models_ResourceUpdatedResponse.md#resourceupdatedresponse)\>

Patch Agent parameters (merge instead of replace)

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `requestBody?` | [`PatchAgentRequest`](../modules/api_models_PatchAgentRequest.md#patchagentrequest) |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api_models_ResourceUpdatedResponse.md#resourceupdatedresponse)\>

ResourceUpdatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:596](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L596)

___

### patchAgentTool

▸ **patchAgentTool**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api_models_ResourceUpdatedResponse.md#resourceupdatedresponse)\>

Patch Agent tool parameters (merge instead of replace)

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `requestBody?` | [`PatchToolRequest`](../modules/api_models_PatchToolRequest.md#patchtoolrequest) |
| › `toolId` | `string` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api_models_ResourceUpdatedResponse.md#resourceupdatedresponse)\>

ResourceUpdatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:925](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L925)

___

### patchSession

▸ **patchSession**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api_models_ResourceUpdatedResponse.md#resourceupdatedresponse)\>

Patch Session parameters (merge instead of replace)

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `requestBody?` | [`PatchSessionRequest`](../modules/api_models_PatchSessionRequest.md#patchsessionrequest) |
| › `sessionId` | `string` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api_models_ResourceUpdatedResponse.md#resourceupdatedresponse)\>

ResourceUpdatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:306](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L306)

___

### patchUser

▸ **patchUser**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api_models_ResourceUpdatedResponse.md#resourceupdatedresponse)\>

Patch User parameters (merge instead of replace)

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `requestBody?` | [`PatchUserRequest`](../modules/api_models_PatchUserRequest.md#patchuserrequest) |
| › `userId` | `string` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api_models_ResourceUpdatedResponse.md#resourceupdatedresponse)\>

ResourceUpdatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:520](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L520)

___

### updateAgent

▸ **updateAgent**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api_models_ResourceUpdatedResponse.md#resourceupdatedresponse)\>

Update agent parameters

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `requestBody?` | [`UpdateAgentRequest`](../modules/api_models_UpdateAgentRequest.md#updateagentrequest) |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api_models_ResourceUpdatedResponse.md#resourceupdatedresponse)\>

ResourceUpdatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:574](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L574)

___

### updateAgentTool

▸ **updateAgentTool**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api_models_ResourceUpdatedResponse.md#resourceupdatedresponse)\>

Update agent tool definition

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `requestBody?` | [`UpdateToolRequest`](../modules/api_models_UpdateToolRequest.md#updatetoolrequest) |
| › `toolId` | `string` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api_models_ResourceUpdatedResponse.md#resourceupdatedresponse)\>

ResourceUpdatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:900](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L900)

___

### updateSession

▸ **updateSession**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api_models_ResourceUpdatedResponse.md#resourceupdatedresponse)\>

Update session parameters

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `requestBody?` | [`UpdateSessionRequest`](../modules/api_models_UpdateSessionRequest.md#updatesessionrequest) |
| › `sessionId` | `string` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api_models_ResourceUpdatedResponse.md#resourceupdatedresponse)\>

ResourceUpdatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:284](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L284)

___

### updateUser

▸ **updateUser**(`«destructured»`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api_models_ResourceUpdatedResponse.md#resourceupdatedresponse)\>

Update user parameters

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `requestBody?` | [`UpdateUserRequest`](../modules/api_models_UpdateUserRequest.md#updateuserrequest) |
| › `userId` | `string` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<[`ResourceUpdatedResponse`](../modules/api_models_ResourceUpdatedResponse.md#resourceupdatedresponse)\>

ResourceUpdatedResponse

**`Throws`**

ApiError

#### Defined in

[src/api/services/DefaultService.ts:498](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/services/DefaultService.ts#L498)
