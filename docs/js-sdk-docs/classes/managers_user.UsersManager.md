[@julep/sdk](../README.md) / [Modules](../modules.md) / [managers/user](../modules/managers_user.md) / UsersManager

# Class: UsersManager

[managers/user](../modules/managers_user.md).UsersManager

BaseManager serves as the base class for all manager classes that interact with the Julep API.
It provides common functionality needed for API interactions.

## Hierarchy

- [`BaseManager`](managers_base.BaseManager.md)

  ↳ **`UsersManager`**

## Table of contents

### Constructors

- [constructor](managers_user.UsersManager.md#constructor)

### Properties

- [apiClient](managers_user.UsersManager.md#apiclient)

### Methods

- [create](managers_user.UsersManager.md#create)
- [delete](managers_user.UsersManager.md#delete)
- [get](managers_user.UsersManager.md#get)
- [list](managers_user.UsersManager.md#list)
- [update](managers_user.UsersManager.md#update)

## Constructors

### constructor

• **new UsersManager**(`apiClient`): [`UsersManager`](managers_user.UsersManager.md)

Constructs a new instance of BaseManager.

#### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `apiClient` | [`JulepApiClient`](api_JulepApiClient.JulepApiClient.md) | The JulepApiClient instance used for API interactions. |

#### Returns

[`UsersManager`](managers_user.UsersManager.md)

#### Inherited from

[BaseManager](managers_base.BaseManager.md).[constructor](managers_base.BaseManager.md#constructor)

#### Defined in

[src/managers/base.ts:14](https://github.com/julep-ai/julep/blob/c9171a9d9cc8bab31093e3e3128a8958db5fd549/sdks/ts/src/managers/base.ts#L14)

## Properties

### apiClient

• **apiClient**: [`JulepApiClient`](api_JulepApiClient.JulepApiClient.md)

The JulepApiClient instance used for API interactions.

#### Inherited from

[BaseManager](managers_base.BaseManager.md).[apiClient](managers_base.BaseManager.md#apiclient)

#### Defined in

[src/managers/base.ts:14](https://github.com/julep-ai/julep/blob/c9171a9d9cc8bab31093e3e3128a8958db5fd549/sdks/ts/src/managers/base.ts#L14)

## Methods

### create

▸ **create**(`options?`): `Promise`\<[`User`](../modules/api.md#user)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `options` | [`CreateUserRequest`](../modules/api.md#createuserrequest) |

#### Returns

`Promise`\<[`User`](../modules/api.md#user)\>

#### Defined in

[src/managers/user.ts:22](https://github.com/julep-ai/julep/blob/c9171a9d9cc8bab31093e3e3128a8958db5fd549/sdks/ts/src/managers/user.ts#L22)

___

### delete

▸ **delete**(`userId`): `Promise`\<`void`\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `userId` | `string` & `Format`\<``"uuid"``\> |

#### Returns

`Promise`\<`void`\>

#### Defined in

[src/managers/user.ts:70](https://github.com/julep-ai/julep/blob/c9171a9d9cc8bab31093e3e3128a8958db5fd549/sdks/ts/src/managers/user.ts#L70)

___

### get

▸ **get**(`userId`): `Promise`\<[`User`](../modules/api.md#user)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `userId` | `string` & `Format`\<``"uuid"``\> |

#### Returns

`Promise`\<[`User`](../modules/api.md#user)\>

#### Defined in

[src/managers/user.ts:14](https://github.com/julep-ai/julep/blob/c9171a9d9cc8bab31093e3e3128a8958db5fd549/sdks/ts/src/managers/user.ts#L14)

___

### list

▸ **list**(`options?`): `Promise`\<[`User`](../modules/api.md#user)[]\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `options` | `Object` |
| `options.limit?` | `number` & `Type`\<``"uint32"``\> & `Minimum`\<``1``\> & `Maximum`\<``1000``\> |
| `options.metadataFilter?` | `Object` |
| `options.offset?` | `number` & `Type`\<``"uint32"``\> & `Minimum`\<``0``\> |

#### Returns

`Promise`\<[`User`](../modules/api.md#user)[]\>

#### Defined in

[src/managers/user.ts:37](https://github.com/julep-ai/julep/blob/c9171a9d9cc8bab31093e3e3128a8958db5fd549/sdks/ts/src/managers/user.ts#L37)

___

### update

▸ **update**(`userId`, `request`, `overwrite`): `Promise`\<[`User`](../modules/api.md#user)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `userId` | `string` |
| `request` | [`UpdateUserRequest`](../modules/api.md#updateuserrequest) |
| `overwrite` | ``true`` |

#### Returns

`Promise`\<[`User`](../modules/api.md#user)\>

#### Defined in

[src/managers/user.ts:76](https://github.com/julep-ai/julep/blob/c9171a9d9cc8bab31093e3e3128a8958db5fd549/sdks/ts/src/managers/user.ts#L76)

▸ **update**(`userId`, `request`, `overwrite?`): `Promise`\<[`User`](../modules/api.md#user)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `userId` | `string` |
| `request` | [`PatchUserRequest`](../modules/api.md#patchuserrequest) |
| `overwrite?` | ``false`` |

#### Returns

`Promise`\<[`User`](../modules/api.md#user)\>

#### Defined in

[src/managers/user.ts:82](https://github.com/julep-ai/julep/blob/c9171a9d9cc8bab31093e3e3128a8958db5fd549/sdks/ts/src/managers/user.ts#L82)
