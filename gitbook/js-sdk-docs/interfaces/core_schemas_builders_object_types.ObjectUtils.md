[@julep/sdk](../README.md) / [Modules](../modules.md) / [core/schemas/builders/object/types](../modules/core_schemas_builders_object_types.md) / ObjectUtils

# Interface: ObjectUtils\<Raw, Parsed\>

[core/schemas/builders/object/types](../modules/core_schemas_builders_object_types.md).ObjectUtils

## Type parameters

| Name |
| :------ |
| `Raw` |
| `Parsed` |

## Table of contents

### Properties

- [extend](core_schemas_builders_object_types.ObjectUtils.md#extend)

## Properties

### extend

• **extend**: \<RawExtension, ParsedExtension\>(`schemas`: [`ObjectSchema`](../modules/core_schemas_builders_object_types.md#objectschema)\<`RawExtension`, `ParsedExtension`\>) => [`ObjectSchema`](../modules/core_schemas_builders_object_types.md#objectschema)\<`Raw` & `RawExtension`, `Parsed` & `ParsedExtension`\>

#### Type declaration

▸ \<`RawExtension`, `ParsedExtension`\>(`schemas`): [`ObjectSchema`](../modules/core_schemas_builders_object_types.md#objectschema)\<`Raw` & `RawExtension`, `Parsed` & `ParsedExtension`\>

##### Type parameters

| Name |
| :------ |
| `RawExtension` |
| `ParsedExtension` |

##### Parameters

| Name | Type |
| :------ | :------ |
| `schemas` | [`ObjectSchema`](../modules/core_schemas_builders_object_types.md#objectschema)\<`RawExtension`, `ParsedExtension`\> |

##### Returns

[`ObjectSchema`](../modules/core_schemas_builders_object_types.md#objectschema)\<`Raw` & `RawExtension`, `Parsed` & `ParsedExtension`\>

#### Defined in

[src/api/core/schemas/builders/object/types.d.ts:15](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/object/types.d.ts#L15)
