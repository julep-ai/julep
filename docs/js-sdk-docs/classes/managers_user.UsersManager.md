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

[src/managers/base.ts:12](https://github.com/julep-ai/julep/blob/75b9d84686931d4e127b888c7fcc950b09165685/sdks/ts/src/managers/base.ts#L12)

## Properties

### apiClient

• **apiClient**: [`JulepApiClient`](api_JulepApiClient.JulepApiClient.md)

The JulepApiClient instance used for API interactions.

#### Inherited from

[BaseManager](managers_base.BaseManager.md).[apiClient](managers_base.BaseManager.md#apiclient)

#### Defined in

[src/managers/base.ts:12](https://github.com/julep-ai/julep/blob/75b9d84686931d4e127b888c7fcc950b09165685/sdks/ts/src/managers/base.ts#L12)

## Methods

### create

▸ **create**(`«destructured»?`): `Promise`\<[`User`](../modules/api.md#user)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | [`CreateUserRequest`](../modules/api.md#createuserrequest) |

#### Returns

`Promise`\<[`User`](../modules/api.md#user)\>

#### Defined in

[src/managers/user.ts:27](https://github.com/julep-ai/julep/blob/75b9d84686931d4e127b888c7fcc950b09165685/sdks/ts/src/managers/user.ts#L27)

___

### delete

▸ **delete**(`userId`): `Promise`\<`void`\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `userId` | `string` |

#### Returns

`Promise`\<`void`\>

#### Defined in

[src/managers/user.ts:63](https://github.com/julep-ai/julep/blob/75b9d84686931d4e127b888c7fcc950b09165685/sdks/ts/src/managers/user.ts#L63)

___

### get

▸ **get**(`userId`): `Promise`\<[`User`](../modules/api.md#user)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `userId` | `string` |

#### Returns

`Promise`\<[`User`](../modules/api.md#user)\>

#### Defined in

[src/managers/user.ts:15](https://github.com/julep-ai/julep/blob/75b9d84686931d4e127b888c7fcc950b09165685/sdks/ts/src/managers/user.ts#L15)

___

### list

▸ **list**(`«destructured»?`): `Promise`\<[`User`](../modules/api.md#user)[]\>

#### Parameters

| Name | Type | Default value |
| :------ | :------ | :------ |
| `«destructured»` | `Object` | `{}` |
| › `limit?` | `number` | `10` |
| › `metadataFilter?` | `Object` | `{}` |
| › `offset?` | `number` | `0` |

#### Returns

`Promise`\<[`User`](../modules/api.md#user)[]\>

#### Defined in

[src/managers/user.ts:44](https://github.com/julep-ai/julep/blob/75b9d84686931d4e127b888c7fcc950b09165685/sdks/ts/src/managers/user.ts#L44)

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

[src/managers/user.ts:73](https://github.com/julep-ai/julep/blob/75b9d84686931d4e127b888c7fcc950b09165685/sdks/ts/src/managers/user.ts#L73)

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

[src/managers/user.ts:79](https://github.com/julep-ai/julep/blob/75b9d84686931d4e127b888c7fcc950b09165685/sdks/ts/src/managers/user.ts#L79)
