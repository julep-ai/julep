[@julep/sdk](../README.md) / [Modules](../modules.md) / core/fetcher/Fetcher

# Module: core/fetcher/Fetcher

## Table of contents

### Namespaces

- [Fetcher](core_fetcher_Fetcher.Fetcher.md)

### Type Aliases

- [FetchFunction](core_fetcher_Fetcher.md#fetchfunction)

### Functions

- [fetcher](core_fetcher_Fetcher.md#fetcher)

## Type Aliases

### FetchFunction

Ƭ **FetchFunction**: \<R\>(`args`: [`Args`](../interfaces/core_fetcher_Fetcher.Fetcher.Args.md)) => `Promise`\<[`APIResponse`](core_fetcher_APIResponse.md#apiresponse)\<`R`, [`Error`](core_fetcher_Fetcher.Fetcher.md#error)\>\>

#### Type declaration

▸ \<`R`\>(`args`): `Promise`\<[`APIResponse`](core_fetcher_APIResponse.md#apiresponse)\<`R`, [`Error`](core_fetcher_Fetcher.Fetcher.md#error)\>\>

##### Type parameters

| Name | Type |
| :------ | :------ |
| `R` | `unknown` |

##### Parameters

| Name | Type |
| :------ | :------ |
| `args` | [`Args`](../interfaces/core_fetcher_Fetcher.Fetcher.Args.md) |

##### Returns

`Promise`\<[`APIResponse`](core_fetcher_APIResponse.md#apiresponse)\<`R`, [`Error`](core_fetcher_Fetcher.Fetcher.md#error)\>\>

#### Defined in

[src/api/core/fetcher/Fetcher.d.ts:2](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/fetcher/Fetcher.d.ts#L2)

## Functions

### fetcher

▸ **fetcher**\<`R`\>(`args`): `Promise`\<[`APIResponse`](core_fetcher_APIResponse.md#apiresponse)\<`R`, [`Error`](core_fetcher_Fetcher.Fetcher.md#error)\>\>

#### Type parameters

| Name | Type |
| :------ | :------ |
| `R` | `unknown` |

#### Parameters

| Name | Type |
| :------ | :------ |
| `args` | [`Args`](../interfaces/core_fetcher_Fetcher.Fetcher.Args.md) |

#### Returns

`Promise`\<[`APIResponse`](core_fetcher_APIResponse.md#apiresponse)\<`R`, [`Error`](core_fetcher_Fetcher.Fetcher.md#error)\>\>

#### Defined in

[src/api/core/fetcher/Fetcher.d.ts:41](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/fetcher/Fetcher.d.ts#L41)
