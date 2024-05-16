[@julep/sdk](../README.md) / [Exports](../modules.md) / api/models/Agent

# Module: api/models/Agent

## Table of contents

### Type Aliases

- [Agent](api_models_Agent.md#agent)

## Type Aliases

### Agent

Ƭ **Agent**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `about?` | `string` | About the agent |
| `created_at?` | `string` | Agent created at (RFC-3339 format) |
| `default_settings?` | [`AgentDefaultSettings`](api_models_AgentDefaultSettings.md#agentdefaultsettings) | Default settings for all sessions created by this agent |
| `id` | `string` | Agent id (UUID) |
| `instructions?` | `string` \| `string`[] | Instructions for the agent |
| `metadata?` | `any` | Optional metadata |
| `model` | `string` | The model to use with this agent |
| `name` | `string` | Name of the agent |
| `updated_at?` | `string` | Agent updated at (RFC-3339 format) |

#### Defined in

[src/api/models/Agent.ts:6](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/models/Agent.ts#L6)
