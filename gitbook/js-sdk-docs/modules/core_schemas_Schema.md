[@julep/sdk](../README.md) / [Modules](../modules.md) / core/schemas/Schema

# Module: core/schemas/Schema

## Table of contents

### Interfaces

- [BaseSchema](../interfaces/core_schemas_Schema.BaseSchema.md)
- [Invalid](../interfaces/core_schemas_Schema.Invalid.md)
- [SchemaOptions](../interfaces/core_schemas_Schema.SchemaOptions.md)
- [Valid](../interfaces/core_schemas_Schema.Valid.md)
- [ValidationError](../interfaces/core_schemas_Schema.ValidationError.md)

### Type Aliases

- [MaybeValid](core_schemas_Schema.md#maybevalid)
- [Schema](core_schemas_Schema.md#schema)
- [SchemaType](core_schemas_Schema.md#schematype)
- [inferParsed](core_schemas_Schema.md#inferparsed)
- [inferRaw](core_schemas_Schema.md#inferraw)

### Variables

- [SchemaType](core_schemas_Schema.md#schematype-1)

## Type Aliases

### MaybeValid

Ƭ **MaybeValid**\<`T`\>: [`Valid`](../interfaces/core_schemas_Schema.Valid.md)\<`T`\> \| [`Invalid`](../interfaces/core_schemas_Schema.Invalid.md)

#### Type parameters

| Name |
| :------ |
| `T` |

#### Defined in

[src/api/core/schemas/Schema.d.ts:42](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/Schema.d.ts#L42)

___

### Schema

Ƭ **Schema**\<`Raw`, `Parsed`\>: [`BaseSchema`](../interfaces/core_schemas_Schema.BaseSchema.md)\<`Raw`, `Parsed`\> & [`SchemaUtils`](../interfaces/core_schemas_builders_schema_utils_getSchemaUtils.SchemaUtils.md)\<`Raw`, `Parsed`\>

#### Type parameters

| Name | Type |
| :------ | :------ |
| `Raw` | `unknown` |
| `Parsed` | `unknown` |

#### Defined in

[src/api/core/schemas/Schema.d.ts:3](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/Schema.d.ts#L3)

___

### SchemaType

Ƭ **SchemaType**: typeof [`SchemaType`](core_schemas_Schema.md#schematype-1)[keyof typeof [`SchemaType`](core_schemas_Schema.md#schematype-1)]

#### Defined in

[src/api/core/schemas/Schema.d.ts:23](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/Schema.d.ts#L23)

[src/api/core/schemas/Schema.d.ts:41](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/Schema.d.ts#L41)

___

### inferParsed

Ƭ **inferParsed**\<`S`\>: `S` extends [`Schema`](core_schemas_Schema.md#schema)\<`any`, infer Parsed\> ? `Parsed` : `never`

#### Type parameters

| Name | Type |
| :------ | :------ |
| `S` | extends [`Schema`](core_schemas_Schema.md#schema) |

#### Defined in

[src/api/core/schemas/Schema.d.ts:10](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/Schema.d.ts#L10)

___

### inferRaw

Ƭ **inferRaw**\<`S`\>: `S` extends [`Schema`](core_schemas_Schema.md#schema)\<infer Raw, `any`\> ? `Raw` : `never`

#### Type parameters

| Name | Type |
| :------ | :------ |
| `S` | extends [`Schema`](core_schemas_Schema.md#schema) |

#### Defined in

[src/api/core/schemas/Schema.d.ts:8](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/Schema.d.ts#L8)

## Variables

### SchemaType

• `Const` **SchemaType**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `ANY` | ``"any"`` |
| `BOOLEAN` | ``"boolean"`` |
| `BOOLEAN_LITERAL` | ``"booleanLiteral"`` |
| `DATE` | ``"date"`` |
| `ENUM` | ``"enum"`` |
| `LIST` | ``"list"`` |
| `NUMBER` | ``"number"`` |
| `OBJECT` | ``"object"`` |
| `OPTIONAL` | ``"optional"`` |
| `RECORD` | ``"record"`` |
| `SET` | ``"set"`` |
| `STRING` | ``"string"`` |
| `STRING_LITERAL` | ``"stringLiteral"`` |
| `UNDISCRIMINATED_UNION` | ``"undiscriminatedUnion"`` |
| `UNION` | ``"union"`` |
| `UNKNOWN` | ``"unknown"`` |

#### Defined in

[src/api/core/schemas/Schema.d.ts:23](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/Schema.d.ts#L23)

[src/api/core/schemas/Schema.d.ts:41](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/Schema.d.ts#L41)
