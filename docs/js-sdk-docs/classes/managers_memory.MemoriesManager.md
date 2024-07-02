[@julep/sdk](../README.md) / [Modules](../modules.md) / [managers/memory](../modules/managers_memory.md) / MemoriesManager

# Class: MemoriesManager

[managers/memory](../modules/managers_memory.md).MemoriesManager

BaseManager serves as the base class for all manager classes that interact with the Julep API.
It provides common functionality needed for API interactions.

## Hierarchy

- [`BaseManager`](managers_base.BaseManager.md)

  ↳ **`MemoriesManager`**

## Table of contents

### Constructors

- [constructor](managers_memory.MemoriesManager.md#constructor)

### Properties

- [apiClient](managers_memory.MemoriesManager.md#apiclient)

### Methods

- [list](managers_memory.MemoriesManager.md#list)

## Constructors

### constructor

• **new MemoriesManager**(`apiClient`): [`MemoriesManager`](managers_memory.MemoriesManager.md)

Constructs a new instance of BaseManager.

#### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `apiClient` | [`JulepApiClient`](api_JulepApiClient.JulepApiClient.md) | The JulepApiClient instance used for API interactions. |

#### Returns

[`MemoriesManager`](managers_memory.MemoriesManager.md)

#### Inherited from

[BaseManager](managers_base.BaseManager.md).[constructor](managers_base.BaseManager.md#constructor)

#### Defined in

[src/managers/base.ts:14](https://github.com/julep-ai/julep/blob/95c1a0c85f2af36bb95762cf8f17743fa7cf60e8/sdks/ts/src/managers/base.ts#L14)

## Properties

### apiClient

• **apiClient**: [`JulepApiClient`](api_JulepApiClient.JulepApiClient.md)

The JulepApiClient instance used for API interactions.

#### Inherited from

[BaseManager](managers_base.BaseManager.md).[apiClient](managers_base.BaseManager.md#apiclient)

#### Defined in

[src/managers/base.ts:14](https://github.com/julep-ai/julep/blob/95c1a0c85f2af36bb95762cf8f17743fa7cf60e8/sdks/ts/src/managers/base.ts#L14)

## Methods

### list

▸ **list**(`options`): `Promise`\<[`Memory`](../modules/api.md#memory)[]\>

Lists memories based on the provided parameters.

#### Parameters

| Name | Type |
| :------ | :------ |
| `options` | `Object` |
| `options.agentId` | `string` & `Format`\<``"uuid"``\> |
| `options.limit?` | `number` & `Type`\<``"uint32"``\> & `Minimum`\<``1``\> & `Maximum`\<``1000``\> |
| `options.offset?` | `number` & `Type`\<``"uint32"``\> & `Minimum`\<``0``\> |
| `options.query` | `string` |
| `options.userId?` | `string` & `Format`\<``"uuid"``\> |

#### Returns

`Promise`\<[`Memory`](../modules/api.md#memory)[]\>

A promise that resolves to an array of Memory objects.

#### Defined in

[src/managers/memory.ts:21](https://github.com/julep-ai/julep/blob/95c1a0c85f2af36bb95762cf8f17743fa7cf60e8/sdks/ts/src/managers/memory.ts#L21)
