[@julep/sdk](../README.md) / [Modules](../modules.md) / [api](../modules/api.md) / CancelError

# Class: CancelError

[api](../modules/api.md).CancelError

## Hierarchy

- `Error`

  ↳ **`CancelError`**

## Table of contents

### Constructors

- [constructor](api.CancelError.md#constructor)

### Properties

- [message](api.CancelError.md#message)
- [name](api.CancelError.md#name)
- [stack](api.CancelError.md#stack)
- [prepareStackTrace](api.CancelError.md#preparestacktrace)
- [stackTraceLimit](api.CancelError.md#stacktracelimit)

### Accessors

- [isCancelled](api.CancelError.md#iscancelled)

### Methods

- [captureStackTrace](api.CancelError.md#capturestacktrace)

## Constructors

### constructor

• **new CancelError**(`message`): [`CancelError`](api.CancelError.md)

#### Parameters

| Name | Type |
| :------ | :------ |
| `message` | `string` |

#### Returns

[`CancelError`](api.CancelError.md)

#### Overrides

Error.constructor

#### Defined in

[src/api/core/CancelablePromise.ts:6](https://github.com/julep-ai/julep/blob/c8ef59fdd0cb68867b0ad9e09a0183bba8b152be/sdks/ts/src/api/core/CancelablePromise.ts#L6)

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

[src/api/core/CancelablePromise.ts:11](https://github.com/julep-ai/julep/blob/c8ef59fdd0cb68867b0ad9e09a0183bba8b152be/sdks/ts/src/api/core/CancelablePromise.ts#L11)

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
