[@julep/sdk](../README.md) / [Modules](../modules.md) / [managers/tool](../modules/managers_tool.md) / ToolsManager

# Class: ToolsManager

[managers/tool](../modules/managers_tool.md).ToolsManager

BaseManager serves as the base class for all manager classes that interact with the Julep API.
It provides common functionality needed for API interactions.

## Hierarchy

- [`BaseManager`](managers_base.BaseManager.md)

  ↳ **`ToolsManager`**

## Table of contents

### Constructors

- [constructor](managers_tool.ToolsManager.md#constructor)

### Properties

- [apiClient](managers_tool.ToolsManager.md#apiclient)

### Methods

- [create](managers_tool.ToolsManager.md#create)
- [delete](managers_tool.ToolsManager.md#delete)
- [list](managers_tool.ToolsManager.md#list)
- [update](managers_tool.ToolsManager.md#update)

## Constructors

### constructor

• **new ToolsManager**(`apiClient`): [`ToolsManager`](managers_tool.ToolsManager.md)

Constructs a new instance of BaseManager.

#### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `apiClient` | [`JulepApiClient`](api_JulepApiClient.JulepApiClient.md) | The JulepApiClient instance used for API interactions. |

#### Returns

[`ToolsManager`](managers_tool.ToolsManager.md)

#### Inherited from

[BaseManager](managers_base.BaseManager.md).[constructor](managers_base.BaseManager.md#constructor)

#### Defined in

[src/managers/base.ts:14](https://github.com/julep-ai/julep/blob/1aacc650d71dfc8cc6e2993599c2493784d992ef/sdks/ts/src/managers/base.ts#L14)

## Properties

### apiClient

• **apiClient**: [`JulepApiClient`](api_JulepApiClient.JulepApiClient.md)

The JulepApiClient instance used for API interactions.

#### Inherited from

[BaseManager](managers_base.BaseManager.md).[apiClient](managers_base.BaseManager.md#apiclient)

#### Defined in

[src/managers/base.ts:14](https://github.com/julep-ai/julep/blob/1aacc650d71dfc8cc6e2993599c2493784d992ef/sdks/ts/src/managers/base.ts#L14)

## Methods

### create

▸ **create**(`options`): `Promise`\<[`Tool`](../modules/api.md#tool)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `options` | `Object` |
| `options.agentId` | `string` & `Format`\<``"uuid"``\> |
| `options.tool` | `Object` |
| `options.tool.function` | [`FunctionDef`](../modules/api.md#functiondef) |
| `options.tool.type` | ``"function"`` \| ``"webhook"`` |

#### Returns

`Promise`\<[`Tool`](../modules/api.md#tool)\>

#### Defined in

[src/managers/tool.ts:44](https://github.com/julep-ai/julep/blob/1aacc650d71dfc8cc6e2993599c2493784d992ef/sdks/ts/src/managers/tool.ts#L44)

___

### delete

▸ **delete**(`options`): `Promise`\<`void`\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `options` | `Object` |
| `options.agentId` | `string` & `Format`\<``"uuid"``\> |
| `options.toolId` | `string` & `Format`\<``"uuid"``\> |

#### Returns

`Promise`\<`void`\>

#### Defined in

[src/managers/tool.ts:105](https://github.com/julep-ai/julep/blob/1aacc650d71dfc8cc6e2993599c2493784d992ef/sdks/ts/src/managers/tool.ts#L105)

___

### list

▸ **list**(`agentId`, `options?`): `Promise`\<[`Tool`](../modules/api.md#tool)[]\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` & `Format`\<``"uuid"``\> |
| `options` | `Object` |
| `options.limit?` | `number` & `Type`\<``"uint32"``\> & `Minimum`\<``1``\> & `Maximum`\<``1000``\> |
| `options.offset?` | `number` & `Type`\<``"uint32"``\> & `Minimum`\<``0``\> |

#### Returns

`Promise`\<[`Tool`](../modules/api.md#tool)[]\>

#### Defined in

[src/managers/tool.ts:14](https://github.com/julep-ai/julep/blob/1aacc650d71dfc8cc6e2993599c2493784d992ef/sdks/ts/src/managers/tool.ts#L14)

___

### update

▸ **update**(`options`, `overwrite?`): `Promise`\<[`Tool`](../modules/api.md#tool)\>

#### Parameters

| Name | Type | Default value |
| :------ | :------ | :------ |
| `options` | `Object` | `undefined` |
| `options.agentId` | `string` & `Format`\<``"uuid"``\> | `undefined` |
| `options.tool` | [`UpdateToolRequest`](../modules/api.md#updatetoolrequest) | `undefined` |
| `options.toolId` | `string` & `Format`\<``"uuid"``\> | `undefined` |
| `overwrite` | `boolean` | `false` |

#### Returns

`Promise`\<[`Tool`](../modules/api.md#tool)\>

#### Defined in

[src/managers/tool.ts:71](https://github.com/julep-ai/julep/blob/1aacc650d71dfc8cc6e2993599c2493784d992ef/sdks/ts/src/managers/tool.ts#L71)
