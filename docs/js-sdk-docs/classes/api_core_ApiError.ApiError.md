[@julep/sdk](../README.md) / [Exports](../modules.md) / [api/core/ApiError](../modules/api_core_ApiError.md) / ApiError

# Class: ApiError

[api/core/ApiError](../modules/api_core_ApiError.md).ApiError

## Hierarchy

- `Error`

  ↳ **`ApiError`**

## Table of contents

### Constructors

- [constructor](api_core_ApiError.ApiError.md#constructor)

### Properties

- [body](api_core_ApiError.ApiError.md#body)
- [message](api_core_ApiError.ApiError.md#message)
- [name](api_core_ApiError.ApiError.md#name)
- [request](api_core_ApiError.ApiError.md#request)
- [stack](api_core_ApiError.ApiError.md#stack)
- [status](api_core_ApiError.ApiError.md#status)
- [statusText](api_core_ApiError.ApiError.md#statustext)
- [url](api_core_ApiError.ApiError.md#url)
- [prepareStackTrace](api_core_ApiError.ApiError.md#preparestacktrace)
- [stackTraceLimit](api_core_ApiError.ApiError.md#stacktracelimit)

### Methods

- [captureStackTrace](api_core_ApiError.ApiError.md#capturestacktrace)

## Constructors

### constructor

• **new ApiError**(`request`, `response`, `message`): [`ApiError`](api_core_ApiError.ApiError.md)

#### Parameters

| Name | Type |
| :------ | :------ |
| `request` | [`ApiRequestOptions`](../modules/api_core_ApiRequestOptions.md#apirequestoptions) |
| `response` | [`ApiResult`](../modules/api_core_ApiResult.md#apiresult) |
| `message` | `string` |

#### Returns

[`ApiError`](api_core_ApiError.ApiError.md)

#### Overrides

Error.constructor

#### Defined in

[src/api/core/ApiError.ts:15](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/ApiError.ts#L15)

## Properties

### body

• `Readonly` **body**: `any`

#### Defined in

[src/api/core/ApiError.ts:12](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/ApiError.ts#L12)

___

### message

• **message**: `string`

#### Inherited from

Error.message

#### Defined in

node_modules/typescript/lib/lib.es5.d.ts:1077

___

### name

• **name**: `string`

#### Inherited from

Error.name

#### Defined in

node_modules/typescript/lib/lib.es5.d.ts:1076

___

### request

• `Readonly` **request**: [`ApiRequestOptions`](../modules/api_core_ApiRequestOptions.md#apirequestoptions)

#### Defined in

[src/api/core/ApiError.ts:13](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/ApiError.ts#L13)

___

### stack

• `Optional` **stack**: `string`

#### Inherited from

Error.stack

#### Defined in

node_modules/typescript/lib/lib.es5.d.ts:1078

___

### status

• `Readonly` **status**: `number`

#### Defined in

[src/api/core/ApiError.ts:10](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/ApiError.ts#L10)

___

### statusText

• `Readonly` **statusText**: `string`

#### Defined in

[src/api/core/ApiError.ts:11](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/ApiError.ts#L11)

___

### url

• `Readonly` **url**: `string`

#### Defined in

[src/api/core/ApiError.ts:9](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/ApiError.ts#L9)

___

### prepareStackTrace

▪ `Static` `Optional` **prepareStackTrace**: (`err`: `Error`, `stackTraces`: `CallSite`[]) => `any`

Optional override for formatting stack traces

**`See`**

https://v8.dev/docs/stack-trace-api#customizing-stack-traces

#### Type declaration

▸ (`err`, `stackTraces`): `any`

##### Parameters

| Name | Type |
| :------ | :------ |
| `err` | `Error` |
| `stackTraces` | `CallSite`[] |

##### Returns

`any`

#### Inherited from

Error.prepareStackTrace

#### Defined in

node_modules/@types/node/globals.d.ts:28

___

### stackTraceLimit

▪ `Static` **stackTraceLimit**: `number`

#### Inherited from

Error.stackTraceLimit

#### Defined in

node_modules/@types/node/globals.d.ts:30

## Methods

### captureStackTrace

▸ **captureStackTrace**(`targetObject`, `constructorOpt?`): `void`

Create .stack property on a target object

#### Parameters

| Name | Type |
| :------ | :------ |
| `targetObject` | `object` |
| `constructorOpt?` | `Function` |

#### Returns

`void`

#### Inherited from

Error.captureStackTrace

#### Defined in

node_modules/@types/node/globals.d.ts:21
