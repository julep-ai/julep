[@julep/sdk](../README.md) / [Modules](../modules.md) / core/schemas/builders/object/property

# Module: core/schemas/builders/object/property

## Table of contents

### Interfaces

- [Property](../interfaces/core_schemas_builders_object_property.Property.md)

### Functions

- [isProperty](core_schemas_builders_object_property.md#isproperty)
- [property](core_schemas_builders_object_property.md#property)

## Functions

### isProperty

▸ **isProperty**\<`O`\>(`maybeProperty`): maybeProperty is O

#### Type parameters

| Name | Type |
| :------ | :------ |
| `O` | extends [`Property`](../interfaces/core_schemas_builders_object_property.Property.md)\<`any`, `any`, `any`\> |

#### Parameters

| Name | Type |
| :------ | :------ |
| `maybeProperty` | `unknown` |

#### Returns

maybeProperty is O

#### Defined in

[src/api/core/schemas/builders/object/property.d.ts:11](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/property.d.ts#L11)

___

### property

▸ **property**\<`RawKey`, `RawValue`, `ParsedValue`\>(`rawKey`, `valueSchema`): [`Property`](../interfaces/core_schemas_builders_object_property.Property.md)\<`RawKey`, `RawValue`, `ParsedValue`\>

#### Type parameters

| Name | Type |
| :------ | :------ |
| `RawKey` | extends `string` |
| `RawValue` | `RawValue` |
| `ParsedValue` | `ParsedValue` |

#### Parameters

| Name | Type |
| :------ | :------ |
| `rawKey` | `RawKey` |
| `valueSchema` | [`Schema`](core_schemas_Schema.md#schema)\<`RawValue`, `ParsedValue`\> |

#### Returns

[`Property`](../interfaces/core_schemas_builders_object_property.Property.md)\<`RawKey`, `RawValue`, `ParsedValue`\>

#### Defined in

[src/api/core/schemas/builders/object/property.d.ts:2](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/property.d.ts#L2)
