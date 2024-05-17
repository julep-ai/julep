[@julep/sdk](../README.md) / [Exports](../modules.md) / [api/core/CancelablePromise](../modules/api_core_CancelablePromise.md) / CancelError

# Class: CancelError

[api/core/CancelablePromise](../modules/api_core_CancelablePromise.md).CancelError

## Hierarchy

- `Error`

  ↳ **`CancelError`**

## Table of contents

### Constructors

- [constructor](api_core_CancelablePromise.CancelError.md#constructor)

### Properties

- [message](api_core_CancelablePromise.CancelError.md#message)
- [name](api_core_CancelablePromise.CancelError.md#name)
- [stack](api_core_CancelablePromise.CancelError.md#stack)
- [prepareStackTrace](api_core_CancelablePromise.CancelError.md#preparestacktrace)
- [stackTraceLimit](api_core_CancelablePromise.CancelError.md#stacktracelimit)

### Accessors

- [isCancelled](api_core_CancelablePromise.CancelError.md#iscancelled)

### Methods

- [captureStackTrace](api_core_CancelablePromise.CancelError.md#capturestacktrace)

## Constructors

### constructor

• **new CancelError**(`message`): [`CancelError`](api_core_CancelablePromise.CancelError.md)

#### Parameters

| Name | Type |
| :------ | :------ |
| `message` | `string` |

#### Returns

[`CancelError`](api_core_CancelablePromise.CancelError.md)

#### Overrides

Error.constructor

#### Defined in

[src/api/core/CancelablePromise.ts:6](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/CancelablePromise.ts#L6)

## Properties

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

### stack

• `Optional` **stack**: `string`

#### Inherited from

Error.stack

#### Defined in

node_modules/typescript/lib/lib.es5.d.ts:1078

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

## Accessors

### isCancelled

• `get` **isCancelled**(): `boolean`

#### Returns

`boolean`

#### Defined in

[src/api/core/CancelablePromise.ts:11](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/CancelablePromise.ts#L11)

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
