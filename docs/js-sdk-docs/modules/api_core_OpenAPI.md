[@julep/sdk](../README.md) / [Exports](../modules.md) / api/core/OpenAPI

# Module: api/core/OpenAPI

## Table of contents

### Type Aliases

- [OpenAPIConfig](api_core_OpenAPI.md#openapiconfig)

### Variables

- [OpenAPI](api_core_OpenAPI.md#openapi)

## Type Aliases

### OpenAPIConfig

Ƭ **OpenAPIConfig**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `BASE` | `string` |
| `CREDENTIALS` | ``"include"`` \| ``"omit"`` \| ``"same-origin"`` |
| `ENCODE_PATH?` | (`path`: `string`) => `string` |
| `HEADERS?` | `Headers` \| `Resolver`\<`Headers`\> |
| `PASSWORD?` | `string` \| `Resolver`\<`string`\> |
| `TOKEN?` | `string` \| `Resolver`\<`string`\> |
| `USERNAME?` | `string` \| `Resolver`\<`string`\> |
| `VERSION` | `string` |
| `WITH_CREDENTIALS` | `boolean` |

#### Defined in

[src/api/core/OpenAPI.ts:10](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/OpenAPI.ts#L10)

## Variables

### OpenAPI

• `Const` **OpenAPI**: [`OpenAPIConfig`](api_core_OpenAPI.md#openapiconfig)

#### Defined in

[src/api/core/OpenAPI.ts:22](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/core/OpenAPI.ts#L22)
