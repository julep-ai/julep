[@julep/sdk](../README.md) / [Modules](../modules.md) / [api/JulepApiClient](../modules/api_JulepApiClient.md) / JulepApiClient

# Class: JulepApiClient

[api/JulepApiClient](../modules/api_JulepApiClient.md).JulepApiClient

## Table of contents

### Constructors

- [constructor](api_JulepApiClient.JulepApiClient.md#constructor)

### Properties

- [default](api_JulepApiClient.JulepApiClient.md#default)
- [request](api_JulepApiClient.JulepApiClient.md#request)

## Constructors

### constructor

• **new JulepApiClient**(`config?`, `HttpRequest?`): [`JulepApiClient`](api_JulepApiClient.JulepApiClient.md)

#### Parameters

| Name | Type | Default value |
| :------ | :------ | :------ |
| `config?` | `Partial`\<[`OpenAPIConfig`](../modules/api.md#openapiconfig)\> | `undefined` |
| `HttpRequest` | `HttpRequestConstructor` | `AxiosHttpRequest` |

#### Returns

[`JulepApiClient`](api_JulepApiClient.JulepApiClient.md)

#### Defined in

[src/api/JulepApiClient.ts:13](https://github.com/julep-ai/julep/blob/c703332acc3c978fec6732847b3d2cfd6d3b1330/sdks/ts/src/api/JulepApiClient.ts#L13)

## Properties

### default

• `Readonly` **default**: [`DefaultService`](api.DefaultService.md)

#### Defined in

[src/api/JulepApiClient.ts:11](https://github.com/julep-ai/julep/blob/c703332acc3c978fec6732847b3d2cfd6d3b1330/sdks/ts/src/api/JulepApiClient.ts#L11)

___

### request

• `Readonly` **request**: [`BaseHttpRequest`](api.BaseHttpRequest.md)

#### Defined in

[src/api/JulepApiClient.ts:12](https://github.com/julep-ai/julep/blob/c703332acc3c978fec6732847b3d2cfd6d3b1330/sdks/ts/src/api/JulepApiClient.ts#L12)
