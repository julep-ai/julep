[@julep/sdk](../README.md) / [Modules](../modules.md) / core/schemas/builders/undiscriminated-union/types

# Module: core/schemas/builders/undiscriminated-union/types

## Table of contents

### Type Aliases

- [UndiscriminatedUnionSchema](core_schemas_builders_undiscriminated_union_types.md#undiscriminatedunionschema)
- [inferParsedUnidiscriminatedUnionSchema](core_schemas_builders_undiscriminated_union_types.md#inferparsedunidiscriminatedunionschema)
- [inferRawUnidiscriminatedUnionSchema](core_schemas_builders_undiscriminated_union_types.md#inferrawunidiscriminatedunionschema)

## Type Aliases

### UndiscriminatedUnionSchema

Ƭ **UndiscriminatedUnionSchema**\<`Schemas`\>: [`Schema`](core_schemas_Schema.md#schema)\<[`inferRawUnidiscriminatedUnionSchema`](core_schemas_builders_undiscriminated_union_types.md#inferrawunidiscriminatedunionschema)\<`Schemas`\>, [`inferParsedUnidiscriminatedUnionSchema`](core_schemas_builders_undiscriminated_union_types.md#inferparsedunidiscriminatedunionschema)\<`Schemas`\>\>

#### Type parameters

| Name | Type |
| :------ | :------ |
| `Schemas` | extends [...Schema[]] |

#### Defined in

[src/api/core/schemas/builders/undiscriminated-union/types.d.ts:2](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/undiscriminated-union/types.d.ts#L2)

___

### inferParsedUnidiscriminatedUnionSchema

Ƭ **inferParsedUnidiscriminatedUnionSchema**\<`Schemas`\>: [`inferParsed`](core_schemas_Schema.md#inferparsed)\<`Schemas`[`number`]\>

#### Type parameters

| Name | Type |
| :------ | :------ |
| `Schemas` | extends [...Schema[]] |

#### Defined in

[src/api/core/schemas/builders/undiscriminated-union/types.d.ts:10](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/undiscriminated-union/types.d.ts#L10)

___

### inferRawUnidiscriminatedUnionSchema

Ƭ **inferRawUnidiscriminatedUnionSchema**\<`Schemas`\>: [`inferRaw`](core_schemas_Schema.md#inferraw)\<`Schemas`[`number`]\>

#### Type parameters

| Name | Type |
| :------ | :------ |
| `Schemas` | extends [...Schema[]] |

#### Defined in

[src/api/core/schemas/builders/undiscriminated-union/types.d.ts:7](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/undiscriminated-union/types.d.ts#L7)
