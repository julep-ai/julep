[@julep/sdk](../README.md) / [Exports](../modules.md) / api/models/CreateSessionRequest

# Module: api/models/CreateSessionRequest

## Table of contents

### Type Aliases

- [CreateSessionRequest](api_models_CreateSessionRequest.md#createsessionrequest)

## Type Aliases

### CreateSessionRequest

Ƭ **CreateSessionRequest**: `Object`

A valid request payload for creating a session

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `agent_id` | `string` | Agent ID of agent to associate with this session |
| `metadata?` | `any` | Optional metadata |
| `render_templates?` | `boolean` | Render system and assistant message content as jinja templates |
| `situation?` | `string` | A specific situation that sets the background for this session |
| `user_id?` | `string` | (Optional) User ID of user to associate with this session |

#### Defined in

[src/api/models/CreateSessionRequest.ts:8](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/models/CreateSessionRequest.ts#L8)
