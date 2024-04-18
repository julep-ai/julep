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

[src/managers/base.ts:12](https://github.com/julep-ai/julep/blob/459f37c65d4e139f914f7bba9dec6f3570b62fcb/sdks/ts/src/managers/base.ts#L12)

## Properties

### apiClient

• **apiClient**: [`JulepApiClient`](api_JulepApiClient.JulepApiClient.md)

The JulepApiClient instance used for API interactions.

#### Inherited from

[BaseManager](managers_base.BaseManager.md).[apiClient](managers_base.BaseManager.md#apiclient)

#### Defined in

[src/managers/base.ts:12](https://github.com/julep-ai/julep/blob/459f37c65d4e139f914f7bba9dec6f3570b62fcb/sdks/ts/src/managers/base.ts#L12)

## Methods

### create

▸ **create**(`«destructured»`): `Promise`\<[`Tool`](../modules/api.md#tool)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `tool` | `Object` |
| › `tool.function` | [`FunctionDef`](../modules/api.md#functiondef) |
| › `tool.type` | ``"function"`` \| ``"webhook"`` |

#### Returns

`Promise`\<[`Tool`](../modules/api.md#tool)\>

#### Defined in

[src/managers/tool.ts:32](https://github.com/julep-ai/julep/blob/459f37c65d4e139f914f7bba9dec6f3570b62fcb/sdks/ts/src/managers/tool.ts#L32)

___

### delete

▸ **delete**(`«destructured»`): `Promise`\<`void`\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `«destructured»` | `Object` |
| › `agentId` | `string` |
| › `toolId` | `string` |

#### Returns

`Promise`\<`void`\>

#### Defined in

[src/managers/tool.ts:86](https://github.com/julep-ai/julep/blob/459f37c65d4e139f914f7bba9dec6f3570b62fcb/sdks/ts/src/managers/tool.ts#L86)

___

### list

▸ **list**(`agentId`, `«destructured»?`): `Promise`\<[`Tool`](../modules/api.md#tool)[]\>

#### Parameters

| Name | Type | Default value |
| :------ | :------ | :------ |
| `agentId` | `string` | `undefined` |
| `«destructured»` | `Object` | `{}` |
| › `limit?` | `number` | `10` |
| › `offset?` | `number` | `0` |

#### Returns

`Promise`\<[`Tool`](../modules/api.md#tool)[]\>

#### Defined in

[src/managers/tool.ts:12](https://github.com/julep-ai/julep/blob/459f37c65d4e139f914f7bba9dec6f3570b62fcb/sdks/ts/src/managers/tool.ts#L12)

___

### update

▸ **update**(`«destructured»`, `overwrite?`): `Promise`\<[`Tool`](../modules/api.md#tool)\>

#### Parameters

| Name | Type | Default value |
| :------ | :------ | :------ |
| `«destructured»` | `Object` | `undefined` |
| › `agentId` | `string` | `undefined` |
| › `tool` | [`UpdateToolRequest`](../modules/api.md#updatetoolrequest) | `undefined` |
| › `toolId` | `string` | `undefined` |
| `overwrite` | `boolean` | `false` |

#### Returns

`Promise`\<[`Tool`](../modules/api.md#tool)\>

#### Defined in

[src/managers/tool.ts:54](https://github.com/julep-ai/julep/blob/459f37c65d4e139f914f7bba9dec6f3570b62fcb/sdks/ts/src/managers/tool.ts#L54)
