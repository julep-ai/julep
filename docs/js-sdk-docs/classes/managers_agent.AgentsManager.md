# Agent

[@julep/sdk](../) / [Modules](../modules.md) / [managers/agent](../modules/managers\_agent.md) / AgentsManager

## Class: AgentsManager

[managers/agent](../modules/managers\_agent.md).AgentsManager

BaseManager serves as the base class for all manager classes that interact with the Julep API. It provides common functionality needed for API interactions.

### Hierarchy

*   [`BaseManager`](managers\_base.BaseManager.md)

    ↳ **`AgentsManager`**

### Table of contents

#### Constructors

* [constructor](managers\_agent.AgentsManager.md#constructor)

#### Properties

* [apiClient](managers\_agent.AgentsManager.md#apiclient)

#### Methods

* [create](managers\_agent.AgentsManager.md#create)
* [delete](managers\_agent.AgentsManager.md#delete)
* [get](managers\_agent.AgentsManager.md#get)
* [list](managers\_agent.AgentsManager.md#list)
* [update](managers\_agent.AgentsManager.md#update)

### Constructors

#### constructor

• **new AgentsManager**(`apiClient`): [`AgentsManager`](managers\_agent.AgentsManager.md)

Constructs a new instance of BaseManager.

**Parameters**

| Name        | Type                                                      | Description                                            |
| ----------- | --------------------------------------------------------- | ------------------------------------------------------ |
| `apiClient` | [`JulepApiClient`](api\_JulepApiClient.JulepApiClient.md) | The JulepApiClient instance used for API interactions. |

**Returns**

[`AgentsManager`](managers\_agent.AgentsManager.md)

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

#### create

▸ **create**(`«destructured»`): `Promise`<`Partial`<[`Agent`](../modules/api.md#agent)> & { `id`: `string` }>

**Parameters**

| Name                  | Type                                                             | Default value                 |
| --------------------- | ---------------------------------------------------------------- | ----------------------------- |
| `«destructured»`      | `Object`                                                         | `undefined`                   |
| › `about`             | `string`                                                         | `undefined`                   |
| › `default_settings?` | [`AgentDefaultSettings`](../modules/api.md#agentdefaultsettings) | `undefined`                   |
| › `docs?`             | [`Doc`](../modules/api.md#doc)\[]                                | `[]`                          |
| › `instructions`      | `string` \| `string`\[]                                          | `[]`                          |
| › `model?`            | `string`                                                         | `"julep-ai/samantha-1-turbo"` |
| › `name`              | `string`                                                         | `undefined`                   |
| › `tools?`            | [`CreateToolRequest`](../modules/api.md#createtoolrequest)\[]    | `undefined`                   |

**Returns**

`Promise`<`Partial`<[`Agent`](../modules/api.md#agent)> & { `id`: `string` }>

**Defined in**

[src/managers/agent.ts:24](https://github.com/julep-ai/julep/blob/0ca1d07766d1438171f2d4e9652f8251741cf335/sdks/ts/src/managers/agent.ts#L24)

***

#### delete

▸ **delete**(`agentId`): `Promise`<`void`>

**Parameters**

| Name      | Type     |
| --------- | -------- |
| `agentId` | `string` |

**Returns**

`Promise`<`void`>

**Defined in**

[src/managers/agent.ts:85](https://github.com/julep-ai/julep/blob/0ca1d07766d1438171f2d4e9652f8251741cf335/sdks/ts/src/managers/agent.ts#L85)

***

#### get

▸ **get**(`agentId`): `Promise`<[`Agent`](../modules/api.md#agent)>

**Parameters**

| Name      | Type     |
| --------- | -------- |
| `agentId` | `string` |

**Returns**

`Promise`<[`Agent`](../modules/api.md#agent)>

**Defined in**

[src/managers/agent.ts:18](https://github.com/julep-ai/julep/blob/0ca1d07766d1438171f2d4e9652f8251741cf335/sdks/ts/src/managers/agent.ts#L18)

***

#### list

▸ **list**(`«destructured»?`): `Promise`<[`Agent`](../modules/api.md#agent)\[]>

**Parameters**

| Name                | Type     | Default value |
| ------------------- | -------- | ------------- |
| `«destructured»`    | `Object` | `{}`          |
| › `limit?`          | `number` | `100`         |
| › `metadataFilter?` | `Object` | `{}`          |
| › `offset?`         | `number` | `0`           |

**Returns**

`Promise`<[`Agent`](../modules/api.md#agent)\[]>

**Defined in**

[src/managers/agent.ts:65](https://github.com/julep-ai/julep/blob/0ca1d07766d1438171f2d4e9652f8251741cf335/sdks/ts/src/managers/agent.ts#L65)

***

#### update

▸ **update**(`agentId`, `request`, `overwrite?`): `Promise`<`Partial`<[`Agent`](../modules/api.md#agent)> & { `id`: `string` }>

**Parameters**

| Name         | Type                                                       |
| ------------ | ---------------------------------------------------------- |
| `agentId`    | `string`                                                   |
| `request`    | [`PatchAgentRequest`](../modules/api.md#patchagentrequest) |
| `overwrite?` | `false`                                                    |

**Returns**

`Promise`<`Partial`<[`Agent`](../modules/api.md#agent)> & { `id`: `string` }>

**Defined in**

[src/managers/agent.ts:92](https://github.com/julep-ai/julep/blob/0ca1d07766d1438171f2d4e9652f8251741cf335/sdks/ts/src/managers/agent.ts#L92)

▸ **update**(`agentId`, `request`, `overwrite`): `Promise`<`Partial`<[`Agent`](../modules/api.md#agent)> & { `id`: `string` }>

**Parameters**

| Name        | Type                                                         |
| ----------- | ------------------------------------------------------------ |
| `agentId`   | `string`                                                     |
| `request`   | [`UpdateAgentRequest`](../modules/api.md#updateagentrequest) |
| `overwrite` | `true`                                                       |

**Returns**

`Promise`<`Partial`<[`Agent`](../modules/api.md#agent)> & { `id`: `string` }>

**Defined in**

[src/managers/agent.ts:98](https://github.com/julep-ai/julep/blob/0ca1d07766d1438171f2d4e9652f8251741cf335/sdks/ts/src/managers/agent.ts#L98)
