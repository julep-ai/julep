[@julep/sdk](../README.md) / [Exports](../modules.md) / [api/core/BaseHttpRequest](../modules/api_core_BaseHttpRequest.md) / BaseHttpRequest

# Class: BaseHttpRequest

[api/core/BaseHttpRequest](../modules/api_core_BaseHttpRequest.md).BaseHttpRequest

## Hierarchy

- **`BaseHttpRequest`**

  ↳ [`AxiosHttpRequest`](api_core_AxiosHttpRequest.AxiosHttpRequest.md)

## Table of contents

### Constructors

- [constructor](api_core_BaseHttpRequest.BaseHttpRequest.md#constructor)

### Properties

- [config](api_core_BaseHttpRequest.BaseHttpRequest.md#config)

### Methods

- [request](api_core_BaseHttpRequest.BaseHttpRequest.md#request)

## Constructors

### constructor

• **new BaseHttpRequest**(`config`): [`BaseHttpRequest`](api_core_BaseHttpRequest.BaseHttpRequest.md)

#### Parameters

| Name | Type |
| :------ | :------ |
| `config` | [`OpenAPIConfig`](../modules/api_core_OpenAPI.md#openapiconfig) |

#### Returns

[`BaseHttpRequest`](api_core_BaseHttpRequest.BaseHttpRequest.md)

#### Defined in

[src/api/core/BaseHttpRequest.ts:10](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/BaseHttpRequest.ts#L10)

## Properties

### config

• `Readonly` **config**: [`OpenAPIConfig`](../modules/api_core_OpenAPI.md#openapiconfig)

#### Defined in

[src/api/core/BaseHttpRequest.ts:10](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/BaseHttpRequest.ts#L10)

## Methods

### request

▸ **request**\<`T`\>(`options`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<`T`\>

#### Type parameters

| Name |
| :------ |
| `T` |

#### Parameters

| Name | Type |
| :------ | :------ |
| `options` | [`ApiRequestOptions`](../modules/api_core_ApiRequestOptions.md#apirequestoptions) |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<`T`\>

#### Defined in

[src/api/core/BaseHttpRequest.ts:12](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/BaseHttpRequest.ts#L12)
