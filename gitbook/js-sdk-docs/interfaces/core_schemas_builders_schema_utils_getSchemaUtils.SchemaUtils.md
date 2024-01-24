[@julep/sdk](../README.md) / [Modules](../modules.md) / [core/schemas/builders/schema-utils/getSchemaUtils](../modules/core_schemas_builders_schema_utils_getSchemaUtils.md) / SchemaUtils

# Interface: SchemaUtils\<Raw, Parsed\>

[core/schemas/builders/schema-utils/getSchemaUtils](../modules/core_schemas_builders_schema_utils_getSchemaUtils.md).SchemaUtils

## Type parameters

| Name |
| :------ |
| `Raw` |
| `Parsed` |

## Table of contents

### Properties

- [jsonOrThrow](core_schemas_builders_schema_utils_getSchemaUtils.SchemaUtils.md#jsonorthrow)
- [optional](core_schemas_builders_schema_utils_getSchemaUtils.SchemaUtils.md#optional)
- [parseOrThrow](core_schemas_builders_schema_utils_getSchemaUtils.SchemaUtils.md#parseorthrow)
- [transform](core_schemas_builders_schema_utils_getSchemaUtils.SchemaUtils.md#transform)

## Properties

### jsonOrThrow

• **jsonOrThrow**: (`raw`: `unknown`, `opts?`: [`SchemaOptions`](core_schemas_Schema.SchemaOptions.md)) => `Promise`\<`Raw`\>

#### Type declaration

▸ (`raw`, `opts?`): `Promise`\<`Raw`\>

##### Parameters

| Name | Type |
| :------ | :------ |
| `raw` | `unknown` |
| `opts?` | [`SchemaOptions`](core_schemas_Schema.SchemaOptions.md) |

##### Returns

`Promise`\<`Raw`\>

#### Defined in

[src/api/core/schemas/builders/schema-utils/getSchemaUtils.d.ts:8](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/schema-utils/getSchemaUtils.d.ts#L8)

___

### optional

• **optional**: () => [`Schema`](../modules/core_schemas_Schema.md#schema)\<`undefined` \| ``null`` \| `Raw`, `undefined` \| `Parsed`\>

#### Type declaration

▸ (): [`Schema`](../modules/core_schemas_Schema.md#schema)\<`undefined` \| ``null`` \| `Raw`, `undefined` \| `Parsed`\>

##### Returns

[`Schema`](../modules/core_schemas_Schema.md#schema)\<`undefined` \| ``null`` \| `Raw`, `undefined` \| `Parsed`\>

#### Defined in

[src/api/core/schemas/builders/schema-utils/getSchemaUtils.d.ts:3](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/schema-utils/getSchemaUtils.d.ts#L3)

___

### parseOrThrow

• **parseOrThrow**: (`raw`: `unknown`, `opts?`: [`SchemaOptions`](core_schemas_Schema.SchemaOptions.md)) => `Promise`\<`Parsed`\>

#### Type declaration

▸ (`raw`, `opts?`): `Promise`\<`Parsed`\>

##### Parameters

| Name | Type |
| :------ | :------ |
| `raw` | `unknown` |
| `opts?` | [`SchemaOptions`](core_schemas_Schema.SchemaOptions.md) |

##### Returns

`Promise`\<`Parsed`\>

#### Defined in

[src/api/core/schemas/builders/schema-utils/getSchemaUtils.d.ts:7](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/schema-utils/getSchemaUtils.d.ts#L7)

___

### transform

• **transform**: \<Transformed\>(`transformer`: [`SchemaTransformer`](core_schemas_builders_schema_utils_getSchemaUtils.SchemaTransformer.md)\<`Parsed`, `Transformed`\>) => [`Schema`](../modules/core_schemas_Schema.md#schema)\<`Raw`, `Transformed`\>

#### Type declaration

▸ \<`Transformed`\>(`transformer`): [`Schema`](../modules/core_schemas_Schema.md#schema)\<`Raw`, `Transformed`\>

##### Type parameters

| Name |
| :------ |
| `Transformed` |

##### Parameters

| Name | Type |
| :------ | :------ |
| `transformer` | [`SchemaTransformer`](core_schemas_builders_schema_utils_getSchemaUtils.SchemaTransformer.md)\<`Parsed`, `Transformed`\> |

##### Returns

[`Schema`](../modules/core_schemas_Schema.md#schema)\<`Raw`, `Transformed`\>

#### Defined in

[src/api/core/schemas/builders/schema-utils/getSchemaUtils.d.ts:4](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/schema-utils/getSchemaUtils.d.ts#L4)
