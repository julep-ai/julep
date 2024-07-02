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

[src/managers/base.ts:14](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/managers/base.ts#L14)

## Properties

### apiClient

• **apiClient**: [`JulepApiClient`](api_JulepApiClient.JulepApiClient.md)

The JulepApiClient instance used for API interactions.

#### Inherited from

[BaseManager](managers_base.BaseManager.md).[apiClient](managers_base.BaseManager.md#apiclient)

#### Defined in

[src/managers/base.ts:14](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/managers/base.ts#L14)

## Methods

### create

▸ **create**(`options`): `Promise`\<[`Doc`](../modules/api.md#doc)\>

Creates a document based on the provided agentId or userId.
Ensures that only one of agentId or userId is provided using xor function.
Validates the provided agentId or userId using isValidUuid4.

#### Parameters

| Name | Type |
| :------ | :------ |
| `options` | `Object` |
| `options.agentId?` | `string` & `Format`\<``"uuid"``\> |
| `options.doc` | [`CreateDoc`](../modules/api.md#createdoc) |
| `options.userId?` | `string` & `Format`\<``"uuid"``\> |

#### Returns

`Promise`\<[`Doc`](../modules/api.md#doc)\>

The created document.

**`Throws`**

If neither agentId nor userId is provided.

#### Defined in

[src/managers/doc.ts:162](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/managers/doc.ts#L162)

___

### delete

▸ **delete**(`options`): `Promise`\<`void`\>

Deletes a document based on the provided agentId or userId and the specific docId.
Ensures that only one of agentId or userId is provided using xor function.
Validates the provided agentId or userId using isValidUuid4.

#### Parameters

| Name | Type |
| :------ | :------ |
| `options` | `Object` |
| `options.agentId?` | `string` & `Format`\<``"uuid"``\> |
| `options.docId` | `string` |
| `options.userId?` | `string` & `Format`\<``"uuid"``\> |

#### Returns

`Promise`\<`void`\>

A promise that resolves when the document is successfully deleted.

**`Throws`**

If neither agentId nor userId is provided.

#### Defined in

[src/managers/doc.ts:214](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/managers/doc.ts#L214)

___

### get

▸ **get**(`options?`): `Promise`\<[`CancelablePromise`](api.CancelablePromise.md)\<\{ `items?`: [`Doc`](../modules/api.md#doc)[]  }\> \| [`CancelablePromise`](api.CancelablePromise.md)\<\{ `items?`: [`Doc`](../modules/api.md#doc)[]  }\>\>

Retrieves documents based on the provided agentId or userId.
Ensures that only one of agentId or userId is provided using xor function.
Validates the provided agentId or userId using isValidUuid4.

#### Parameters

| Name | Type |
| :------ | :------ |
| `options` | `Object` |
| `options.agentId?` | `string` & `Format`\<``"uuid"``\> |
| `options.limit?` | `number` & `Type`\<``"uint32"``\> & `Minimum`\<``1``\> & `Maximum`\<``1000``\> |
| `options.offset?` | `number` & `Type`\<``"uint32"``\> & `Minimum`\<``0``\> |
| `options.userId?` | `string` & `Format`\<``"uuid"``\> |

#### Returns

`Promise`\<[`CancelablePromise`](api.CancelablePromise.md)\<\{ `items?`: [`Doc`](../modules/api.md#doc)[]  }\> \| [`CancelablePromise`](api.CancelablePromise.md)\<\{ `items?`: [`Doc`](../modules/api.md#doc)[]  }\>\>

The retrieved documents.

**`Throws`**

If neither agentId nor userId is provided.

#### Defined in

[src/managers/doc.ts:23](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/managers/doc.ts#L23)

___

### list

▸ **list**(`options?`): `Promise`\<[`Doc`](../modules/api.md#doc)[]\>

Lists documents based on the provided agentId or userId, with optional metadata filtering.
Ensures that only one of agentId or userId is provided using xor function.
Validates the provided agentId or userId using isValidUuid4.
Allows for filtering based on metadata.

#### Parameters

| Name | Type |
| :------ | :------ |
| `options` | `Object` |
| `options.agentId?` | `string` & `Format`\<``"uuid"``\> |
| `options.limit?` | `number` & `Type`\<``"uint32"``\> & `Minimum`\<``1``\> & `Maximum`\<``1000``\> |
| `options.metadataFilter?` | `Object` |
| `options.offset?` | `number` & `Type`\<``"uint32"``\> & `Minimum`\<``0``\> |
| `options.userId?` | `string` & `Format`\<``"uuid"``\> |

#### Returns

`Promise`\<[`Doc`](../modules/api.md#doc)[]\>

The list of filtered documents.

**`Throws`**

If neither agentId nor userId is provided.

#### Defined in

[src/managers/doc.ts:90](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/managers/doc.ts#L90)
