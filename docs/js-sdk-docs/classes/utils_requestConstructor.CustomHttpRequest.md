[@julep/sdk](../README.md) / [Exports](../modules.md) / [utils/requestConstructor](../modules/utils_requestConstructor.md) / CustomHttpRequest

# Class: CustomHttpRequest

[utils/requestConstructor](../modules/utils_requestConstructor.md).CustomHttpRequest

## Hierarchy

- [`AxiosHttpRequest`](api_core_AxiosHttpRequest.AxiosHttpRequest.md)

  ↳ **`CustomHttpRequest`**

## Table of contents

### Constructors

- [constructor](utils_requestConstructor.CustomHttpRequest.md#constructor)

### Properties

- [config](utils_requestConstructor.CustomHttpRequest.md#config)

### Methods

- [request](utils_requestConstructor.CustomHttpRequest.md#request)

## Constructors

### constructor

• **new CustomHttpRequest**(`config`): [`CustomHttpRequest`](utils_requestConstructor.CustomHttpRequest.md)

#### Parameters

| Name | Type |
| :------ | :------ |
| `config` | [`OpenAPIConfig`](../modules/api_core_OpenAPI.md#openapiconfig) |

#### Returns

[`CustomHttpRequest`](utils_requestConstructor.CustomHttpRequest.md)

#### Overrides

[AxiosHttpRequest](api_core_AxiosHttpRequest.AxiosHttpRequest.md).[constructor](api_core_AxiosHttpRequest.AxiosHttpRequest.md#constructor)

#### Defined in

[src/utils/requestConstructor.ts:16](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/utils/requestConstructor.ts#L16)

## Properties

### config

• `Readonly` **config**: [`OpenAPIConfig`](../modules/api_core_OpenAPI.md#openapiconfig)

#### Inherited from

[AxiosHttpRequest](api_core_AxiosHttpRequest.AxiosHttpRequest.md).[config](api_core_AxiosHttpRequest.AxiosHttpRequest.md#config)

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

[AxiosHttpRequest](api_core_AxiosHttpRequest.AxiosHttpRequest.md).[request](api_core_AxiosHttpRequest.AxiosHttpRequest.md#request)

#### Defined in

[src/utils/requestConstructor.ts:21](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/utils/requestConstructor.ts#L21)
