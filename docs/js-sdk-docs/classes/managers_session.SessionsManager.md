[@julep/sdk](../README.md) / [Modules](../modules.md) / [managers/session](../modules/managers_session.md) / SessionsManager

# Class: SessionsManager

[managers/session](../modules/managers_session.md).SessionsManager

BaseManager serves as the base class for all manager classes that interact with the Julep API.
It provides common functionality needed for API interactions.

## Hierarchy

- [`BaseManager`](managers_base.BaseManager.md)

  ↳ **`SessionsManager`**

## Table of contents

### Constructors

- [constructor](managers_session.SessionsManager.md#constructor)

### Properties

- [apiClient](managers_session.SessionsManager.md#apiclient)

### Methods

- [chat](managers_session.SessionsManager.md#chat)
- [create](managers_session.SessionsManager.md#create)
- [delete](managers_session.SessionsManager.md#delete)
- [deleteHistory](managers_session.SessionsManager.md#deletehistory)
- [get](managers_session.SessionsManager.md#get)
- [history](managers_session.SessionsManager.md#history)
- [list](managers_session.SessionsManager.md#list)
- [suggestions](managers_session.SessionsManager.md#suggestions)
- [update](managers_session.SessionsManager.md#update)

## Constructors

### constructor

• **new SessionsManager**(`apiClient`): [`SessionsManager`](managers_session.SessionsManager.md)

Constructs a new instance of BaseManager.

#### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `apiClient` | [`JulepApiClient`](api_JulepApiClient.JulepApiClient.md) | The JulepApiClient instance used for API interactions. |

#### Returns

[`SessionsManager`](managers_session.SessionsManager.md)

#### Inherited from

[BaseManager](managers_base.BaseManager.md).[constructor](managers_base.BaseManager.md#constructor)

#### Defined in

[src/managers/base.ts:12](https://github.com/julep-ai/julep/blob/137fc3344978acb0061f00ed2f60bb7671aff682/sdks/ts/src/managers/base.ts#L12)

## Properties

### apiClient

• **apiClient**: [`JulepApiClient`](api_JulepApiClient.JulepApiClient.md)

The JulepApiClient instance used for API interactions.

#### Inherited from

[BaseManager](managers_base.BaseManager.md).[apiClient](managers_base.BaseManager.md#apiclient)

#### Defined in

[src/managers/base.ts:12](https://github.com/julep-ai/julep/blob/137fc3344978acb0061f00ed2f60bb7671aff682/sdks/ts/src/managers/base.ts#L12)

## Methods

### chat

▸ **chat**(`sessionId`, `«destructured»`): `Promise`\<[`ChatResponse`](../modules/api.md#chatresponse)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `sessionId` | `string` |
| `«destructured»` | [`ChatInput`](../modules/api.md#chatinput) |

#### Returns

`Promise`\<[`ChatResponse`](../modules/api.md#chatresponse)\>

#### Defined in

[src/managers/session.ts:110](https://github.com/julep-ai/julep/blob/137fc3344978acb0061f00ed2f60bb7671aff682/sdks/ts/src/managers/session.ts#L110)

___

### create

▸ **create**(`«destructured»`): `Promise`\<[`ResourceCreatedResponse`](../modules/api.md#resourcecreatedresponse)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | [`CreateSessionPayload`](../interfaces/managers_session.CreateSessionPayload.md) |

#### Returns

`Promise`\<[`ResourceCreatedResponse`](../modules/api.md#resourcecreatedresponse)\>

#### Defined in

[src/managers/session.ts:35](https://github.com/julep-ai/julep/blob/137fc3344978acb0061f00ed2f60bb7671aff682/sdks/ts/src/managers/session.ts#L35)

___

### delete

▸ **delete**(`sessionId`): `Promise`\<`void`\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `sessionId` | `string` |

#### Returns

`Promise`\<`void`\>

#### Defined in

[src/managers/session.ts:81](https://github.com/julep-ai/julep/blob/137fc3344978acb0061f00ed2f60bb7671aff682/sdks/ts/src/managers/session.ts#L81)

___

### deleteHistory

▸ **deleteHistory**(`sessionId`): `Promise`\<`void`\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `sessionId` | `string` |

#### Returns

`Promise`\<`void`\>

#### Defined in

[src/managers/session.ts:206](https://github.com/julep-ai/julep/blob/137fc3344978acb0061f00ed2f60bb7671aff682/sdks/ts/src/managers/session.ts#L206)

___

### get

▸ **get**(`sessionId`): `Promise`\<[`Session`](../modules/api.md#session)\>

Retrieves a session by its ID.

#### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `sessionId` | `string` | The unique identifier of the session. |

#### Returns

`Promise`\<[`Session`](../modules/api.md#session)\>

A promise that resolves with the session object.

#### Defined in

[src/managers/session.ts:27](https://github.com/julep-ai/julep/blob/137fc3344978acb0061f00ed2f60bb7671aff682/sdks/ts/src/managers/session.ts#L27)

___

### history

▸ **history**(`sessionId`, `«destructured»?`): `Promise`\<[`ChatMLMessage`](../modules/api.md#chatmlmessage)[]\>

#### Parameters

| Name | Type | Default value |
| :------ | :------ | :------ |
| `sessionId` | `string` | `undefined` |
| `«destructured»` | `Object` | `{}` |
| › `limit?` | `number` | `100` |
| › `offset?` | `number` | `0` |

#### Returns

`Promise`\<[`ChatMLMessage`](../modules/api.md#chatmlmessage)[]\>

#### Defined in

[src/managers/session.ts:187](https://github.com/julep-ai/julep/blob/137fc3344978acb0061f00ed2f60bb7671aff682/sdks/ts/src/managers/session.ts#L187)

___

### list

▸ **list**(`«destructured»?`): `Promise`\<[`Session`](../modules/api.md#session)[]\>

#### Parameters

| Name | Type | Default value |
| :------ | :------ | :------ |
| `«destructured»` | `Object` | `{}` |
| › `limit?` | `number` | `100` |
| › `metadataFilter?` | `Object` | `{}` |
| › `offset?` | `number` | `0` |

#### Returns

`Promise`\<[`Session`](../modules/api.md#session)[]\>

#### Defined in

[src/managers/session.ts:61](https://github.com/julep-ai/julep/blob/137fc3344978acb0061f00ed2f60bb7671aff682/sdks/ts/src/managers/session.ts#L61)

___

### suggestions

▸ **suggestions**(`sessionId`, `«destructured»?`): `Promise`\<[`Suggestion`](../modules/api.md#suggestion)[]\>

#### Parameters

| Name | Type | Default value |
| :------ | :------ | :------ |
| `sessionId` | `string` | `undefined` |
| `«destructured»` | `Object` | `{}` |
| › `limit?` | `number` | `100` |
| › `offset?` | `number` | `0` |

#### Returns

`Promise`\<[`Suggestion`](../modules/api.md#suggestion)[]\>

#### Defined in

[src/managers/session.ts:168](https://github.com/julep-ai/julep/blob/137fc3344978acb0061f00ed2f60bb7671aff682/sdks/ts/src/managers/session.ts#L168)

___

### update

▸ **update**(`sessionId`, `«destructured»`, `overwrite?`): `Promise`\<[`ResourceUpdatedResponse`](../modules/api.md#resourceupdatedresponse)\>

#### Parameters

| Name | Type | Default value |
| :------ | :------ | :------ |
| `sessionId` | `string` | `undefined` |
| `«destructured»` | `Object` | `undefined` |
| › `metadata?` | `any` | `{}` |
| › `situation` | `string` | `undefined` |
| `overwrite` | `boolean` | `false` |

#### Returns

`Promise`\<[`ResourceUpdatedResponse`](../modules/api.md#resourceupdatedresponse)\>

#### Defined in

[src/managers/session.ts:91](https://github.com/julep-ai/julep/blob/137fc3344978acb0061f00ed2f60bb7671aff682/sdks/ts/src/managers/session.ts#L91)
