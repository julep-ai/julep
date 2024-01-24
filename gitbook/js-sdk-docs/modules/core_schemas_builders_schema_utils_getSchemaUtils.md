[@julep/sdk](../README.md) / [Modules](../modules.md) / core/schemas/builders/schema-utils/getSchemaUtils

# Module: core/schemas/builders/schema-utils/getSchemaUtils

## Table of contents

### Interfaces

- [SchemaTransformer](../interfaces/core_schemas_builders_schema_utils_getSchemaUtils.SchemaTransformer.md)
- [SchemaUtils](../interfaces/core_schemas_builders_schema_utils_getSchemaUtils.SchemaUtils.md)

### Functions

- [getSchemaUtils](core_schemas_builders_schema_utils_getSchemaUtils.md#getschemautils)
- [optional](core_schemas_builders_schema_utils_getSchemaUtils.md#optional)
- [transform](core_schemas_builders_schema_utils_getSchemaUtils.md#transform)

## Functions

### getSchemaUtils

▸ **getSchemaUtils**\<`Raw`, `Parsed`\>(`schema`): [`SchemaUtils`](../interfaces/core_schemas_builders_schema_utils_getSchemaUtils.SchemaUtils.md)\<`Raw`, `Parsed`\>

#### Type parameters

| Name |
| :------ |
| `Raw` |
| `Parsed` |

#### Parameters

| Name | Type |
| :------ | :------ |
| `schema` | [`BaseSchema`](../interfaces/core_schemas_Schema.BaseSchema.md)\<`Raw`, `Parsed`\> |

#### Returns

[`SchemaUtils`](../interfaces/core_schemas_builders_schema_utils_getSchemaUtils.SchemaUtils.md)\<`Raw`, `Parsed`\>

#### Defined in

[src/api/core/schemas/builders/schema-utils/getSchemaUtils.d.ts:14](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/schema-utils/getSchemaUtils.d.ts#L14)

___

### optional

▸ **optional**\<`Raw`, `Parsed`\>(`schema`): [`Schema`](core_schemas_Schema.md#schema)\<`Raw` \| ``null`` \| `undefined`, `Parsed` \| `undefined`\>

schema utils are defined in one file to resolve issues with circular imports

#### Type parameters

| Name |
| :------ |
| `Raw` |
| `Parsed` |

#### Parameters

| Name | Type |
| :------ | :------ |
| `schema` | [`BaseSchema`](../interfaces/core_schemas_Schema.BaseSchema.md)\<`Raw`, `Parsed`\> |

#### Returns

[`Schema`](core_schemas_Schema.md#schema)\<`Raw` \| ``null`` \| `undefined`, `Parsed` \| `undefined`\>

#### Defined in

[src/api/core/schemas/builders/schema-utils/getSchemaUtils.d.ts:20](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/schema-utils/getSchemaUtils.d.ts#L20)

___

### transform

▸ **transform**\<`Raw`, `Parsed`, `Transformed`\>(`schema`, `transformer`): [`Schema`](core_schemas_Schema.md#schema)\<`Raw`, `Transformed`\>

#### Type parameters

| Name |
| :------ |
| `Raw` |
| `Parsed` |
| `Transformed` |

#### Parameters

| Name | Type |
| :------ | :------ |
| `schema` | [`BaseSchema`](../interfaces/core_schemas_Schema.BaseSchema.md)\<`Raw`, `Parsed`\> |
| `transformer` | [`SchemaTransformer`](../interfaces/core_schemas_builders_schema_utils_getSchemaUtils.SchemaTransformer.md)\<`Parsed`, `Transformed`\> |

#### Returns

[`Schema`](core_schemas_Schema.md#schema)\<`Raw`, `Transformed`\>

#### Defined in

[src/api/core/schemas/builders/schema-utils/getSchemaUtils.d.ts:23](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/schema-utils/getSchemaUtils.d.ts#L23)
