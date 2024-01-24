[@julep/sdk](../README.md) / [Modules](../modules.md) / [api/client/requests/CreateAgentRequest](../modules/api_client_requests_CreateAgentRequest.md) / CreateAgentRequest

# Interface: CreateAgentRequest

[api/client/requests/CreateAgentRequest](../modules/api_client_requests_CreateAgentRequest.md).CreateAgentRequest

**`Example`**

```ts
{
 *         name: "string",
 *         about: "string",
 *         instructions: [{
 *                 content: "string"
 *             }],
 *         tools: [{
 *                 type: JulepApi.CreateToolRequestType.Function,
 *                 definition: {
 *                     name: "string",
 *                     parameters: {
 *                         "string": "string"
 *                     }
 *                 }
 *             }],
 *         defaultSettings: {
 *             temperature: 1,
 *             topP: 1
 *         },
 *         model: "string",
 *         additionalInfo: [{
 *                 title: "string",
 *                 content: "string"
 *             }]
 *     }
```

## Table of contents

### Properties

- [about](api_client_requests_CreateAgentRequest.CreateAgentRequest.md#about)
- [additionalInfo](api_client_requests_CreateAgentRequest.CreateAgentRequest.md#additionalinfo)
- [defaultSettings](api_client_requests_CreateAgentRequest.CreateAgentRequest.md#defaultsettings)
- [instructions](api_client_requests_CreateAgentRequest.CreateAgentRequest.md#instructions)
- [model](api_client_requests_CreateAgentRequest.CreateAgentRequest.md#model)
- [name](api_client_requests_CreateAgentRequest.CreateAgentRequest.md#name)
- [tools](api_client_requests_CreateAgentRequest.CreateAgentRequest.md#tools)

## Properties

### about

• **about**: `string`

About the agent

#### Defined in

[src/api/api/client/requests/CreateAgentRequest.d.ts:37](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/client/requests/CreateAgentRequest.d.ts#L37)

___

### additionalInfo

• `Optional` **additionalInfo**: [`CreateAdditionalInfoRequest`](api_types_CreateAdditionalInfoRequest.CreateAdditionalInfoRequest.md)[]

List of additional info about agent

#### Defined in

[src/api/api/client/requests/CreateAgentRequest.d.ts:47](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/client/requests/CreateAgentRequest.d.ts#L47)

___

### defaultSettings

• `Optional` **defaultSettings**: [`AgentDefaultSettings`](api_types_AgentDefaultSettings.AgentDefaultSettings.md)

Default model settings to start every session with

#### Defined in

[src/api/api/client/requests/CreateAgentRequest.d.ts:43](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/client/requests/CreateAgentRequest.d.ts#L43)

___

### instructions

• `Optional` **instructions**: [`Instruction`](api_types_Instruction.Instruction.md)[]

List of instructions for the agent

#### Defined in

[src/api/api/client/requests/CreateAgentRequest.d.ts:39](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/client/requests/CreateAgentRequest.d.ts#L39)

___

### model

• **model**: `string`

Name of the model that the agent is supposed to use

#### Defined in

[src/api/api/client/requests/CreateAgentRequest.d.ts:45](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/client/requests/CreateAgentRequest.d.ts#L45)

___

### name

• **name**: `string`

Name of the agent

#### Defined in

[src/api/api/client/requests/CreateAgentRequest.d.ts:35](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/client/requests/CreateAgentRequest.d.ts#L35)

___

### tools

• `Optional` **tools**: [`CreateToolRequest`](api_types_CreateToolRequest.CreateToolRequest.md)[]

A list of tools the model may call. Currently, only `function`s are supported as a tool. Use this to provide a list of functions the model may generate JSON inputs for.

#### Defined in

[src/api/api/client/requests/CreateAgentRequest.d.ts:41](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/client/requests/CreateAgentRequest.d.ts#L41)
