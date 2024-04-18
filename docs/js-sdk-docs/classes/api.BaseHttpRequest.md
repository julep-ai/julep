[@julep/sdk](../README.md) / [Modules](../modules.md) / [api](../modules/api.md) / BaseHttpRequest

# Class: BaseHttpRequest

[api](../modules/api.md).BaseHttpRequest

## Table of contents

### Constructors

- [constructor](api.BaseHttpRequest.md#constructor)

### Properties

- [config](api.BaseHttpRequest.md#config)

### Methods

- [request](api.BaseHttpRequest.md#request)

## Constructors

### constructor

• **new BaseHttpRequest**(`config`): [`BaseHttpRequest`](api.BaseHttpRequest.md)

#### Parameters

| Name | Type |
| :------ | :------ |
| `config` | [`OpenAPIConfig`](../modules/api.md#openapiconfig) |

#### Returns

[`BaseHttpRequest`](api.BaseHttpRequest.md)

#### Defined in

[src/api/core/BaseHttpRequest.ts:10](https://github.com/julep-ai/infuse/blob/63738d5f951c5fea204e283c17a58fa33f2f6fe0/sdks/ts/src/api/core/BaseHttpRequest.ts#L10)

## Properties

### config

• `Readonly` **config**: [`OpenAPIConfig`](../modules/api.md#openapiconfig)

#### Defined in

[src/api/core/BaseHttpRequest.ts:10](https://github.com/julep-ai/infuse/blob/63738d5f951c5fea204e283c17a58fa33f2f6fe0/sdks/ts/src/api/core/BaseHttpRequest.ts#L10)

## Methods

### request

▸ **request**\<`T`\>(`options`): [`CancelablePromise`](api.CancelablePromise.md)\<`T`\>

#### Type parameters

| Name |
| :------ |
| `T` |

#### Parameters

| Name | Type |
| :------ | :------ |
| `options` | `ApiRequestOptions` |

#### Returns

[`CancelablePromise`](api.CancelablePromise.md)\<`T`\>

#### Defined in

[src/api/core/BaseHttpRequest.ts:12](https://github.com/julep-ai/infuse/blob/63738d5f951c5fea204e283c17a58fa33f2f6fe0/sdks/ts/src/api/core/BaseHttpRequest.ts#L12)
