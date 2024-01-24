[@julep/sdk](../README.md) / [Modules](../modules.md) / core/schemas/builders/object/objectWithoutOptionalProperties

# Module: core/schemas/builders/object/objectWithoutOptionalProperties

## Table of contents

### Type Aliases

- [inferObjectWithoutOptionalPropertiesSchemaFromPropertySchemas](core_schemas_builders_object_objectWithoutOptionalProperties.md#inferobjectwithoutoptionalpropertiesschemafrompropertyschemas)
- [inferParsedObjectWithoutOptionalPropertiesFromPropertySchemas](core_schemas_builders_object_objectWithoutOptionalProperties.md#inferparsedobjectwithoutoptionalpropertiesfrompropertyschemas)

### Functions

- [objectWithoutOptionalProperties](core_schemas_builders_object_objectWithoutOptionalProperties.md#objectwithoutoptionalproperties)

## Type Aliases

### inferObjectWithoutOptionalPropertiesSchemaFromPropertySchemas

Ƭ **inferObjectWithoutOptionalPropertiesSchemaFromPropertySchemas**\<`T`\>: [`ObjectSchema`](core_schemas_builders_object_types.md#objectschema)\<[`inferRawObjectFromPropertySchemas`](core_schemas_builders_object_types.md#inferrawobjectfrompropertyschemas)\<`T`\>, [`inferParsedObjectWithoutOptionalPropertiesFromPropertySchemas`](core_schemas_builders_object_objectWithoutOptionalProperties.md#inferparsedobjectwithoutoptionalpropertiesfrompropertyschemas)\<`T`\>\>

#### Type parameters

| Name | Type |
| :------ | :------ |
| `T` | extends [`PropertySchemas`](core_schemas_builders_object_types.md#propertyschemas)\<keyof `T`\> |

#### Defined in

[src/api/core/schemas/builders/object/objectWithoutOptionalProperties.d.ts:11](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/objectWithoutOptionalProperties.d.ts#L11)

___

### inferParsedObjectWithoutOptionalPropertiesFromPropertySchemas

Ƭ **inferParsedObjectWithoutOptionalPropertiesFromPropertySchemas**\<`T`\>: \{ [K in keyof T]: inferParsedPropertySchema\<T[K]\> }

#### Type parameters

| Name | Type |
| :------ | :------ |
| `T` | extends [`PropertySchemas`](core_schemas_builders_object_types.md#propertyschemas)\<keyof `T`\> |

#### Defined in

[src/api/core/schemas/builders/object/objectWithoutOptionalProperties.d.ts:17](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/objectWithoutOptionalProperties.d.ts#L17)

## Functions

### objectWithoutOptionalProperties

▸ **objectWithoutOptionalProperties**\<`ParsedKeys`, `T`\>(`schemas`): [`inferObjectWithoutOptionalPropertiesSchemaFromPropertySchemas`](core_schemas_builders_object_objectWithoutOptionalProperties.md#inferobjectwithoutoptionalpropertiesschemafrompropertyschemas)\<`T`\>

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

[`inferObjectWithoutOptionalPropertiesSchemaFromPropertySchemas`](core_schemas_builders_object_objectWithoutOptionalProperties.md#inferobjectwithoutoptionalpropertiesschemafrompropertyschemas)\<`T`\>

#### Defined in

[src/api/core/schemas/builders/object/objectWithoutOptionalProperties.d.ts:7](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/objectWithoutOptionalProperties.d.ts#L7)
