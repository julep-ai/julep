# Memory

[@julep/sdk](../) / [Modules](../modules.md) / [managers/memory](../modules/managers\_memory.md) / MemoriesManager

## Class: MemoriesManager

[managers/memory](../modules/managers\_memory.md).MemoriesManager

BaseManager serves as the base class for all manager classes that interact with the Julep API. It provides common functionality needed for API interactions.

### Hierarchy

*   [`BaseManager`](managers\_base.BaseManager.md)

    ↳ **`MemoriesManager`**

### Table of contents

#### Constructors

* [constructor](managers\_memory.MemoriesManager.md#constructor)

#### Properties

* [apiClient](managers\_memory.MemoriesManager.md#apiclient)

#### Methods

* [list](managers\_memory.MemoriesManager.md#list)

### Constructors

#### constructor

• **new MemoriesManager**(`apiClient`): [`MemoriesManager`](managers\_memory.MemoriesManager.md)

Constructs a new instance of BaseManager.

**Parameters**

| Name        | Type                                                      | Description                                            |
| ----------- | --------------------------------------------------------- | ------------------------------------------------------ |
| `apiClient` | [`JulepApiClient`](api\_JulepApiClient.JulepApiClient.md) | The JulepApiClient instance used for API interactions. |

**Returns**

[`MemoriesManager`](managers\_memory.MemoriesManager.md)

**Inherited from**

[BaseManager](managers\_base.BaseManager.md).[constructor](managers\_base.BaseManager.md#constructor)

**Defined in**

[src/managers/base.ts:12](https://github.com/julep-ai/julep/blob/0ca1d07766d1438171f2d4e9652f8251741cf335/sdks/ts/src/managers/base.ts#L12)

### Properties

#### apiClient

• **apiClient**: [`JulepApiClient`](api\_JulepApiClient.JulepApiClient.md)

The JulepApiClient instance used for API interactions.

**Inherited from**

[BaseManager](managers\_base.BaseManager.md).[apiClient](managers\_base.BaseManager.md#apiclient)

**Defined in**

[src/managers/base.ts:12](https://github.com/julep-ai/julep/blob/0ca1d07766d1438171f2d4e9652f8251741cf335/sdks/ts/src/managers/base.ts#L12)

### Methods

#### list

▸ **list**(`«destructured»`): `Promise`<[`Memory`](../modules/api.md#memory)\[]>

Lists memories based on the provided parameters.

**Parameters**

| Name             | Type     | Default value |
| ---------------- | -------- | ------------- |
| `«destructured»` | `Object` | `undefined`   |
| › `agentId`      | `string` | `undefined`   |
| › `limit?`       | `number` | `100`         |
| › `offset?`      | `number` | `0`           |
| › `query`        | `string` | `undefined`   |
| › `userId?`      | `string` | `undefined`   |

**Returns**

`Promise`<[`Memory`](../modules/api.md#memory)\[]>

A promise that resolves to an array of Memory objects.

**Defined in**

[src/managers/memory.ts:21](https://github.com/julep-ai/julep/blob/0ca1d07766d1438171f2d4e9652f8251741cf335/sdks/ts/src/managers/memory.ts#L21)
