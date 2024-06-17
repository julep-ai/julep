# Client

[@julep/sdk](../) / [Modules](../modules.md) / [api/JulepApiClient](../modules/api\_JulepApiClient.md) / JulepApiClient

## Class: JulepApiClient

[api/JulepApiClient](../modules/api\_JulepApiClient.md).JulepApiClient

### Table of contents

#### Constructors

* [constructor](api\_JulepApiClient.JulepApiClient.md#constructor)

#### Properties

* [default](api\_JulepApiClient.JulepApiClient.md#default)
* [request](api\_JulepApiClient.JulepApiClient.md#request)

### Constructors

#### constructor

• **new JulepApiClient**(`config?`, `HttpRequest?`): [`JulepApiClient`](api\_JulepApiClient.JulepApiClient.md)

**Parameters**

| Name          | Type                                                          | Default value      |
| ------------- | ------------------------------------------------------------- | ------------------ |
| `config?`     | `Partial`<[`OpenAPIConfig`](../modules/api.md#openapiconfig)> | `undefined`        |
| `HttpRequest` | `HttpRequestConstructor`                                      | `AxiosHttpRequest` |

**Returns**

[`JulepApiClient`](api\_JulepApiClient.JulepApiClient.md)

**Defined in**

[src/api/JulepApiClient.ts:13](https://github.com/julep-ai/julep/blob/0ca1d07766d1438171f2d4e9652f8251741cf335/sdks/ts/src/api/JulepApiClient.ts#L13)

### Properties

#### default

• `Readonly` **default**: [`DefaultService`](api.DefaultService.md)

**Defined in**

[src/api/JulepApiClient.ts:11](https://github.com/julep-ai/julep/blob/0ca1d07766d1438171f2d4e9652f8251741cf335/sdks/ts/src/api/JulepApiClient.ts#L11)

***

#### request

• `Readonly` **request**: [`BaseHttpRequest`](api.BaseHttpRequest.md)

**Defined in**

[src/api/JulepApiClient.ts:12](https://github.com/julep-ai/julep/blob/0ca1d07766d1438171f2d4e9652f8251741cf335/sdks/ts/src/api/JulepApiClient.ts#L12)
