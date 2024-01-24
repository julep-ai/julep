[@julep/sdk](../README.md) / [Modules](../modules.md) / [core/schemas/Schema](../modules/core_schemas_Schema.md) / BaseSchema

# Interface: BaseSchema\<Raw, Parsed\>

[core/schemas/Schema](../modules/core_schemas_Schema.md).BaseSchema

## Type parameters

| Name |
| :------ |
| `Raw` |
| `Parsed` |

## Hierarchy

- **`BaseSchema`**

  ↳ [`BaseObjectSchema`](core_schemas_builders_object_types.BaseObjectSchema.md)

## Table of contents

### Properties

- [getType](core_schemas_Schema.BaseSchema.md#gettype)
- [json](core_schemas_Schema.BaseSchema.md#json)
- [parse](core_schemas_Schema.BaseSchema.md#parse)

## Properties

### getType

• **getType**: () => [`SchemaType`](../modules/core_schemas_Schema.md#schematype) \| `Promise`\<[`SchemaType`](../modules/core_schemas_Schema.md#schematype)\>

#### Type declaration

▸ (): [`SchemaType`](../modules/core_schemas_Schema.md#schematype) \| `Promise`\<[`SchemaType`](../modules/core_schemas_Schema.md#schematype)\>

##### Returns

[`SchemaType`](../modules/core_schemas_Schema.md#schematype) \| `Promise`\<[`SchemaType`](../modules/core_schemas_Schema.md#schematype)\>

#### Defined in

[src/api/core/schemas/Schema.d.ts:21](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/Schema.d.ts#L21)

___

### json

• **json**: (`parsed`: `unknown`, `opts?`: [`SchemaOptions`](core_schemas_Schema.SchemaOptions.md)) => [`MaybePromise`](../modules/core_schemas_utils_MaybePromise.md#maybepromise)\<[`MaybeValid`](../modules/core_schemas_Schema.md#maybevalid)\<`Raw`\>\>

#### Type declaration

▸ (`parsed`, `opts?`): [`MaybePromise`](../modules/core_schemas_utils_MaybePromise.md#maybepromise)\<[`MaybeValid`](../modules/core_schemas_Schema.md#maybevalid)\<`Raw`\>\>

##### Parameters

| Name | Type |
| :------ | :------ |
| `parsed` | `unknown` |
| `opts?` | [`SchemaOptions`](core_schemas_Schema.SchemaOptions.md) |

##### Returns

[`MaybePromise`](../modules/core_schemas_utils_MaybePromise.md#maybepromise)\<[`MaybeValid`](../modules/core_schemas_Schema.md#maybevalid)\<`Raw`\>\>

#### Defined in

[src/api/core/schemas/Schema.d.ts:17](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/Schema.d.ts#L17)

___

### parse

• **parse**: (`raw`: `unknown`, `opts?`: [`SchemaOptions`](core_schemas_Schema.SchemaOptions.md)) => [`MaybePromise`](../modules/core_schemas_utils_MaybePromise.md#maybepromise)\<[`MaybeValid`](../modules/core_schemas_Schema.md#maybevalid)\<`Parsed`\>\>

#### Type declaration

▸ (`raw`, `opts?`): [`MaybePromise`](../modules/core_schemas_utils_MaybePromise.md#maybepromise)\<[`MaybeValid`](../modules/core_schemas_Schema.md#maybevalid)\<`Parsed`\>\>

##### Parameters

| Name | Type |
| :------ | :------ |
| `raw` | `unknown` |
| `opts?` | [`SchemaOptions`](core_schemas_Schema.SchemaOptions.md) |

##### Returns

[`MaybePromise`](../modules/core_schemas_utils_MaybePromise.md#maybepromise)\<[`MaybeValid`](../modules/core_schemas_Schema.md#maybevalid)\<`Parsed`\>\>

#### Defined in

[src/api/core/schemas/Schema.d.ts:13](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/Schema.d.ts#L13)
