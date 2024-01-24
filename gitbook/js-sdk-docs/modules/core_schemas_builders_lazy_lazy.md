[@julep/sdk](../README.md) / [Modules](../modules.md) / core/schemas/builders/lazy/lazy

# Module: core/schemas/builders/lazy/lazy

## Table of contents

### Type Aliases

- [SchemaGetter](core_schemas_builders_lazy_lazy.md#schemagetter)

### Functions

- [constructLazyBaseSchema](core_schemas_builders_lazy_lazy.md#constructlazybaseschema)
- [getMemoizedSchema](core_schemas_builders_lazy_lazy.md#getmemoizedschema)
- [lazy](core_schemas_builders_lazy_lazy.md#lazy)

## Type Aliases

### SchemaGetter

Ƭ **SchemaGetter**\<`SchemaType`\>: () => `SchemaType` \| `Promise`\<`SchemaType`\>

#### Type parameters

| Name | Type |
| :------ | :------ |
| `SchemaType` | extends [`Schema`](core_schemas_Schema.md#schema)\<`any`, `any`\> |

#### Type declaration

▸ (): `SchemaType` \| `Promise`\<`SchemaType`\>

##### Returns

`SchemaType` \| `Promise`\<`SchemaType`\>

#### Defined in

[src/api/core/schemas/builders/lazy/lazy.d.ts:2](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/lazy/lazy.d.ts#L2)

## Functions

### constructLazyBaseSchema

▸ **constructLazyBaseSchema**\<`Raw`, `Parsed`\>(`getter`): [`BaseSchema`](../interfaces/core_schemas_Schema.BaseSchema.md)\<`Raw`, `Parsed`\>

#### Type parameters

| Name |
| :------ |
| `Raw` |
| `Parsed` |

#### Parameters

| Name | Type |
| :------ | :------ |
| `getter` | [`SchemaGetter`](core_schemas_builders_lazy_lazy.md#schemagetter)\<[`Schema`](core_schemas_Schema.md#schema)\<`Raw`, `Parsed`\>\> |

#### Returns

[`BaseSchema`](../interfaces/core_schemas_Schema.BaseSchema.md)\<`Raw`, `Parsed`\>

#### Defined in

[src/api/core/schemas/builders/lazy/lazy.d.ts:8](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/lazy/lazy.d.ts#L8)

___

### getMemoizedSchema

▸ **getMemoizedSchema**\<`SchemaType`\>(`getter`): `Promise`\<`SchemaType`\>

#### Type parameters

| Name | Type |
| :------ | :------ |
| `SchemaType` | extends [`Schema`](core_schemas_Schema.md#schema)\<`any`, `any`\> |

#### Parameters

| Name | Type |
| :------ | :------ |
| `getter` | [`SchemaGetter`](core_schemas_builders_lazy_lazy.md#schemagetter)\<`SchemaType`\> |

#### Returns

`Promise`\<`SchemaType`\>

#### Defined in

[src/api/core/schemas/builders/lazy/lazy.d.ts:11](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/lazy/lazy.d.ts#L11)

___

### lazy

▸ **lazy**\<`Raw`, `Parsed`\>(`getter`): [`Schema`](core_schemas_Schema.md#schema)\<`Raw`, `Parsed`\>

#### Type parameters

| Name |
| :------ |
| `Raw` |
| `Parsed` |

#### Parameters

| Name | Type |
| :------ | :------ |
| `getter` | [`SchemaGetter`](core_schemas_builders_lazy_lazy.md#schemagetter)\<[`Schema`](core_schemas_Schema.md#schema)\<`Raw`, `Parsed`\>\> |

#### Returns

[`Schema`](core_schemas_Schema.md#schema)\<`Raw`, `Parsed`\>

#### Defined in

[src/api/core/schemas/builders/lazy/lazy.d.ts:5](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/core/schemas/builders/lazy/lazy.d.ts#L5)
