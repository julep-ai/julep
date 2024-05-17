[@julep/sdk](../README.md) / [Exports](../modules.md) / api/models/ChatMLMessage

# Module: api/models/ChatMLMessage

## Table of contents

### Type Aliases

- [ChatMLMessage](api_models_ChatMLMessage.md#chatmlmessage)

## Type Aliases

### ChatMLMessage

Ƭ **ChatMLMessage**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `content` | `string` | ChatML content |
| `created_at` | `string` | Message created at (RFC-3339 format) |
| `id` | `string` | Message ID |
| `name?` | `string` | ChatML name |
| `role` | ``"user"`` \| ``"assistant"`` \| ``"system"`` \| ``"function_call"`` \| ``"function"`` | ChatML role (system\|assistant\|user\|function_call\|function) |

#### Defined in

[src/api/models/ChatMLMessage.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/models/ChatMLMessage.ts#L5)
