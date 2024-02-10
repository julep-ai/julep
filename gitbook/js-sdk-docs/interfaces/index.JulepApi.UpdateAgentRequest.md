[@julep/sdk](../README.md) / [Modules](../modules.md) / [index](../modules/index.md) / [JulepApi](../modules/index.JulepApi.md) / UpdateAgentRequest

# Interface: UpdateAgentRequest

[index](../modules/index.md).[JulepApi](../modules/index.JulepApi.md).UpdateAgentRequest

**`Example`**

```ts
{}
```

## Table of contents

### Properties

- [about](index.JulepApi.UpdateAgentRequest.md#about)
- [defaultSettings](index.JulepApi.UpdateAgentRequest.md#defaultsettings)
- [instructions](index.JulepApi.UpdateAgentRequest.md#instructions)
- [model](index.JulepApi.UpdateAgentRequest.md#model)
- [name](index.JulepApi.UpdateAgentRequest.md#name)

## Properties

### about

• `Optional` **about**: `string`

About the agent

#### Defined in

[src/api/api/client/requests/UpdateAgentRequest.d.ts:11](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/client/requests/UpdateAgentRequest.d.ts#L11)

___

### defaultSettings

• `Optional` **defaultSettings**: [`AgentDefaultSettings`](index.JulepApi.AgentDefaultSettings.md)

Default model settings to start every session with

#### Defined in

[src/api/api/client/requests/UpdateAgentRequest.d.ts:19](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/client/requests/UpdateAgentRequest.d.ts#L19)

___

### instructions

• `Optional` **instructions**: [`Instruction`](index.JulepApi.Instruction.md)[]

List of instructions for the agent

#### Defined in

[src/api/api/client/requests/UpdateAgentRequest.d.ts:13](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/client/requests/UpdateAgentRequest.d.ts#L13)

___

### model

• `Optional` **model**: `string`

Name of the model that the agent is supposed to use

#### Defined in

[src/api/api/client/requests/UpdateAgentRequest.d.ts:17](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/client/requests/UpdateAgentRequest.d.ts#L17)

___

### name

• `Optional` **name**: `string`

Name of the agent

#### Defined in

[src/api/api/client/requests/UpdateAgentRequest.d.ts:15](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/client/requests/UpdateAgentRequest.d.ts#L15)
