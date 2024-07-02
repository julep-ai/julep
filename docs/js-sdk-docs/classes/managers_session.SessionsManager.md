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

[src/managers/base.ts:14](https://github.com/julep-ai/julep/blob/dd1994163c03c7bb7077bec610f7ab1fb374dfec/sdks/ts/src/managers/base.ts#L14)

## Properties

### apiClient

• **apiClient**: [`JulepApiClient`](api_JulepApiClient.JulepApiClient.md)

The JulepApiClient instance used for API interactions.

#### Inherited from

[BaseManager](managers_base.BaseManager.md).[apiClient](managers_base.BaseManager.md#apiclient)

#### Defined in

[src/managers/base.ts:14](https://github.com/julep-ai/julep/blob/dd1994163c03c7bb7077bec610f7ab1fb374dfec/sdks/ts/src/managers/base.ts#L14)

## Methods

### chat

▸ **chat**(`sessionId`, `input`): `Promise`\<[`ChatResponse`](../modules/api.md#chatresponse)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `sessionId` | `string` & `Format`\<``"uuid"``\> |
| `input` | [`ChatInput`](../modules/api.md#chatinput) |

#### Returns

`Promise`\<[`ChatResponse`](../modules/api.md#chatresponse)\>

#### Defined in

[src/managers/session.ts:161](https://github.com/julep-ai/julep/blob/dd1994163c03c7bb7077bec610f7ab1fb374dfec/sdks/ts/src/managers/session.ts#L161)

___

### create

▸ **create**(`payload`): `Promise`\<[`ResourceCreatedResponse`](../modules/api.md#resourcecreatedresponse)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `payload` | [`CreateSessionPayload`](../interfaces/managers_session.CreateSessionPayload.md) |

#### Returns

`Promise`\<[`ResourceCreatedResponse`](../modules/api.md#resourcecreatedresponse)\>

#### Defined in

[src/managers/session.ts:39](https://github.com/julep-ai/julep/blob/dd1994163c03c7bb7077bec610f7ab1fb374dfec/sdks/ts/src/managers/session.ts#L39)

___

### delete

▸ **delete**(`sessionId`): `Promise`\<`void`\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `sessionId` | `string` & `Format`\<``"uuid"``\> |

#### Returns

`Promise`\<`void`\>

#### Defined in

[src/managers/session.ts:109](https://github.com/julep-ai/julep/blob/dd1994163c03c7bb7077bec610f7ab1fb374dfec/sdks/ts/src/managers/session.ts#L109)

___

### deleteHistory

▸ **deleteHistory**(`sessionId`): `Promise`\<`void`\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `sessionId` | `string` & `Format`\<``"uuid"``\> |

#### Returns

`Promise`\<`void`\>

#### Defined in

[src/managers/session.ts:263](https://github.com/julep-ai/julep/blob/dd1994163c03c7bb7077bec610f7ab1fb374dfec/sdks/ts/src/managers/session.ts#L263)

___

### get

▸ **get**(`sessionId`): `Promise`\<[`Session`](../modules/api.md#session)\>

Retrieves a session by its ID.

#### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `sessionId` | `string` & `Format`\<``"uuid"``\> | The unique identifier of the session. |

#### Returns

`Promise`\<[`Session`](../modules/api.md#session)\>

A promise that resolves with the session object.

#### Defined in

[src/managers/session.ts:33](https://github.com/julep-ai/julep/blob/dd1994163c03c7bb7077bec610f7ab1fb374dfec/sdks/ts/src/managers/session.ts#L33)

___

### history

▸ **history**(`sessionId`, `options?`): `Promise`\<[`ChatMLMessage`](../modules/api.md#chatmlmessage)[]\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `sessionId` | `string` & `Format`\<``"uuid"``\> |
| `options` | `Object` |
| `options.limit?` | `number` & `Minimum`\<``1``\> & `Maximum`\<``1000``\> |
| `options.offset?` | `number` & `Minimum`\<``0``\> |

#### Returns

`Promise`\<[`ChatMLMessage`](../modules/api.md#chatmlmessage)[]\>

#### Defined in

[src/managers/session.ts:240](https://github.com/julep-ai/julep/blob/dd1994163c03c7bb7077bec610f7ab1fb374dfec/sdks/ts/src/managers/session.ts#L240)

___

### list

▸ **list**(`options?`): `Promise`\<[`Session`](../modules/api.md#session)[]\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `options` | `Object` |
| `options.limit?` | `number` & `Type`\<``"uint32"``\> & `Minimum`\<``1``\> & `Maximum`\<``1000``\> |
| `options.metadataFilter?` | `Object` |
| `options.offset?` | `number` & `Minimum`\<``1``\> & `Maximum`\<``1000``\> |

#### Returns

`Promise`\<[`Session`](../modules/api.md#session)[]\>

#### Defined in

[src/managers/session.ts:75](https://github.com/julep-ai/julep/blob/dd1994163c03c7bb7077bec610f7ab1fb374dfec/sdks/ts/src/managers/session.ts#L75)

___

### suggestions

▸ **suggestions**(`sessionId`, `options?`): `Promise`\<[`Suggestion`](../modules/api.md#suggestion)[]\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `sessionId` | `string` & `Format`\<``"uuid"``\> |
| `options` | `Object` |
| `options.limit?` | `number` & `Minimum`\<``1``\> & `Maximum`\<``1000``\> |
| `options.offset?` | `number` & `Minimum`\<``0``\> |

#### Returns

`Promise`\<[`Suggestion`](../modules/api.md#suggestion)[]\>

#### Defined in

[src/managers/session.ts:217](https://github.com/julep-ai/julep/blob/dd1994163c03c7bb7077bec610f7ab1fb374dfec/sdks/ts/src/managers/session.ts#L217)

___

### update

▸ **update**(`sessionId`, `options`, `overwrite?`): `Promise`\<[`ResourceUpdatedResponse`](../modules/api.md#resourceupdatedresponse)\>

#### Parameters

| Name | Type | Default value |
| :------ | :------ | :------ |
| `sessionId` | `string` & `Format`\<``"uuid"``\> | `undefined` |
| `options` | `Object` | `undefined` |
| `options.contextOverflow?` | ``"truncate"`` \| ``"adaptive"`` | `undefined` |
| `options.metadata?` | `Record`\<`string`, `any`\> | `undefined` |
| `options.situation` | `string` | `undefined` |
| `options.tokenBudget?` | `number` & `Minimum`\<``1``\> | `undefined` |
| `overwrite` | `boolean` | `false` |

#### Returns

`Promise`\<[`ResourceUpdatedResponse`](../modules/api.md#resourceupdatedresponse)\>

#### Defined in

[src/managers/session.ts:115](https://github.com/julep-ai/julep/blob/dd1994163c03c7bb7077bec610f7ab1fb374dfec/sdks/ts/src/managers/session.ts#L115)
