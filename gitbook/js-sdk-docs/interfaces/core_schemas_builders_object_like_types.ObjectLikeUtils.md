[@julep/sdk](../README.md) / [Modules](../modules.md) / [core/schemas/builders/object-like/types](../modules/core_schemas_builders_object_like_types.md) / ObjectLikeUtils

# Interface: ObjectLikeUtils\<Raw, Parsed\>

[core/schemas/builders/object-like/types](../modules/core_schemas_builders_object_like_types.md).ObjectLikeUtils

## Type parameters

| Name |
| :------ |
| `Raw` |
| `Parsed` |

## Table of contents

### Properties

- [withParsedProperties](core_schemas_builders_object_like_types.ObjectLikeUtils.md#withparsedproperties)

## Properties

### withParsedProperties

• **withParsedProperties**: \<T\>(`properties`: \{ [K in string \| number \| symbol]: T[K] \| Function }) => [`ObjectLikeSchema`](../modules/core_schemas_builders_object_like_types.md#objectlikeschema)\<`Raw`, `Parsed` & `T`\>

#### Type declaration

▸ \<`T`\>(`properties`): [`ObjectLikeSchema`](../modules/core_schemas_builders_object_like_types.md#objectlikeschema)\<`Raw`, `Parsed` & `T`\>

##### Type parameters

| Name | Type |
| :------ | :------ |
| `T` | extends `Record`\<`string`, `any`\> |

##### Parameters

| Name | Type |
| :------ | :------ |
| `properties` | \{ [K in string \| number \| symbol]: T[K] \| Function } |

##### Returns

[`ObjectLikeSchema`](../modules/core_schemas_builders_object_like_types.md#objectlikeschema)\<`Raw`, `Parsed` & `T`\>

#### Defined in

[src/api/core/schemas/builders/object-like/types.d.ts:6](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object-like/types.d.ts#L6)
