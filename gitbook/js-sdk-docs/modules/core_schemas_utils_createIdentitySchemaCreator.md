[@julep/sdk](../README.md) / [Modules](../modules.md) / core/schemas/utils/createIdentitySchemaCreator

# Module: core/schemas/utils/createIdentitySchemaCreator

## Table of contents

### Functions

- [createIdentitySchemaCreator](core_schemas_utils_createIdentitySchemaCreator.md#createidentityschemacreator)

## Functions

### createIdentitySchemaCreator

▸ **createIdentitySchemaCreator**\<`T`\>(`schemaType`, `validate`): () => [`Schema`](core_schemas_Schema.md#schema)\<`T`, `T`\>

#### Type parameters

| Name |
| :------ |
| `T` |

#### Parameters

| Name | Type |
| :------ | :------ |
| `schemaType` | [`SchemaType`](core_schemas_Schema.md#schematype) |
| `validate` | (`value`: `unknown`, `opts?`: [`SchemaOptions`](../interfaces/core_schemas_Schema.SchemaOptions.md)) => [`MaybeValid`](core_schemas_Schema.md#maybevalid)\<`T`\> |

#### Returns

`fn`

▸ (): [`Schema`](core_schemas_Schema.md#schema)\<`T`, `T`\>

##### Returns

[`Schema`](core_schemas_Schema.md#schema)\<`T`, `T`\>

#### Defined in

[src/api/core/schemas/utils/createIdentitySchemaCreator.d.ts:2](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/utils/createIdentitySchemaCreator.d.ts#L2)
