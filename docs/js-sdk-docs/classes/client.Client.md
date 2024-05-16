[@julep/sdk](../README.md) / [Exports](../modules.md) / [client](../modules/client.md) / Client

# Class: Client

[client](../modules/client.md).Client

Client for interacting with the Julep API and OpenAI.

## Table of contents

### Constructors

- [constructor](client.Client.md#constructor)

### Properties

- [\_apiClient](client.Client.md#_apiclient)
- [\_openaiClient](client.Client.md#_openaiclient)
- [agents](client.Client.md#agents)
- [chat](client.Client.md#chat)
- [completions](client.Client.md#completions)
- [docs](client.Client.md#docs)
- [memories](client.Client.md#memories)
- [sessions](client.Client.md#sessions)
- [tools](client.Client.md#tools)
- [users](client.Client.md#users)

## Constructors

### constructor

• **new Client**(`options?`): [`Client`](client.Client.md)

Creates an instance of Client.
Initializes the client with the provided or default API key and base URL. If neither are provided nor set as environment variables, an error is thrown.

#### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `options?` | `ClientOptions` | Configuration options for the client. |

#### Returns

[`Client`](client.Client.md)

**`Throws`**

Throws an error if both apiKey and baseUrl are not provided and not set as environment variables.

#### Defined in

[src/client.ts:33](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/client.ts#L33)

## Properties

### \_apiClient

• `Private` **\_apiClient**: [`JulepApiClient`](api_JulepApiClient.JulepApiClient.md)

#### Defined in

[src/client.ts:22](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/client.ts#L22)

___

### \_openaiClient

• `Private` **\_openaiClient**: `OpenAI`

#### Defined in

[src/client.ts:23](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/client.ts#L23)

___

### agents

• **agents**: [`AgentsManager`](managers_agent.AgentsManager.md)

Manager for interacting with agents.
Provides methods to manage and interact with agents within the Julep API.

#### Defined in

[src/client.ts:72](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/client.ts#L72)

___

### chat

• **chat**: `Chat`

OpenAI Chat API.
This is patched to enhance functionality and ensure compatibility with Julep API.

#### Defined in

[src/client.ts:108](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/client.ts#L108)

___

### completions

• **completions**: `Completions`

OpenAI Completions API.
Enhanced with custom patches for improved integration and usage within Julep.

#### Defined in

[src/client.ts:114](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/client.ts#L114)

___

### docs

• **docs**: [`DocsManager`](managers_doc.DocsManager.md)

Manager for interacting with documents.
Enables document management including creation, update, and deletion.

#### Defined in

[src/client.ts:90](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/client.ts#L90)

___

### memories

• **memories**: [`MemoriesManager`](managers_memory.MemoriesManager.md)

Manager for interacting with memories.
Allows for storing and retrieving user-specific data and preferences.

#### Defined in

[src/client.ts:96](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/client.ts#L96)

___

### sessions

• **sessions**: [`SessionsManager`](managers_session.SessionsManager.md)

Manager for interacting with sessions.
Facilitates the creation, management, and retrieval of user sessions.

#### Defined in

[src/client.ts:84](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/client.ts#L84)

___

### tools

• **tools**: [`ToolsManager`](managers_tool.ToolsManager.md)

Manager for interacting with tools.
Provides access to various utility tools and functionalities.

#### Defined in

[src/client.ts:102](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/client.ts#L102)

___

### users

• **users**: [`UsersManager`](managers_user.UsersManager.md)

Manager for interacting with users.
Offers functionalities to handle user accounts and their data.

#### Defined in

[src/client.ts:78](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/client.ts#L78)
