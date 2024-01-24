[@julep/sdk](../README.md) / [Modules](../modules.md) / core/schemas/builders/union/types

# Module: core/schemas/builders/union/types

## Table of contents

### Type Aliases

- [UnionSubtypes](core_schemas_builders_union_types.md#unionsubtypes)
- [inferParsedDiscriminant](core_schemas_builders_union_types.md#inferparseddiscriminant)
- [inferParsedUnion](core_schemas_builders_union_types.md#inferparsedunion)
- [inferRawDiscriminant](core_schemas_builders_union_types.md#inferrawdiscriminant)
- [inferRawUnion](core_schemas_builders_union_types.md#inferrawunion)

## Type Aliases

### UnionSubtypes

Ƭ **UnionSubtypes**\<`DiscriminantValues`\>: \{ [K in DiscriminantValues]: ObjectSchema\<any, any\> }

#### Type parameters

| Name | Type |
| :------ | :------ |
| `DiscriminantValues` | extends `string` \| `number` \| `symbol` |

#### Defined in

[src/api/core/schemas/builders/union/types.d.ts:3](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/union/types.d.ts#L3)

___

### inferParsedDiscriminant

Ƭ **inferParsedDiscriminant**\<`D`\>: `D` extends `string` ? `D` : `D` extends [`Discriminant`](../interfaces/core_schemas_builders_union_discriminant.Discriminant.md)\<`any`, infer Parsed\> ? `Parsed` : `never`

#### Type parameters

| Name | Type |
| :------ | :------ |
| `D` | extends `string` \| [`Discriminant`](../interfaces/core_schemas_builders_union_discriminant.Discriminant.md)\<`any`, `any`\> |

#### Defined in

[src/api/core/schemas/builders/union/types.d.ts:24](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/union/types.d.ts#L24)

___

### inferParsedUnion

Ƭ **inferParsedUnion**\<`D`, `U`\>: \{ [K in keyof U]: Record\<inferParsedDiscriminant\<D\>, K\> & inferParsedObject\<U[K]\> }[keyof `U`]

#### Type parameters

| Name | Type |
| :------ | :------ |
| `D` | extends `string` \| [`Discriminant`](../interfaces/core_schemas_builders_union_discriminant.Discriminant.md)\<`any`, `any`\> |
| `U` | extends [`UnionSubtypes`](core_schemas_builders_union_types.md#unionsubtypes)\<keyof `U`\> |

#### Defined in

[src/api/core/schemas/builders/union/types.d.ts:14](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/union/types.d.ts#L14)

___

### inferRawDiscriminant

Ƭ **inferRawDiscriminant**\<`D`\>: `D` extends `string` ? `D` : `D` extends [`Discriminant`](../interfaces/core_schemas_builders_union_discriminant.Discriminant.md)\<infer Raw, `any`\> ? `Raw` : `never`

#### Type parameters

| Name | Type |
| :------ | :------ |
| `D` | extends `string` \| [`Discriminant`](../interfaces/core_schemas_builders_union_discriminant.Discriminant.md)\<`any`, `any`\> |

#### Defined in

[src/api/core/schemas/builders/union/types.d.ts:21](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/union/types.d.ts#L21)

___

### inferRawUnion

Ƭ **inferRawUnion**\<`D`, `U`\>: \{ [K in keyof U]: Record\<inferRawDiscriminant\<D\>, K\> & inferRawObject\<U[K]\> }[keyof `U`]

#### Type parameters

| Name | Type |
| :------ | :------ |
| `D` | extends `string` \| [`Discriminant`](../interfaces/core_schemas_builders_union_discriminant.Discriminant.md)\<`any`, `any`\> |
| `U` | extends [`UnionSubtypes`](core_schemas_builders_union_types.md#unionsubtypes)\<keyof `U`\> |

#### Defined in

[src/api/core/schemas/builders/union/types.d.ts:8](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/union/types.d.ts#L8)
