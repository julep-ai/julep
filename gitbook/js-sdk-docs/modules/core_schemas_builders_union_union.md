[@julep/sdk](../README.md) / [Modules](../modules.md) / core/schemas/builders/union/union

# Module: core/schemas/builders/union/union

## Table of contents

### Functions

- [union](core_schemas_builders_union_union.md#union)

## Functions

### union

▸ **union**\<`D`, `U`\>(`discriminant`, `union`): [`ObjectLikeSchema`](core_schemas_builders_object_like_types.md#objectlikeschema)\<[`inferRawUnion`](core_schemas_builders_union_types.md#inferrawunion)\<`D`, `U`\>, [`inferParsedUnion`](core_schemas_builders_union_types.md#inferparsedunion)\<`D`, `U`\>\>

#### Type parameters

| Name | Type |
| :------ | :------ |
| `D` | extends `string` \| [`Discriminant`](../interfaces/core_schemas_builders_union_discriminant.Discriminant.md)\<`any`, `any`\> |
| `U` | extends [`UnionSubtypes`](core_schemas_builders_union_types.md#unionsubtypes)\<`any`\> |

#### Parameters

| Name | Type |
| :------ | :------ |
| `discriminant` | `D` |
| `union` | `U` |

#### Returns

[`ObjectLikeSchema`](core_schemas_builders_object_like_types.md#objectlikeschema)\<[`inferRawUnion`](core_schemas_builders_union_types.md#inferrawunion)\<`D`, `U`\>, [`inferParsedUnion`](core_schemas_builders_union_types.md#inferparsedunion)\<`D`, `U`\>\>

#### Defined in

[src/api/core/schemas/builders/union/union.d.ts:4](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/union/union.d.ts#L4)
