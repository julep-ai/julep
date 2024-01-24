[@julep/sdk](../README.md) / [Modules](../modules.md) / core/schemas/builders/object/types

# Module: core/schemas/builders/object/types

## Table of contents

### Interfaces

- [BaseObjectSchema](../interfaces/core_schemas_builders_object_types.BaseObjectSchema.md)
- [ObjectUtils](../interfaces/core_schemas_builders_object_types.ObjectUtils.md)

### Type Aliases

- [ObjectSchema](core_schemas_builders_object_types.md#objectschema)
- [PropertySchemas](core_schemas_builders_object_types.md#propertyschemas)
- [inferObjectSchemaFromPropertySchemas](core_schemas_builders_object_types.md#inferobjectschemafrompropertyschemas)
- [inferParsedObject](core_schemas_builders_object_types.md#inferparsedobject)
- [inferParsedObjectFromPropertySchemas](core_schemas_builders_object_types.md#inferparsedobjectfrompropertyschemas)
- [inferParsedPropertySchema](core_schemas_builders_object_types.md#inferparsedpropertyschema)
- [inferRawKey](core_schemas_builders_object_types.md#inferrawkey)
- [inferRawObject](core_schemas_builders_object_types.md#inferrawobject)
- [inferRawObjectFromPropertySchemas](core_schemas_builders_object_types.md#inferrawobjectfrompropertyschemas)
- [inferRawPropertySchema](core_schemas_builders_object_types.md#inferrawpropertyschema)

## Type Aliases

### ObjectSchema

Ƭ **ObjectSchema**\<`Raw`, `Parsed`\>: [`BaseObjectSchema`](../interfaces/core_schemas_builders_object_types.BaseObjectSchema.md)\<`Raw`, `Parsed`\> & [`ObjectLikeUtils`](../interfaces/core_schemas_builders_object_like_types.ObjectLikeUtils.md)\<`Raw`, `Parsed`\> & [`ObjectUtils`](../interfaces/core_schemas_builders_object_types.ObjectUtils.md)\<`Raw`, `Parsed`\> & [`SchemaUtils`](../interfaces/core_schemas_builders_schema_utils_getSchemaUtils.SchemaUtils.md)\<`Raw`, `Parsed`\>

#### Type parameters

| Name |
| :------ |
| `Raw` |
| `Parsed` |

#### Defined in

[src/api/core/schemas/builders/object/types.d.ts:6](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/types.d.ts#L6)

___

### PropertySchemas

Ƭ **PropertySchemas**\<`ParsedKeys`\>: `Record`\<`ParsedKeys`, [`Property`](../interfaces/core_schemas_builders_object_property.Property.md)\<`any`, `any`, `any`\> \| [`Schema`](core_schemas_Schema.md#schema)\<`any`, `any`\>\>

#### Type parameters

| Name | Type |
| :------ | :------ |
| `ParsedKeys` | extends `string` \| `number` \| `symbol` |

#### Defined in

[src/api/core/schemas/builders/object/types.d.ts:42](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/types.d.ts#L42)

___

### inferObjectSchemaFromPropertySchemas

Ƭ **inferObjectSchemaFromPropertySchemas**\<`T`\>: [`ObjectSchema`](core_schemas_builders_object_types.md#objectschema)\<[`inferRawObjectFromPropertySchemas`](core_schemas_builders_object_types.md#inferrawobjectfrompropertyschemas)\<`T`\>, [`inferParsedObjectFromPropertySchemas`](core_schemas_builders_object_types.md#inferparsedobjectfrompropertyschemas)\<`T`\>\>

#### Type parameters

| Name | Type |
| :------ | :------ |
| `T` | extends [`PropertySchemas`](core_schemas_builders_object_types.md#propertyschemas)\<keyof `T`\> |

#### Defined in

[src/api/core/schemas/builders/object/types.d.ts:23](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/types.d.ts#L23)

___

### inferParsedObject

Ƭ **inferParsedObject**\<`O`\>: `O` extends [`ObjectSchema`](core_schemas_builders_object_types.md#objectschema)\<`any`, infer Parsed\> ? `Parsed` : `never`

#### Type parameters

| Name | Type |
| :------ | :------ |
| `O` | extends [`ObjectSchema`](core_schemas_builders_object_types.md#objectschema)\<`any`, `any`\> |

#### Defined in

[src/api/core/schemas/builders/object/types.d.ts:21](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/types.d.ts#L21)

___

### inferParsedObjectFromPropertySchemas

Ƭ **inferParsedObjectFromPropertySchemas**\<`T`\>: [`addQuestionMarksToNullableProperties`](core_schemas_utils_addQuestionMarksToNullableProperties.md#addquestionmarkstonullableproperties)\<\{ [K in keyof T]: inferParsedPropertySchema\<T[K]\> }\>

#### Type parameters

| Name | Type |
| :------ | :------ |
| `T` | extends [`PropertySchemas`](core_schemas_builders_object_types.md#propertyschemas)\<keyof `T`\> |

#### Defined in

[src/api/core/schemas/builders/object/types.d.ts:37](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/types.d.ts#L37)

___

### inferParsedPropertySchema

Ƭ **inferParsedPropertySchema**\<`P`\>: `P` extends [`Property`](../interfaces/core_schemas_builders_object_property.Property.md)\<`any`, `any`, infer Parsed\> ? `Parsed` : `P` extends [`Schema`](core_schemas_Schema.md#schema)\<`any`, `any`\> ? [`inferParsed`](core_schemas_Schema.md#inferparsed)\<`P`\> : `never`

#### Type parameters

| Name | Type |
| :------ | :------ |
| `P` | extends [`Property`](../interfaces/core_schemas_builders_object_property.Property.md)\<`any`, `any`, `any`\> \| [`Schema`](core_schemas_Schema.md#schema)\<`any`, `any`\> |

#### Defined in

[src/api/core/schemas/builders/object/types.d.ts:53](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/types.d.ts#L53)

___

### inferRawKey

Ƭ **inferRawKey**\<`ParsedKey`, `P`\>: `P` extends [`Property`](../interfaces/core_schemas_builders_object_property.Property.md)\<infer Raw, `any`, `any`\> ? `Raw` : `ParsedKey`

#### Type parameters

| Name | Type |
| :------ | :------ |
| `ParsedKey` | extends `string` \| `number` \| `symbol` |
| `P` | extends [`Property`](../interfaces/core_schemas_builders_object_property.Property.md)\<`any`, `any`, `any`\> \| [`Schema`](core_schemas_Schema.md#schema)\<`any`, `any`\> |

#### Defined in

[src/api/core/schemas/builders/object/types.d.ts:61](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/types.d.ts#L61)

___

### inferRawObject

Ƭ **inferRawObject**\<`O`\>: `O` extends [`ObjectSchema`](core_schemas_builders_object_types.md#objectschema)\<infer Raw, `any`\> ? `Raw` : `never`

#### Type parameters

| Name | Type |
| :------ | :------ |
| `O` | extends [`ObjectSchema`](core_schemas_builders_object_types.md#objectschema)\<`any`, `any`\> |

#### Defined in

[src/api/core/schemas/builders/object/types.d.ts:19](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/types.d.ts#L19)

___

### inferRawObjectFromPropertySchemas

Ƭ **inferRawObjectFromPropertySchemas**\<`T`\>: [`addQuestionMarksToNullableProperties`](core_schemas_utils_addQuestionMarksToNullableProperties.md#addquestionmarkstonullableproperties)\<\{ [ParsedKey in keyof T as inferRawKey\<ParsedKey, T[ParsedKey]\>]: inferRawPropertySchema\<T[ParsedKey]\> }\>

#### Type parameters

| Name | Type |
| :------ | :------ |
| `T` | extends [`PropertySchemas`](core_schemas_builders_object_types.md#propertyschemas)\<keyof `T`\> |

#### Defined in

[src/api/core/schemas/builders/object/types.d.ts:29](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/types.d.ts#L29)

___

### inferRawPropertySchema

Ƭ **inferRawPropertySchema**\<`P`\>: `P` extends [`Property`](../interfaces/core_schemas_builders_object_property.Property.md)\<`any`, infer Raw, `any`\> ? `Raw` : `P` extends [`Schema`](core_schemas_Schema.md#schema)\<`any`, `any`\> ? [`inferRaw`](core_schemas_Schema.md#inferraw)\<`P`\> : `never`

#### Type parameters

| Name | Type |
| :------ | :------ |
| `P` | extends [`Property`](../interfaces/core_schemas_builders_object_property.Property.md)\<`any`, `any`, `any`\> \| [`Schema`](core_schemas_Schema.md#schema)\<`any`, `any`\> |

#### Defined in

[src/api/core/schemas/builders/object/types.d.ts:45](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/types.d.ts#L45)
