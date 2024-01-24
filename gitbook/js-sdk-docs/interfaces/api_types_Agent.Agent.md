[@julep/sdk](../README.md) / [Modules](../modules.md) / [api/types/Agent](../modules/api_types_Agent.md) / Agent

# Interface: Agent

[api/types/Agent](../modules/api_types_Agent.md).Agent

## Table of contents

### Properties

- [about](api_types_Agent.Agent.md#about)
- [createdAt](api_types_Agent.Agent.md#createdat)
- [defaultSettings](api_types_Agent.Agent.md#defaultsettings)
- [id](api_types_Agent.Agent.md#id)
- [instructions](api_types_Agent.Agent.md#instructions)
- [model](api_types_Agent.Agent.md#model)
- [name](api_types_Agent.Agent.md#name)
- [updatedAt](api_types_Agent.Agent.md#updatedat)

## Properties

### about

• **about**: `string`

About the agent

#### Defined in

[src/api/api/types/Agent.d.ts:9](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/Agent.d.ts#L9)

___

### createdAt

• `Optional` **createdAt**: `Date`

Agent created at (RFC-3339 format)

#### Defined in

[src/api/api/types/Agent.d.ts:13](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/Agent.d.ts#L13)

___

### defaultSettings

• `Optional` **defaultSettings**: [`AgentDefaultSettings`](api_types_AgentDefaultSettings.AgentDefaultSettings.md)

Default settings for all sessions created by this agent

#### Defined in

[src/api/api/types/Agent.d.ts:19](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/Agent.d.ts#L19)

___

### id

• **id**: `string`

Agent id (UUID)

#### Defined in

[src/api/api/types/Agent.d.ts:17](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/Agent.d.ts#L17)

___

### instructions

• `Optional` **instructions**: [`Instruction`](api_types_Instruction.Instruction.md)[]

List of instructions for the agent

#### Defined in

[src/api/api/types/Agent.d.ts:11](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/Agent.d.ts#L11)

___

### model

• **model**: `string`

The model to use with this agent

#### Defined in

[src/api/api/types/Agent.d.ts:21](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/Agent.d.ts#L21)

___

### name

• **name**: `string`

Name of the agent

#### Defined in

[src/api/api/types/Agent.d.ts:7](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/Agent.d.ts#L7)

___

### updatedAt

• `Optional` **updatedAt**: `Date`

Agent updated at (RFC-3339 format)

#### Defined in

[src/api/api/types/Agent.d.ts:15](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/Agent.d.ts#L15)
