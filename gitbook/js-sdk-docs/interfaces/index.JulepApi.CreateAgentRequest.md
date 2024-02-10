[@julep/sdk](../README.md) / [Modules](../modules.md) / [index](../modules/index.md) / [JulepApi](../modules/index.JulepApi.md) / CreateAgentRequest

# Interface: CreateAgentRequest

[index](../modules/index.md).[JulepApi](../modules/index.JulepApi.md).CreateAgentRequest

**`Example`**

```ts
{
 *         name: "name",
 *         about: "about",
 *         model: "model"
 *     }
```

## Table of contents

### Properties

- [about](index.JulepApi.CreateAgentRequest.md#about)
- [defaultSettings](index.JulepApi.CreateAgentRequest.md#defaultsettings)
- [docs](index.JulepApi.CreateAgentRequest.md#docs)
- [instructions](index.JulepApi.CreateAgentRequest.md#instructions)
- [model](index.JulepApi.CreateAgentRequest.md#model)
- [name](index.JulepApi.CreateAgentRequest.md#name)
- [tools](index.JulepApi.CreateAgentRequest.md#tools)

## Properties

### about

• **about**: `string`

About the agent

#### Defined in

[src/api/api/client/requests/CreateAgentRequest.d.ts:17](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/client/requests/CreateAgentRequest.d.ts#L17)

___

### defaultSettings

• `Optional` **defaultSettings**: [`AgentDefaultSettings`](index.JulepApi.AgentDefaultSettings.md)

Default model settings to start every session with

#### Defined in

[src/api/api/client/requests/CreateAgentRequest.d.ts:23](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/client/requests/CreateAgentRequest.d.ts#L23)

___

### docs

• `Optional` **docs**: [`CreateDoc`](index.JulepApi.CreateDoc.md)[]

List of docs about agent

#### Defined in

[src/api/api/client/requests/CreateAgentRequest.d.ts:27](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/client/requests/CreateAgentRequest.d.ts#L27)

___

### instructions

• `Optional` **instructions**: [`Instruction`](index.JulepApi.Instruction.md)[]

List of instructions for the agent

#### Defined in

[src/api/api/client/requests/CreateAgentRequest.d.ts:19](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/client/requests/CreateAgentRequest.d.ts#L19)

___

### model

• **model**: `string`

Name of the model that the agent is supposed to use

#### Defined in

[src/api/api/client/requests/CreateAgentRequest.d.ts:25](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/client/requests/CreateAgentRequest.d.ts#L25)

___

### name

• **name**: `string`

Name of the agent

#### Defined in

[src/api/api/client/requests/CreateAgentRequest.d.ts:15](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/client/requests/CreateAgentRequest.d.ts#L15)

___

### tools

• `Optional` **tools**: [`CreateToolRequest`](index.JulepApi.CreateToolRequest.md)[]

A list of tools the model may call. Currently, only `function`s are supported as a tool. Use this to provide a list of functions the model may generate JSON inputs for.

#### Defined in

[src/api/api/client/requests/CreateAgentRequest.d.ts:21](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/client/requests/CreateAgentRequest.d.ts#L21)
