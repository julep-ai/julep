[@julep/sdk](../README.md) / [Modules](../modules.md) / core/schemas/builders/object/object

# Module: core/schemas/builders/object/object

## Table of contents

### Functions

- [getObjectUtils](core_schemas_builders_object_object.md#getobjectutils)
- [object](core_schemas_builders_object_object.md#object)

## Functions

### getObjectUtils

▸ **getObjectUtils**\<`Raw`, `Parsed`\>(`schema`): [`ObjectUtils`](../interfaces/core_schemas_builders_object_types.ObjectUtils.md)\<`Raw`, `Parsed`\>

#### Type parameters

| Name |
| :------ |
| `Raw` |
| `Parsed` |

#### Parameters

| Name | Type |
| :------ | :------ |
| `schema` | [`BaseObjectSchema`](../interfaces/core_schemas_builders_object_types.BaseObjectSchema.md)\<`Raw`, `Parsed`\> |

#### Returns

[`ObjectUtils`](../interfaces/core_schemas_builders_object_types.ObjectUtils.md)\<`Raw`, `Parsed`\>

#### Defined in

[src/api/core/schemas/builders/object/object.d.ts:11](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/object.d.ts#L11)

___

### object

▸ **object**\<`ParsedKeys`, `T`\>(`schemas`): [`inferObjectSchemaFromPropertySchemas`](core_schemas_builders_object_types.md#inferobjectschemafrompropertyschemas)\<`T`\>

#### Type parameters

| Name | Type |
| :------ | :------ |
| `ParsedKeys` | extends `string` |
| `T` | extends [`PropertySchemas`](core_schemas_builders_object_types.md#propertyschemas)\<`ParsedKeys`\> |

#### Parameters

| Name | Type |
| :------ | :------ |
| `schemas` | `T` |

#### Returns

[`inferObjectSchemaFromPropertySchemas`](core_schemas_builders_object_types.md#inferobjectschemafrompropertyschemas)\<`T`\>

#### Defined in

[src/api/core/schemas/builders/object/object.d.ts:7](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/object.d.ts#L7)
