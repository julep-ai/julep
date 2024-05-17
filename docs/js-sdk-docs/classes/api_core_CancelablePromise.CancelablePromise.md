[@julep/sdk](../README.md) / [Exports](../modules.md) / [api/core/CancelablePromise](../modules/api_core_CancelablePromise.md) / CancelablePromise

# Class: CancelablePromise\<T\>

[api/core/CancelablePromise](../modules/api_core_CancelablePromise.md).CancelablePromise

## Type parameters

| Name |
| :------ |
| `T` |

## Implements

- `Promise`\<`T`\>

## Table of contents

### Constructors

- [constructor](api_core_CancelablePromise.CancelablePromise.md#constructor)

### Properties

- [#cancelHandlers](api_core_CancelablePromise.CancelablePromise.md##cancelhandlers)
- [#isCancelled](api_core_CancelablePromise.CancelablePromise.md##iscancelled)
- [#isRejected](api_core_CancelablePromise.CancelablePromise.md##isrejected)
- [#isResolved](api_core_CancelablePromise.CancelablePromise.md##isresolved)
- [#promise](api_core_CancelablePromise.CancelablePromise.md##promise)
- [#reject](api_core_CancelablePromise.CancelablePromise.md##reject)
- [#resolve](api_core_CancelablePromise.CancelablePromise.md##resolve)

### Accessors

- [[toStringTag]](api_core_CancelablePromise.CancelablePromise.md#[tostringtag])
- [isCancelled](api_core_CancelablePromise.CancelablePromise.md#iscancelled)

### Methods

- [cancel](api_core_CancelablePromise.CancelablePromise.md#cancel)
- [catch](api_core_CancelablePromise.CancelablePromise.md#catch)
- [finally](api_core_CancelablePromise.CancelablePromise.md#finally)
- [then](api_core_CancelablePromise.CancelablePromise.md#then)

## Constructors

### constructor

• **new CancelablePromise**\<`T`\>(`executor`): [`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<`T`\>

#### Type parameters

| Name |
| :------ |
| `T` |

#### Parameters

| Name | Type |
| :------ | :------ |
| `executor` | (`resolve`: (`value`: `T` \| `PromiseLike`\<`T`\>) => `void`, `reject`: (`reason?`: `any`) => `void`, `onCancel`: [`OnCancel`](../interfaces/api_core_CancelablePromise.OnCancel.md)) => `void` |

#### Returns

[`CancelablePromise`](api_core_CancelablePromise.CancelablePromise.md)\<`T`\>

#### Defined in

[src/api/core/CancelablePromise.ts:33](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/CancelablePromise.ts#L33)

## Properties

### #cancelHandlers

• `Private` `Readonly` **#cancelHandlers**: () => `void`[]

#### Defined in

[src/api/core/CancelablePromise.ts:28](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/CancelablePromise.ts#L28)

___

### #isCancelled

• `Private` **#isCancelled**: `boolean`

#### Defined in

[src/api/core/CancelablePromise.ts:27](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/CancelablePromise.ts#L27)

___

### #isRejected

• `Private` **#isRejected**: `boolean`

#### Defined in

[src/api/core/CancelablePromise.ts:26](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/CancelablePromise.ts#L26)

___

### #isResolved

• `Private` **#isResolved**: `boolean`

#### Defined in

[src/api/core/CancelablePromise.ts:25](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/CancelablePromise.ts#L25)

___

### #promise

• `Private` `Readonly` **#promise**: `Promise`\<`T`\>

#### Defined in

[src/api/core/CancelablePromise.ts:29](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/CancelablePromise.ts#L29)

___

### #reject

• `Private` `Optional` **#reject**: (`reason?`: `any`) => `void`

#### Type declaration

▸ (`reason?`): `void`

##### Parameters

| Name | Type |
| :------ | :------ |
| `reason?` | `any` |

##### Returns

`void`

#### Defined in

[src/api/core/CancelablePromise.ts:31](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/CancelablePromise.ts#L31)

___

### #resolve

• `Private` `Optional` **#resolve**: (`value`: `T` \| `PromiseLike`\<`T`\>) => `void`

#### Type declaration

▸ (`value`): `void`

##### Parameters

| Name | Type |
| :------ | :------ |
| `value` | `T` \| `PromiseLike`\<`T`\> |

##### Returns

`void`

#### Defined in

[src/api/core/CancelablePromise.ts:30](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/CancelablePromise.ts#L30)

## Accessors

### [toStringTag]

• `get` **[toStringTag]**(): `string`

#### Returns

`string`

#### Implementation of

Promise.[toStringTag]

#### Defined in

[src/api/core/CancelablePromise.ts:87](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/CancelablePromise.ts#L87)

___

### isCancelled

• `get` **isCancelled**(): `boolean`

#### Returns

`boolean`

#### Defined in

[src/api/core/CancelablePromise.ts:127](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/CancelablePromise.ts#L127)

## Methods

### cancel

▸ **cancel**(): `void`

#### Returns

`void`

#### Defined in

[src/api/core/CancelablePromise.ts:108](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/CancelablePromise.ts#L108)

___

### catch

▸ **catch**\<`TResult`\>(`onRejected?`): `Promise`\<`T` \| `TResult`\>

#### Type parameters

| Name | Type |
| :------ | :------ |
| `TResult` | `never` |

#### Parameters

| Name | Type |
| :------ | :------ |
| `onRejected?` | ``null`` \| (`reason`: `any`) => `TResult` \| `PromiseLike`\<`TResult`\> |

#### Returns

`Promise`\<`T` \| `TResult`\>

#### Implementation of

Promise.catch

#### Defined in

[src/api/core/CancelablePromise.ts:98](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/CancelablePromise.ts#L98)

___

### finally

▸ **finally**(`onFinally?`): `Promise`\<`T`\>

#### Parameters

| Name | Type |
| :------ | :------ |
| `onFinally?` | ``null`` \| () => `void` |

#### Returns

`Promise`\<`T`\>

#### Implementation of

Promise.finally

#### Defined in

[src/api/core/CancelablePromise.ts:104](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/CancelablePromise.ts#L104)

___

### then

▸ **then**\<`TResult1`, `TResult2`\>(`onFulfilled?`, `onRejected?`): `Promise`\<`TResult1` \| `TResult2`\>

#### Type parameters

| Name | Type |
| :------ | :------ |
| `TResult1` | `T` |
| `TResult2` | `never` |

#### Parameters

| Name | Type |
| :------ | :------ |
| `onFulfilled?` | ``null`` \| (`value`: `T`) => `TResult1` \| `PromiseLike`\<`TResult1`\> |
| `onRejected?` | ``null`` \| (`reason`: `any`) => `TResult2` \| `PromiseLike`\<`TResult2`\> |

#### Returns

`Promise`\<`TResult1` \| `TResult2`\>

#### Implementation of

Promise.then

#### Defined in

[src/api/core/CancelablePromise.ts:91](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/CancelablePromise.ts#L91)
