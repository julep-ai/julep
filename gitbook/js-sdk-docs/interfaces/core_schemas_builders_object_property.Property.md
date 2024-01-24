[@julep/sdk](../README.md) / [Modules](../modules.md) / [core/schemas/builders/object/property](../modules/core_schemas_builders_object_property.md) / Property

# Interface: Property\<RawKey, RawValue, ParsedValue\>

[core/schemas/builders/object/property](../modules/core_schemas_builders_object_property.md).Property

## Type parameters

| Name | Type |
| :------ | :------ |
| `RawKey` | extends `string` |
| `RawValue` | `RawValue` |
| `ParsedValue` | `ParsedValue` |

## Table of contents

### Properties

- [isProperty](core_schemas_builders_object_property.Property.md#isproperty)
- [rawKey](core_schemas_builders_object_property.Property.md#rawkey)
- [valueSchema](core_schemas_builders_object_property.Property.md#valueschema)

## Properties

### isProperty

• **isProperty**: ``true``

#### Defined in

[src/api/core/schemas/builders/object/property.d.ts:9](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/property.d.ts#L9)

___

### rawKey

• **rawKey**: `RawKey`

#### Defined in

[src/api/core/schemas/builders/object/property.d.ts:7](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/property.d.ts#L7)

___

### valueSchema

• **valueSchema**: [`Schema`](../modules/core_schemas_Schema.md#schema)\<`RawValue`, `ParsedValue`\>

#### Defined in

[src/api/core/schemas/builders/object/property.d.ts:8](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/property.d.ts#L8)
