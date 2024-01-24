[@julep/sdk](../README.md) / [Modules](../modules.md) / [core/schemas/builders/schema-utils/getSchemaUtils](../modules/core_schemas_builders_schema_utils_getSchemaUtils.md) / SchemaTransformer

# Interface: SchemaTransformer\<Parsed, Transformed\>

[core/schemas/builders/schema-utils/getSchemaUtils](../modules/core_schemas_builders_schema_utils_getSchemaUtils.md).SchemaTransformer

## Type parameters

| Name |
| :------ |
| `Parsed` |
| `Transformed` |

## Table of contents

### Properties

- [transform](core_schemas_builders_schema_utils_getSchemaUtils.SchemaTransformer.md#transform)
- [untransform](core_schemas_builders_schema_utils_getSchemaUtils.SchemaTransformer.md#untransform)

## Properties

### transform

• **transform**: (`parsed`: `Parsed`) => `Transformed`

#### Type declaration

▸ (`parsed`): `Transformed`

##### Parameters

| Name | Type |
| :------ | :------ |
| `parsed` | `Parsed` |

##### Returns

`Transformed`

#### Defined in

[src/api/core/schemas/builders/schema-utils/getSchemaUtils.d.ts:11](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/schema-utils/getSchemaUtils.d.ts#L11)

___

### untransform

• **untransform**: (`transformed`: `any`) => `Parsed`

#### Type declaration

▸ (`transformed`): `Parsed`

##### Parameters

| Name | Type |
| :------ | :------ |
| `transformed` | `any` |

##### Returns

`Parsed`

#### Defined in

[src/api/core/schemas/builders/schema-utils/getSchemaUtils.d.ts:12](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/schema-utils/getSchemaUtils.d.ts#L12)
