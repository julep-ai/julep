[@julep/sdk](../README.md) / [Exports](../modules.md) / api/models/Session

# Module: api/models/Session

## Table of contents

### Type Aliases

- [Session](api_models_Session.md#session)

## Type Aliases

### Session

Ƭ **Session**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `agent_id` | `string` | Agent ID of agent associated with this session |
| `created_at?` | `string` | Session created at (RFC-3339 format) |
| `id` | `string` | Session id (UUID) |
| `metadata?` | `any` | Optional metadata |
| `render_templates?` | `boolean` | Render system and assistant message content as jinja templates |
| `situation?` | `string` | A specific situation that sets the background for this session |
| `summary?` | `string` | (null at the beginning) - generated automatically after every interaction |
| `updated_at?` | `string` | Session updated at (RFC-3339 format) |
| `user_id?` | `string` | User ID of user associated with this session |

#### Defined in

[src/api/models/Session.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/models/Session.ts#L5)
