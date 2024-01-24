[@julep/sdk](../README.md) / [Modules](../modules.md) / [core/schemas/Schema](../modules/core_schemas_Schema.md) / SchemaOptions

# Interface: SchemaOptions

[core/schemas/Schema](../modules/core_schemas_Schema.md).SchemaOptions

## Table of contents

### Properties

- [allowUnrecognizedEnumValues](core_schemas_Schema.SchemaOptions.md#allowunrecognizedenumvalues)
- [allowUnrecognizedUnionMembers](core_schemas_Schema.SchemaOptions.md#allowunrecognizedunionmembers)
- [breadcrumbsPrefix](core_schemas_Schema.SchemaOptions.md#breadcrumbsprefix)
- [skipValidation](core_schemas_Schema.SchemaOptions.md#skipvalidation)
- [unrecognizedObjectKeys](core_schemas_Schema.SchemaOptions.md#unrecognizedobjectkeys)

## Properties

### allowUnrecognizedEnumValues

• `Optional` **allowUnrecognizedEnumValues**: `boolean`

whether to fail when an unrecognized enum value is encountered

**`Default`**

```ts
false
```

#### Defined in

[src/api/core/schemas/Schema.d.ts:74](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/Schema.d.ts#L74)

___

### allowUnrecognizedUnionMembers

• `Optional` **allowUnrecognizedUnionMembers**: `boolean`

whether to fail when an unrecognized discriminant value is
encountered in a union

**`Default`**

```ts
false
```

#### Defined in

[src/api/core/schemas/Schema.d.ts:68](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/Schema.d.ts#L68)

___

### breadcrumbsPrefix

• `Optional` **breadcrumbsPrefix**: `string`[]

each validation failure contains a "path" property, which is
the breadcrumbs to the offending node in the JSON. you can supply
a prefix that is prepended to all the errors' paths. this can be
helpful for zurg's internal debug logging.

#### Defined in

[src/api/core/schemas/Schema.d.ts:92](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/Schema.d.ts#L92)

___

### skipValidation

• `Optional` **skipValidation**: `boolean`

whether to allow data that doesn't conform to the schema.
invalid data is passed through without transformation.

when this is enabled, .parse() and .json() will always
return `ok: true`. `.parseOrThrow()` and `.jsonOrThrow()`
will never fail.

**`Default`**

```ts
false
```

#### Defined in

[src/api/core/schemas/Schema.d.ts:85](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/Schema.d.ts#L85)

___

### unrecognizedObjectKeys

• `Optional` **unrecognizedObjectKeys**: ``"fail"`` \| ``"passthrough"`` \| ``"strip"``

how to handle unrecognized keys in objects

**`Default`**

```ts
"fail"
```

#### Defined in

[src/api/core/schemas/Schema.d.ts:61](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/Schema.d.ts#L61)
