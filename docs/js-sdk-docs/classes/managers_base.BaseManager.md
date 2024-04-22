[@julep/sdk](../README.md) / [Modules](../modules.md) / [managers/base](../modules/managers_base.md) / BaseManager

# Class: BaseManager

[managers/base](../modules/managers_base.md).BaseManager

BaseManager serves as the base class for all manager classes that interact with the Julep API.
It provides common functionality needed for API interactions.

## Hierarchy

- **`BaseManager`**

  ↳ [`AgentsManager`](managers_agent.AgentsManager.md)

  ↳ [`DocsManager`](managers_doc.DocsManager.md)

  ↳ [`MemoriesManager`](managers_memory.MemoriesManager.md)

  ↳ [`SessionsManager`](managers_session.SessionsManager.md)

  ↳ [`ToolsManager`](managers_tool.ToolsManager.md)

  ↳ [`UsersManager`](managers_user.UsersManager.md)

## Table of contents

### Constructors

- [constructor](managers_base.BaseManager.md#constructor)

### Properties

- [apiClient](managers_base.BaseManager.md#apiclient)

## Constructors

### constructor

• **new BaseManager**(`apiClient`): [`BaseManager`](managers_base.BaseManager.md)

Constructs a new instance of BaseManager.

#### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `apiClient` | [`JulepApiClient`](api_JulepApiClient.JulepApiClient.md) | The JulepApiClient instance used for API interactions. |

#### Returns

[`BaseManager`](managers_base.BaseManager.md)

#### Defined in

[src/managers/base.ts:12](https://github.com/julep-ai/julep/blob/7e0cd1ddad0ce1e315b5dcb1a50a56fc6a63a183/sdks/ts/src/managers/base.ts#L12)

## Properties

### apiClient

• **apiClient**: [`JulepApiClient`](api_JulepApiClient.JulepApiClient.md)

The JulepApiClient instance used for API interactions.

#### Defined in

[src/managers/base.ts:12](https://github.com/julep-ai/julep/blob/7e0cd1ddad0ce1e315b5dcb1a50a56fc6a63a183/sdks/ts/src/managers/base.ts#L12)
