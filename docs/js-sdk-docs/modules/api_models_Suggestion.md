[@julep/sdk](../README.md) / [Exports](../modules.md) / api/models/Suggestion

# Module: api/models/Suggestion

## Table of contents

### Type Aliases

- [Suggestion](api_models_Suggestion.md#suggestion)

## Type Aliases

### Suggestion

Ƭ **Suggestion**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `content` | `string` | The content of the suggestion |
| `created_at?` | `string` | Suggestion created at (RFC-3339 format) |
| `message_id` | `string` | The message that produced it |
| `session_id` | `string` | Session this suggestion belongs to |
| `target` | ``"user"`` \| ``"agent"`` | Whether the suggestion is for the `agent` or a `user` |

#### Defined in

[src/api/models/Suggestion.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/models/Suggestion.ts#L5)
