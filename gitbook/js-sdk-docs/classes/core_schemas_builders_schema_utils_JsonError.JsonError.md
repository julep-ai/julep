[@julep/sdk](../README.md) / [Modules](../modules.md) / [core/schemas/builders/schema-utils/JsonError](../modules/core_schemas_builders_schema_utils_JsonError.md) / JsonError

# Class: JsonError

[core/schemas/builders/schema-utils/JsonError](../modules/core_schemas_builders_schema_utils_JsonError.md).JsonError

## Hierarchy

- `Error`

  ↳ **`JsonError`**

## Table of contents

### Constructors

- [constructor](core_schemas_builders_schema_utils_JsonError.JsonError.md#constructor)

### Properties

- [cause](core_schemas_builders_schema_utils_JsonError.JsonError.md#cause)
- [errors](core_schemas_builders_schema_utils_JsonError.JsonError.md#errors)
- [message](core_schemas_builders_schema_utils_JsonError.JsonError.md#message)
- [name](core_schemas_builders_schema_utils_JsonError.JsonError.md#name)
- [stack](core_schemas_builders_schema_utils_JsonError.JsonError.md#stack)

## Constructors

### constructor

• **new JsonError**(`errors`): [`JsonError`](core_schemas_builders_schema_utils_JsonError.JsonError.md)

#### Parameters

| Name | Type |
| :------ | :------ |
| `errors` | [`ValidationError`](../interfaces/core_schemas_Schema.ValidationError.md)[] |

#### Returns

[`JsonError`](core_schemas_builders_schema_utils_JsonError.JsonError.md)

#### Overrides

Error.constructor

#### Defined in

[src/api/core/schemas/builders/schema-utils/JsonError.d.ts:4](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/schema-utils/JsonError.d.ts#L4)

## Properties

### cause

• `Optional` **cause**: `unknown`

#### Inherited from

Error.cause

#### Defined in

node_modules/typescript/lib/lib.es2022.error.d.ts:24

___

### errors

• `Readonly` **errors**: [`ValidationError`](../interfaces/core_schemas_Schema.ValidationError.md)[]

#### Defined in

[src/api/core/schemas/builders/schema-utils/JsonError.d.ts:3](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/schema-utils/JsonError.d.ts#L3)

___

### message

• **message**: `string`

#### Inherited from

Error.message

#### Defined in

node_modules/typescript/lib/lib.es5.d.ts:1076

___

### name

• **name**: `string`

#### Inherited from

Error.name

#### Defined in

node_modules/typescript/lib/lib.es5.d.ts:1075

___

### stack

• `Optional` **stack**: `string`

#### Inherited from

Error.stack

#### Defined in

node_modules/typescript/lib/lib.es5.d.ts:1077
