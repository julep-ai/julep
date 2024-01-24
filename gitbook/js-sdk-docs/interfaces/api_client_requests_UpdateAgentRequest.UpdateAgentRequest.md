[@julep/sdk](../README.md) / [Modules](../modules.md) / [api/client/requests/UpdateAgentRequest](../modules/api_client_requests_UpdateAgentRequest.md) / UpdateAgentRequest

# Interface: UpdateAgentRequest

[api/client/requests/UpdateAgentRequest](../modules/api_client_requests_UpdateAgentRequest.md).UpdateAgentRequest

**`Example`**

```ts
{
 *         instructions: [{
 *                 content: "string"
 *             }],
 *         defaultSettings: {
 *             temperature: 1,
 *             topP: 1
 *         }
 *     }
```

## Table of contents

### Properties

- [about](api_client_requests_UpdateAgentRequest.UpdateAgentRequest.md#about)
- [defaultSettings](api_client_requests_UpdateAgentRequest.UpdateAgentRequest.md#defaultsettings)
- [instructions](api_client_requests_UpdateAgentRequest.UpdateAgentRequest.md#instructions)
- [model](api_client_requests_UpdateAgentRequest.UpdateAgentRequest.md#model)
- [name](api_client_requests_UpdateAgentRequest.UpdateAgentRequest.md#name)

## Properties

### about

• `Optional` **about**: `string`

About the agent

#### Defined in

[src/api/api/client/requests/UpdateAgentRequest.d.ts:19](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/client/requests/UpdateAgentRequest.d.ts#L19)

___

### defaultSettings

• `Optional` **defaultSettings**: [`AgentDefaultSettings`](api_types_AgentDefaultSettings.AgentDefaultSettings.md)

Default model settings to start every session with

#### Defined in

[src/api/api/client/requests/UpdateAgentRequest.d.ts:27](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/client/requests/UpdateAgentRequest.d.ts#L27)

___

### instructions

• `Optional` **instructions**: [`Instruction`](api_types_Instruction.Instruction.md)[]

List of instructions for the agent

#### Defined in

[src/api/api/client/requests/UpdateAgentRequest.d.ts:21](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/client/requests/UpdateAgentRequest.d.ts#L21)

___

### model

• `Optional` **model**: `string`

Name of the model that the agent is supposed to use

#### Defined in

[src/api/api/client/requests/UpdateAgentRequest.d.ts:25](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/client/requests/UpdateAgentRequest.d.ts#L25)

___

### name

• `Optional` **name**: `string`

Name of the agent

#### Defined in

[src/api/api/client/requests/UpdateAgentRequest.d.ts:23](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/client/requests/UpdateAgentRequest.d.ts#L23)
