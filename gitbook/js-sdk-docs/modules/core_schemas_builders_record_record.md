[@julep/sdk](../README.md) / [Modules](../modules.md) / core/schemas/builders/record/record

# Module: core/schemas/builders/record/record

## Table of contents

### Functions

- [record](core_schemas_builders_record_record.md#record)

## Functions

### record

▸ **record**\<`RawKey`, `RawValue`, `ParsedValue`, `ParsedKey`\>(`keySchema`, `valueSchema`): [`RecordSchema`](core_schemas_builders_record_types.md#recordschema)\<`RawKey`, `RawValue`, `ParsedKey`, `ParsedValue`\>

#### Type parameters

| Name | Type |
| :------ | :------ |
| `RawKey` | extends `string` \| `number` |
| `RawValue` | `RawValue` |
| `ParsedValue` | `ParsedValue` |
| `ParsedKey` | extends `string` \| `number` |

#### Parameters

| Name | Type |
| :------ | :------ |
| `keySchema` | [`Schema`](core_schemas_Schema.md#schema)\<`RawKey`, `ParsedKey`\> |
| `valueSchema` | [`Schema`](core_schemas_Schema.md#schema)\<`RawValue`, `ParsedValue`\> |

#### Returns

[`RecordSchema`](core_schemas_builders_record_types.md#recordschema)\<`RawKey`, `RawValue`, `ParsedKey`, `ParsedValue`\>

#### Defined in

[src/api/core/schemas/builders/record/record.d.ts:3](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/record/record.d.ts#L3)
