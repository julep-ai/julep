[@julep/sdk](../README.md) / [Exports](../modules.md) / api/models/UpdateAgentRequest

# Module: api/models/UpdateAgentRequest

## Table of contents

### Type Aliases

- [UpdateAgentRequest](api_models_UpdateAgentRequest.md#updateagentrequest)

## Type Aliases

### UpdateAgentRequest

Ƭ **UpdateAgentRequest**: `Object`

A valid request payload for updating an agent

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `about` | `string` | About the agent |
| `default_settings?` | [`AgentDefaultSettings`](api_models_AgentDefaultSettings.md#agentdefaultsettings) | Default model settings to start every session with |
| `instructions?` | `string` \| `string`[] | Instructions for the agent |
| `metadata?` | `any` | Optional metadata |
| `model?` | `string` | Name of the model that the agent is supposed to use |
| `name` | `string` | Name of the agent |

#### Defined in

[src/api/models/UpdateAgentRequest.ts:9](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/models/UpdateAgentRequest.ts#L9)
