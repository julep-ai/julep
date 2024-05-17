[@julep/sdk](../README.md) / [Exports](../modules.md) / api/models/CreateAgentRequest

# Module: api/models/CreateAgentRequest

## Table of contents

### Type Aliases

- [CreateAgentRequest](api_models_CreateAgentRequest.md#createagentrequest)

## Type Aliases

### CreateAgentRequest

Ƭ **CreateAgentRequest**: `Object`

A valid request payload for creating an agent

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `about?` | `string` | About the agent |
| `default_settings?` | [`AgentDefaultSettings`](api_models_AgentDefaultSettings.md#agentdefaultsettings) | Default model settings to start every session with |
| `docs?` | [`CreateDoc`](api_models_CreateDoc.md#createdoc)[] | List of docs about agent |
| `instructions?` | `string` \| `string`[] | Instructions for the agent |
| `metadata?` | `any` | (Optional) metadata |
| `model?` | `string` | Name of the model that the agent is supposed to use |
| `name` | `string` | Name of the agent |
| `tools?` | [`CreateToolRequest`](api_models_CreateToolRequest.md#createtoolrequest)[] | A list of tools the model may call. Currently, only `function`s are supported as a tool. Use this to provide a list of functions the model may generate JSON inputs for. |

#### Defined in

[src/api/models/CreateAgentRequest.ts:11](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/models/CreateAgentRequest.ts#L11)
