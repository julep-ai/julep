[@julep/sdk](../README.md) / [Exports](../modules.md) / [api/core/AxiosHttpRequest](../modules/api_core_AxiosHttpRequest.md) / AxiosHttpRequest

# Class: AxiosHttpRequest

[api/core/AxiosHttpRequest](../modules/api_core_AxiosHttpRequest.md).AxiosHttpRequest

## Hierarchy

- [`BaseHttpRequest`](api_core_BaseHttpRequest.BaseHttpRequest.md)

  ↳ **`AxiosHttpRequest`**

  ↳↳ [`CustomHttpRequest`](utils_requestConstructor.CustomHttpRequest.md)

## Table of contents

### Constructors

- [constructor](api_core_AxiosHttpRequest.AxiosHttpRequest.md#constructor)

### Properties

- [config](api_core_AxiosHttpRequest.AxiosHttpRequest.md#config)

### Methods

- [request](api_core_AxiosHttpRequest.AxiosHttpRequest.md#request)

## Constructors

### constructor

• **new AxiosHttpRequest**(`config`): [`AxiosHttpRequest`](api_core_AxiosHttpRequest.AxiosHttpRequest.md)

#### Parameters

| Name | Type |
| :------ | :------ |
| `config` | [`OpenAPIConfig`](../modules/api_core_OpenAPI.md#openapiconfig) |

#### Returns

[`AxiosHttpRequest`](api_core_AxiosHttpRequest.AxiosHttpRequest.md)

#### Overrides

[BaseHttpRequest](api_core_BaseHttpRequest.BaseHttpRequest.md).[constructor](api_core_BaseHttpRequest.BaseHttpRequest.md#constructor)

#### Defined in

[src/api/core/AxiosHttpRequest.ts:12](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/AxiosHttpRequest.ts#L12)

## Properties

### config

• `Readonly` **config**: [`OpenAPIConfig`](../modules/api_core_OpenAPI.md#openapiconfig)

#### Inherited from

[BaseHttpRequest](api_core_BaseHttpRequest.BaseHttpRequest.md).[config](api_core_BaseHttpRequest.BaseHttpRequest.md#config)

#### Defined in

[src/api/core/BaseHttpRequest.ts:10](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/BaseHttpRequest.ts#L10)

## Methods

### request

▸ **request**\<`T`\>(`options`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<`T`\>

Request method

#### Type parameters

| Name |
| :------ |
| `T` |

#### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `options` | [`ApiRequestOptions`](../modules/api_core_ApiRequestOptions.md#apirequestoptions) | The request options from the service |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<`T`\>

CancelablePromise<T>

**`Throws`**

ApiError

#### Overrides

[BaseHttpRequest](api_core_BaseHttpRequest.BaseHttpRequest.md).[request](api_core_BaseHttpRequest.BaseHttpRequest.md#request)

#### Defined in

[src/api/core/AxiosHttpRequest.ts:22](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/AxiosHttpRequest.ts#L22)
