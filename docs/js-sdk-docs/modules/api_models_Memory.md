[@julep/sdk](../README.md) / [Exports](../modules.md) / api/models/Memory

# Module: api/models/Memory

## Table of contents

### Type Aliases

- [Memory](api_models_Memory.md#memory)

## Type Aliases

### Memory

Ƭ **Memory**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `agent_id` | `string` | ID of the agent |
| `content` | `string` | Content of the memory |
| `created_at` | `string` | Memory created at (RFC-3339 format) |
| `entities` | `any`[] | List of entities mentioned in the memory |
| `id` | `string` | Memory id (UUID) |
| `last_accessed_at?` | `string` | Memory last accessed at (RFC-3339 format) |
| `sentiment?` | `number` | Sentiment (valence) of the memory on a scale of -1 to 1 |
| `timestamp?` | `string` | Memory happened at (RFC-3339 format) |
| `user_id` | `string` | ID of the user |

#### Defined in

[src/api/models/Memory.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/models/Memory.ts#L5)
