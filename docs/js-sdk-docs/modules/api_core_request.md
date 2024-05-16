[@julep/sdk](../README.md) / [Exports](../modules.md) / api/core/request

# Module: api/core/request

## Table of contents

### Functions

- [base64](api_core_request.md#base64)
- [catchErrorCodes](api_core_request.md#catcherrorcodes)
- [getFormData](api_core_request.md#getformdata)
- [getHeaders](api_core_request.md#getheaders)
- [getQueryString](api_core_request.md#getquerystring)
- [getRequestBody](api_core_request.md#getrequestbody)
- [getResponseBody](api_core_request.md#getresponsebody)
- [getResponseHeader](api_core_request.md#getresponseheader)
- [isBlob](api_core_request.md#isblob)
- [isDefined](api_core_request.md#isdefined)
- [isFormData](api_core_request.md#isformdata)
- [isString](api_core_request.md#isstring)
- [isStringWithValue](api_core_request.md#isstringwithvalue)
- [isSuccess](api_core_request.md#issuccess)
- [request](api_core_request.md#request)
- [resolve](api_core_request.md#resolve)
- [sendRequest](api_core_request.md#sendrequest)

## Functions

### base64

▸ **base64**(`str`): `string`

#### Parameters

| Name | Type |
| :------ | :------ |
| `str` | `string` |

#### Returns

`string`

#### Defined in

[src/api/core/request.ts:56](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/request.ts#L56)

___

### catchErrorCodes

▸ **catchErrorCodes**(`options`, `result`): `void`

#### Parameters

| Name | Type |
| :------ | :------ |
| `options` | [`ApiRequestOptions`](api_core_ApiRequestOptions.md#apirequestoptions) |
| `result` | [`ApiResult`](api_core_ApiResult.md#apiresult) |

#### Returns

`void`

#### Defined in

[src/api/core/request.ts:275](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/request.ts#L275)

___

### getFormData

▸ **getFormData**(`options`): `undefined` \| `FormData`

#### Parameters

| Name | Type |
| :------ | :------ |
| `options` | [`ApiRequestOptions`](api_core_ApiRequestOptions.md#apirequestoptions) |

#### Returns

`undefined` \| `FormData`

#### Defined in

[src/api/core/request.ts:118](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/request.ts#L118)

___

### getHeaders

▸ **getHeaders**(`config`, `options`, `formData?`): `Promise`\<`Record`\<`string`, `string`\>\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `config` | [`OpenAPIConfig`](api_core_OpenAPI.md#openapiconfig) |
| `options` | [`ApiRequestOptions`](api_core_ApiRequestOptions.md#apirequestoptions) |
| `formData?` | `FormData` |

#### Returns

`Promise`\<`Record`\<`string`, `string`\>\>

#### Defined in

[src/api/core/request.ts:159](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/request.ts#L159)

___

### getQueryString

▸ **getQueryString**(`params`): `string`

#### Parameters

| Name | Type |
| :------ | :------ |
| `params` | `Record`\<`string`, `any`\> |

#### Returns

`string`

#### Defined in

[src/api/core/request.ts:65](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/request.ts#L65)

___

### getRequestBody

▸ **getRequestBody**(`options`): `any`

#### Parameters

| Name | Type |
| :------ | :------ |
| `options` | [`ApiRequestOptions`](api_core_ApiRequestOptions.md#apirequestoptions) |

#### Returns

`any`

#### Defined in

[src/api/core/request.ts:214](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/request.ts#L214)

___

### getResponseBody

▸ **getResponseBody**(`response`): `any`

#### Parameters

| Name | Type |
| :------ | :------ |
| `response` | `AxiosResponse`\<`any`, `any`\> |

#### Returns

`any`

#### Defined in

[src/api/core/request.ts:268](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/request.ts#L268)

___

### getResponseHeader

▸ **getResponseHeader**(`response`, `responseHeader?`): `undefined` \| `string`

#### Parameters

| Name | Type |
| :------ | :------ |
| `response` | `AxiosResponse`\<`any`, `any`\> |
| `responseHeader?` | `string` |

#### Returns

`undefined` \| `string`

#### Defined in

[src/api/core/request.ts:255](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/request.ts#L255)

___

### isBlob

▸ **isBlob**(`value`): value is Blob

#### Parameters

| Name | Type |
| :------ | :------ |
| `value` | `any` |

#### Returns

value is Blob

#### Defined in

[src/api/core/request.ts:35](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/request.ts#L35)

___

### isDefined

▸ **isDefined**\<`T`\>(`value`): value is Exclude\<T, undefined \| null\>

#### Type parameters

| Name |
| :------ |
| `T` |

#### Parameters

| Name | Type |
| :------ | :------ |
| `value` | `undefined` \| ``null`` \| `T` |

#### Returns

value is Exclude\<T, undefined \| null\>

#### Defined in

[src/api/core/request.ts:21](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/request.ts#L21)

___

### isFormData

▸ **isFormData**(`value`): value is FormData

#### Parameters

| Name | Type |
| :------ | :------ |
| `value` | `any` |

#### Returns

value is FormData

#### Defined in

[src/api/core/request.ts:48](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/request.ts#L48)

___

### isString

▸ **isString**(`value`): value is string

#### Parameters

| Name | Type |
| :------ | :------ |
| `value` | `any` |

#### Returns

value is string

#### Defined in

[src/api/core/request.ts:27](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/request.ts#L27)

___

### isStringWithValue

▸ **isStringWithValue**(`value`): value is string

#### Parameters

| Name | Type |
| :------ | :------ |
| `value` | `any` |

#### Returns

value is string

#### Defined in

[src/api/core/request.ts:31](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/request.ts#L31)

___

### isSuccess

▸ **isSuccess**(`status`): `boolean`

#### Parameters

| Name | Type |
| :------ | :------ |
| `status` | `number` |

#### Returns

`boolean`

#### Defined in

[src/api/core/request.ts:52](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/request.ts#L52)

___

### request

▸ **request**\<`T`\>(`config`, `options`, `axiosClient?`): [`CancelablePromise`](../classes/api_core_CancelablePromise.CancelablePromise.md)\<`T`\>

Request method

#### Type parameters

| Name |
| :------ |
| `T` |

#### Parameters

| Name | Type | Default value | Description |
| :------ | :------ | :------ | :------ |
| `config` | [`OpenAPIConfig`](api_core_OpenAPI.md#openapiconfig) | `undefined` | The OpenAPI configuration object |
| `options` | [`ApiRequestOptions`](api_core_ApiRequestOptions.md#apirequestoptions) | `undefined` | The request options from the service |
| `axiosClient` | `AxiosInstance` | `axios` | The axios client instance to use |

#### Returns

[`CancelablePromise`](../classes/api_core_CancelablePromise.CancelablePromise.md)\<`T`\>

CancelablePromise<T>

**`Throws`**

ApiError

#### Defined in

[src/api/core/request.ts:322](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/request.ts#L322)

___

### resolve

▸ **resolve**\<`T`\>(`options`, `resolver?`): `Promise`\<`undefined` \| `T`\>

#### Type parameters

| Name |
| :------ |
| `T` |

#### Parameters

| Name | Type |
| :------ | :------ |
| `options` | [`ApiRequestOptions`](api_core_ApiRequestOptions.md#apirequestoptions) |
| `resolver?` | `T` \| `Resolver`\<`T`\> |

#### Returns

`Promise`\<`undefined` \| `T`\>

#### Defined in

[src/api/core/request.ts:149](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/request.ts#L149)

___

### sendRequest

▸ **sendRequest**\<`T`\>(`config`, `options`, `url`, `body`, `formData`, `headers`, `onCancel`, `axiosClient`): `Promise`\<`AxiosResponse`\<`T`, `any`\>\>

#### Type parameters

| Name |
| :------ |
| `T` |

#### Parameters

| Name | Type |
| :------ | :------ |
| `config` | [`OpenAPIConfig`](api_core_OpenAPI.md#openapiconfig) |
| `options` | [`ApiRequestOptions`](api_core_ApiRequestOptions.md#apirequestoptions) |
| `url` | `string` |
| `body` | `any` |
| `formData` | `undefined` \| `FormData` |
| `headers` | `Record`\<`string`, `string`\> |
| `onCancel` | [`OnCancel`](../interfaces/api_core_CancelablePromise.OnCancel.md) |
| `axiosClient` | `AxiosInstance` |

#### Returns

`Promise`\<`AxiosResponse`\<`T`, `any`\>\>

#### Defined in

[src/api/core/request.ts:221](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/request.ts#L221)
