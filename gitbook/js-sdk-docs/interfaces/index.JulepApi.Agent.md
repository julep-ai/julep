[@julep/sdk](../README.md) / [Modules](../modules.md) / [index](../modules/index.md) / [JulepApi](../modules/index.JulepApi.md) / Agent

# Interface: Agent

[index](../modules/index.md).[JulepApi](../modules/index.JulepApi.md).Agent

## Table of contents

### Properties

- [about](index.JulepApi.Agent.md#about)
- [createdAt](index.JulepApi.Agent.md#createdat)
- [defaultSettings](index.JulepApi.Agent.md#defaultsettings)
- [id](index.JulepApi.Agent.md#id)
- [instructions](index.JulepApi.Agent.md#instructions)
- [model](index.JulepApi.Agent.md#model)
- [name](index.JulepApi.Agent.md#name)
- [updatedAt](index.JulepApi.Agent.md#updatedat)

## Properties

### about

• **about**: `string`

About the agent

#### Defined in

[src/api/api/types/Agent.d.ts:9](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/Agent.d.ts#L9)

___

### createdAt

• `Optional` **createdAt**: `Date`

Agent created at (RFC-3339 format)

#### Defined in

[src/api/api/types/Agent.d.ts:13](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/Agent.d.ts#L13)

___

### defaultSettings

• `Optional` **defaultSettings**: [`AgentDefaultSettings`](index.JulepApi.AgentDefaultSettings.md)

Default settings for all sessions created by this agent

#### Defined in

[src/api/api/types/Agent.d.ts:19](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/Agent.d.ts#L19)

___

### id

• **id**: `string`

Agent id (UUID)

#### Defined in

[src/api/api/types/Agent.d.ts:17](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/Agent.d.ts#L17)

___

### instructions

• `Optional` **instructions**: [`Instruction`](index.JulepApi.Instruction.md)[]

List of instructions for the agent

#### Defined in

[src/api/api/types/Agent.d.ts:11](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/Agent.d.ts#L11)

___

### model

• **model**: `string`

The model to use with this agent

#### Defined in

[src/api/api/types/Agent.d.ts:21](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/Agent.d.ts#L21)

___

### name

• **name**: `string`

Name of the agent

#### Defined in

[src/api/api/types/Agent.d.ts:7](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/Agent.d.ts#L7)

___

### updatedAt

• `Optional` **updatedAt**: `Date`

Agent updated at (RFC-3339 format)

#### Defined in

[src/api/api/types/Agent.d.ts:15](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/Agent.d.ts#L15)
