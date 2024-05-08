[@julep/sdk](../README.md) / [Modules](../modules.md) / [managers/doc](../modules/managers_doc.md) / DocsManager

# Class: DocsManager

[managers/doc](../modules/managers_doc.md).DocsManager

BaseManager serves as the base class for all manager classes that interact with the Julep API.
It provides common functionality needed for API interactions.

## Hierarchy

- [`BaseManager`](managers_base.BaseManager.md)

  ↳ **`DocsManager`**

## Table of contents

### Constructors

- [constructor](managers_doc.DocsManager.md#constructor)

### Properties

- [apiClient](managers_doc.DocsManager.md#apiclient)

### Methods

- [create](managers_doc.DocsManager.md#create)
- [delete](managers_doc.DocsManager.md#delete)
- [get](managers_doc.DocsManager.md#get)
- [list](managers_doc.DocsManager.md#list)

## Constructors

### constructor

• **new DocsManager**(`apiClient`): [`DocsManager`](managers_doc.DocsManager.md)

Constructs a new instance of BaseManager.

#### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `apiClient` | [`JulepApiClient`](api_JulepApiClient.JulepApiClient.md) | The JulepApiClient instance used for API interactions. |

#### Returns

[`DocsManager`](managers_doc.DocsManager.md)

#### Inherited from

[BaseManager](managers_base.BaseManager.md).[constructor](managers_base.BaseManager.md#constructor)

#### Defined in

[src/managers/base.ts:12](https://github.com/julep-ai/julep/blob/08407a6147cd8759256e5a36f249a98b1d2477ab/sdks/ts/src/managers/base.ts#L12)

## Properties

### apiClient

• **apiClient**: [`JulepApiClient`](api_JulepApiClient.JulepApiClient.md)

The JulepApiClient instance used for API interactions.

#### Inherited from

[BaseManager](managers_base.BaseManager.md).[apiClient](managers_base.BaseManager.md#apiclient)

#### Defined in

[src/managers/base.ts:12](https://github.com/julep-ai/julep/blob/08407a6147cd8759256e5a36f249a98b1d2477ab/sdks/ts/src/managers/base.ts#L12)

## Methods

### create

▸ **create**(`params`): `Promise`\<[`Doc`](../modules/api.md#doc)\>

Creates a document based on the provided agentId or userId.
Ensures that only one of agentId or userId is provided using xor function.
Validates the provided agentId or userId using isValidUuid4.

#### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `params` | `Object` | The parameters for creating a document. |
| `params.agentId?` | `string` | The agent's unique identifier, if creating for an agent. |
| `params.doc` | [`CreateDoc`](../modules/api.md#createdoc) | The document to be created. |
| `params.userId?` | `string` | The user's unique identifier, if creating for a user. |

#### Returns

`Promise`\<[`Doc`](../modules/api.md#doc)\>

The created document.

**`Throws`**

If neither agentId nor userId is provided.

#### Defined in

[src/managers/doc.ts:133](https://github.com/julep-ai/julep/blob/08407a6147cd8759256e5a36f249a98b1d2477ab/sdks/ts/src/managers/doc.ts#L133)

___

### delete

▸ **delete**(`params`): `Promise`\<`void`\>

Deletes a document based on the provided agentId or userId and the specific docId.
Ensures that only one of agentId or userId is provided using xor function.
Validates the provided agentId or userId using isValidUuid4.

#### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `params` | `Object` | The parameters for deleting a document. |
| `params.agentId?` | `string` | The agent's unique identifier, if deleting for an agent. |
| `params.docId` | `string` | The unique identifier of the document to be deleted. |
| `params.userId?` | `string` | The user's unique identifier, if deleting for a user. |

#### Returns

`Promise`\<`void`\>

A promise that resolves when the document is successfully deleted.

**`Throws`**

If neither agentId nor userId is provided.

#### Defined in

[src/managers/doc.ts:186](https://github.com/julep-ai/julep/blob/08407a6147cd8759256e5a36f249a98b1d2477ab/sdks/ts/src/managers/doc.ts#L186)

___

### get

▸ **get**(`params`): `Promise`\<\{ `items?`: [`Doc`](../modules/api.md#doc)[]  }\>

Retrieves documents based on the provided agentId or userId.
Ensures that only one of agentId or userId is provided using xor function.
Validates the provided agentId or userId using isValidUuid4.

#### Parameters

| Name | Type | Default value | Description |
| :------ | :------ | :------ | :------ |
| `params` | `Object` | `undefined` | The parameters for retrieving documents. |
| `params.agentId?` | `string` | `undefined` | The agent's unique identifier. |
| `params.limit?` | `number` | `100` | The maximum number of documents to return. |
| `params.offset?` | `number` | `0` | The offset from which to start the document retrieval. |
| `params.userId?` | `string` | `undefined` | The user's unique identifier. |

#### Returns

`Promise`\<\{ `items?`: [`Doc`](../modules/api.md#doc)[]  }\>

The retrieved documents.

**`Throws`**

If neither agentId nor userId is provided.

#### Defined in

[src/managers/doc.ts:22](https://github.com/julep-ai/julep/blob/08407a6147cd8759256e5a36f249a98b1d2477ab/sdks/ts/src/managers/doc.ts#L22)

___

### list

▸ **list**(`params?`): `Promise`\<[`Doc`](../modules/api.md#doc)[]\>

Lists documents based on the provided agentId or userId, with optional metadata filtering.
Ensures that only one of agentId or userId is provided using xor function.
Validates the provided agentId or userId using isValidUuid4.
Allows for filtering based on metadata.

#### Parameters

| Name | Type | Default value | Description |
| :------ | :------ | :------ | :------ |
| `params` | `Object` | `{}` | The parameters for listing documents, including filtering options. |
| `params.agentId?` | `string` | `undefined` | The agent's unique identifier, if filtering by agent. |
| `params.limit?` | `number` | `100` | The maximum number of documents to return. |
| `params.metadataFilter?` | `Object` | `{}` | Optional metadata to filter the documents. |
| `params.offset?` | `number` | `0` | The offset from which to start the document listing. |
| `params.userId?` | `string` | `undefined` | The user's unique identifier, if filtering by user. |

#### Returns

`Promise`\<[`Doc`](../modules/api.md#doc)[]\>

The list of filtered documents.

**`Throws`**

If neither agentId nor userId is provided.

#### Defined in

[src/managers/doc.ts:74](https://github.com/julep-ai/julep/blob/08407a6147cd8759256e5a36f249a98b1d2477ab/sdks/ts/src/managers/doc.ts#L74)
