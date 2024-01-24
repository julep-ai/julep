[@julep/sdk](../README.md) / [Modules](../modules.md) / core/schemas/builders/object-like/getObjectLikeUtils

# Module: core/schemas/builders/object-like/getObjectLikeUtils

## Table of contents

### Functions

- [getObjectLikeUtils](core_schemas_builders_object_like_getObjectLikeUtils.md#getobjectlikeutils)
- [withParsedProperties](core_schemas_builders_object_like_getObjectLikeUtils.md#withparsedproperties)

## Functions

### getObjectLikeUtils

▸ **getObjectLikeUtils**\<`Raw`, `Parsed`\>(`schema`): [`ObjectLikeUtils`](../interfaces/core_schemas_builders_object_like_types.ObjectLikeUtils.md)\<`Raw`, `Parsed`\>

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

[`ObjectLikeUtils`](../interfaces/core_schemas_builders_object_like_types.ObjectLikeUtils.md)\<`Raw`, `Parsed`\>

#### Defined in

[src/api/core/schemas/builders/object-like/getObjectLikeUtils.d.ts:3](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object-like/getObjectLikeUtils.d.ts#L3)

___

### withParsedProperties

▸ **withParsedProperties**\<`RawObjectShape`, `ParsedObjectShape`, `Properties`\>(`objectLike`, `properties`): [`ObjectLikeSchema`](core_schemas_builders_object_like_types.md#objectlikeschema)\<`RawObjectShape`, `ParsedObjectShape` & `Properties`\>

object-like utils are defined in one file to resolve issues with circular imports

#### Type parameters

| Name |
| :------ |
| `RawObjectShape` |
| `ParsedObjectShape` |
| `Properties` |

#### Parameters

| Name | Type |
| :------ | :------ |
| `objectLike` | [`BaseSchema`](../interfaces/core_schemas_Schema.BaseSchema.md)\<`RawObjectShape`, `ParsedObjectShape`\> |
| `properties` | \{ [K in string \| number \| symbol]: Properties[K] \| Function } |

#### Returns

[`ObjectLikeSchema`](core_schemas_builders_object_like_types.md#objectlikeschema)\<`RawObjectShape`, `ParsedObjectShape` & `Properties`\>

#### Defined in

[src/api/core/schemas/builders/object-like/getObjectLikeUtils.d.ts:9](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object-like/getObjectLikeUtils.d.ts#L9)
