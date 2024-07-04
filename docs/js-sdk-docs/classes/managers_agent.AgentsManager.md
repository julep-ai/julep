[@julep/sdk](../README.md) / [Modules](../modules.md) / [managers/agent](../modules/managers_agent.md) / AgentsManager

# Class: AgentsManager

[managers/agent](../modules/managers_agent.md).AgentsManager

BaseManager serves as the base class for all manager classes that interact with the Julep API.
It provides common functionality needed for API interactions.

## Hierarchy

- [`BaseManager`](managers_base.BaseManager.md)

  ↳ **`AgentsManager`**

## Table of contents

### Constructors

- [constructor](managers_agent.AgentsManager.md#constructor)

### Properties

- [apiClient](managers_agent.AgentsManager.md#apiclient)

### Methods

- [create](managers_agent.AgentsManager.md#create)
- [delete](managers_agent.AgentsManager.md#delete)
- [get](managers_agent.AgentsManager.md#get)
- [list](managers_agent.AgentsManager.md#list)
- [update](managers_agent.AgentsManager.md#update)

## Constructors

### constructor

• **new AgentsManager**(`apiClient`): [`AgentsManager`](managers_agent.AgentsManager.md)

Constructs a new instance of BaseManager.

#### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `apiClient` | [`JulepApiClient`](api_JulepApiClient.JulepApiClient.md) | The JulepApiClient instance used for API interactions. |

#### Returns

[`AgentsManager`](managers_agent.AgentsManager.md)

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

### create

▸ **create**(`options`): `Promise`\<`Partial`\<[`Agent`](../modules/api.md#agent)\> & \{ `id`: `string`  }\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `options` | `Object` |
| `options.about` | `string` |
| `options.default_settings?` | [`AgentDefaultSettings`](../modules/api.md#agentdefaultsettings) |
| `options.docs?` | [`Doc`](../modules/api.md#doc)[] |
| `options.instructions` | `string` \| `string`[] |
| `options.model?` | `string` |
| `options.name` | `string` |
| `options.tools?` | [`CreateToolRequest`](../modules/api.md#createtoolrequest)[] |

#### Returns

`Promise`\<`Partial`\<[`Agent`](../modules/api.md#agent)\> & \{ `id`: `string`  }\>

#### Defined in

[src/managers/agent.ts:23](https://github.com/julep-ai/julep/blob/dd1994163c03c7bb7077bec610f7ab1fb374dfec/sdks/ts/src/managers/agent.ts#L23)

___

### delete

▸ **delete**(`agentId`): `Promise`\<`void`\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` & `Format`\<``"uuid"``\> |

#### Returns

`Promise`\<`void`\>

#### Defined in

[src/managers/agent.ts:108](https://github.com/julep-ai/julep/blob/dd1994163c03c7bb7077bec610f7ab1fb374dfec/sdks/ts/src/managers/agent.ts#L108)

___

### get

▸ **get**(`agentId`): `Promise`\<[`Agent`](../modules/api.md#agent)\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` & `Format`\<``"uuid"``\> |

#### Returns

`Promise`\<[`Agent`](../modules/api.md#agent)\>

#### Defined in

[src/managers/agent.ts:17](https://github.com/julep-ai/julep/blob/dd1994163c03c7bb7077bec610f7ab1fb374dfec/sdks/ts/src/managers/agent.ts#L17)

___

### list

▸ **list**(`options?`): `Promise`\<[`Agent`](../modules/api.md#agent)[]\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `options` | `Object` |
| `options.limit?` | `number` & `Type`\<``"uint32"``\> & `Minimum`\<``1``\> & `Maximum`\<``1000``\> |
| `options.metadataFilter?` | `Object` |
| `options.offset?` | `number` & `Type`\<``"uint32"``\> & `Minimum`\<``0``\> |

#### Returns

`Promise`\<[`Agent`](../modules/api.md#agent)[]\>

#### Defined in

[src/managers/agent.ts:74](https://github.com/julep-ai/julep/blob/dd1994163c03c7bb7077bec610f7ab1fb374dfec/sdks/ts/src/managers/agent.ts#L74)

___

### update

▸ **update**(`agentId`, `request`, `overwrite?`): `Promise`\<`Partial`\<[`Agent`](../modules/api.md#agent)\> & \{ `id`: `string`  }\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `request` | [`PatchAgentRequest`](../modules/api.md#patchagentrequest) |
| `overwrite?` | ``false`` |

#### Returns

`Promise`\<`Partial`\<[`Agent`](../modules/api.md#agent)\> & \{ `id`: `string`  }\>

#### Defined in

[src/managers/agent.ts:115](https://github.com/julep-ai/julep/blob/dd1994163c03c7bb7077bec610f7ab1fb374dfec/sdks/ts/src/managers/agent.ts#L115)

▸ **update**(`agentId`, `request`, `overwrite`): `Promise`\<`Partial`\<[`Agent`](../modules/api.md#agent)\> & \{ `id`: `string`  }\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `agentId` | `string` |
| `request` | [`UpdateAgentRequest`](../modules/api.md#updateagentrequest) |
| `overwrite` | ``true`` |

#### Returns

`Promise`\<`Partial`\<[`Agent`](../modules/api.md#agent)\> & \{ `id`: `string`  }\>

#### Defined in

[src/managers/agent.ts:121](https://github.com/julep-ai/julep/blob/dd1994163c03c7bb7077bec610f7ab1fb374dfec/sdks/ts/src/managers/agent.ts#L121)
