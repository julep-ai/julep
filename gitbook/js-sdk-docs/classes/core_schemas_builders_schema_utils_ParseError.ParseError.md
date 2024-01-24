[@julep/sdk](../README.md) / [Modules](../modules.md) / [core/schemas/builders/schema-utils/ParseError](../modules/core_schemas_builders_schema_utils_ParseError.md) / ParseError

# Class: ParseError

[core/schemas/builders/schema-utils/ParseError](../modules/core_schemas_builders_schema_utils_ParseError.md).ParseError

## Hierarchy

- `Error`

  ↳ **`ParseError`**

## Table of contents

### Constructors

- [constructor](core_schemas_builders_schema_utils_ParseError.ParseError.md#constructor)

### Properties

- [cause](core_schemas_builders_schema_utils_ParseError.ParseError.md#cause)
- [errors](core_schemas_builders_schema_utils_ParseError.ParseError.md#errors)
- [message](core_schemas_builders_schema_utils_ParseError.ParseError.md#message)
- [name](core_schemas_builders_schema_utils_ParseError.ParseError.md#name)
- [stack](core_schemas_builders_schema_utils_ParseError.ParseError.md#stack)

## Constructors

### constructor

• **new ParseError**(`errors`): [`ParseError`](core_schemas_builders_schema_utils_ParseError.ParseError.md)

#### Parameters

| Name | Type |
| :------ | :------ |
| `errors` | [`ValidationError`](../interfaces/core_schemas_Schema.ValidationError.md)[] |

#### Returns

[`ParseError`](core_schemas_builders_schema_utils_ParseError.ParseError.md)

#### Overrides

Error.constructor

#### Defined in

[src/api/core/schemas/builders/schema-utils/ParseError.d.ts:4](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/schema-utils/ParseError.d.ts#L4)

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

[src/api/core/schemas/builders/schema-utils/ParseError.d.ts:3](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/schema-utils/ParseError.d.ts#L3)

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
