[@julep/sdk](../README.md) / [Modules](../modules.md) / [core/schemas/builders/object/types](../modules/core_schemas_builders_object_types.md) / BaseObjectSchema

# Interface: BaseObjectSchema\<Raw, Parsed\>

[core/schemas/builders/object/types](../modules/core_schemas_builders_object_types.md).BaseObjectSchema

## Type parameters

| Name |
| :------ |
| `Raw` |
| `Parsed` |

## Hierarchy

- [`BaseSchema`](core_schemas_Schema.BaseSchema.md)\<`Raw`, `Parsed`\>

  ↳ **`BaseObjectSchema`**

## Table of contents

### Properties

- [\_getParsedProperties](core_schemas_builders_object_types.BaseObjectSchema.md#_getparsedproperties)
- [\_getRawProperties](core_schemas_builders_object_types.BaseObjectSchema.md#_getrawproperties)
- [getType](core_schemas_builders_object_types.BaseObjectSchema.md#gettype)
- [json](core_schemas_builders_object_types.BaseObjectSchema.md#json)
- [parse](core_schemas_builders_object_types.BaseObjectSchema.md#parse)

## Properties

### \_getParsedProperties

• **\_getParsedProperties**: () => `Promise`\<keyof `Parsed`[]\>

#### Type declaration

▸ (): `Promise`\<keyof `Parsed`[]\>

##### Returns

`Promise`\<keyof `Parsed`[]\>

#### Defined in

[src/api/core/schemas/builders/object/types.d.ts:12](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/types.d.ts#L12)

___

### \_getRawProperties

• **\_getRawProperties**: () => `Promise`\<keyof `Raw`[]\>

#### Type declaration

▸ (): `Promise`\<keyof `Raw`[]\>

##### Returns

`Promise`\<keyof `Raw`[]\>

#### Defined in

[src/api/core/schemas/builders/object/types.d.ts:11](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/types.d.ts#L11)

___

### getType

• **getType**: () => [`SchemaType`](../modules/core_schemas_Schema.md#schematype) \| `Promise`\<[`SchemaType`](../modules/core_schemas_Schema.md#schematype)\>

#### Type declaration

▸ (): [`SchemaType`](../modules/core_schemas_Schema.md#schematype) \| `Promise`\<[`SchemaType`](../modules/core_schemas_Schema.md#schematype)\>

##### Returns

[`SchemaType`](../modules/core_schemas_Schema.md#schematype) \| `Promise`\<[`SchemaType`](../modules/core_schemas_Schema.md#schematype)\>

#### Inherited from

[BaseSchema](core_schemas_Schema.BaseSchema.md).[getType](core_schemas_Schema.BaseSchema.md#gettype)

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

#### Inherited from

[BaseSchema](core_schemas_Schema.BaseSchema.md).[json](core_schemas_Schema.BaseSchema.md#json)

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

#### Inherited from

[BaseSchema](core_schemas_Schema.BaseSchema.md).[parse](core_schemas_Schema.BaseSchema.md#parse)

#### Defined in

[src/api/core/schemas/Schema.d.ts:13](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/Schema.d.ts#L13)
