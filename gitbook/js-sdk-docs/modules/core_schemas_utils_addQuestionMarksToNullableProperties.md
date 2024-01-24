[@julep/sdk](../README.md) / [Modules](../modules.md) / core/schemas/utils/addQuestionMarksToNullableProperties

# Module: core/schemas/utils/addQuestionMarksToNullableProperties

## Table of contents

### Type Aliases

- [OptionalKeys](core_schemas_utils_addQuestionMarksToNullableProperties.md#optionalkeys)
- [RequiredKeys](core_schemas_utils_addQuestionMarksToNullableProperties.md#requiredkeys)
- [addQuestionMarksToNullableProperties](core_schemas_utils_addQuestionMarksToNullableProperties.md#addquestionmarkstonullableproperties)

## Type Aliases

### OptionalKeys

Ƭ **OptionalKeys**\<`T`\>: \{ [K in keyof T]-?: undefined extends T[K] ? K : null extends T[K] ? K : 1 extends (any extends T[K] ? 0 : 1) ? never : K }[keyof `T`]

#### Type parameters

| Name |
| :------ |
| `T` |

#### Defined in

[src/api/core/schemas/utils/addQuestionMarksToNullableProperties.d.ts:4](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/utils/addQuestionMarksToNullableProperties.d.ts#L4)

___

### RequiredKeys

Ƭ **RequiredKeys**\<`T`\>: `Exclude`\<keyof `T`, [`OptionalKeys`](core_schemas_utils_addQuestionMarksToNullableProperties.md#optionalkeys)\<`T`\>\>

#### Type parameters

| Name |
| :------ |
| `T` |

#### Defined in

[src/api/core/schemas/utils/addQuestionMarksToNullableProperties.d.ts:13](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/utils/addQuestionMarksToNullableProperties.d.ts#L13)

___

### addQuestionMarksToNullableProperties

Ƭ **addQuestionMarksToNullableProperties**\<`T`\>: \{ [K in OptionalKeys\<T\>]?: T[K] } & `Pick`\<`T`, [`RequiredKeys`](core_schemas_utils_addQuestionMarksToNullableProperties.md#requiredkeys)\<`T`\>\>

#### Type parameters

| Name |
| :------ |
| `T` |

#### Defined in

[src/api/core/schemas/utils/addQuestionMarksToNullableProperties.d.ts:1](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/utils/addQuestionMarksToNullableProperties.d.ts#L1)
