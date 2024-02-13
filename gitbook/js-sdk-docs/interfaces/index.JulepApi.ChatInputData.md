[@julep/sdk](../README.md) / [Modules](../modules.md) / [index](../modules/index.md) / [JulepApi](../modules/index.JulepApi.md) / ChatInputData

# Interface: ChatInputData

[index](../modules/index.md).[JulepApi](../modules/index.JulepApi.md).ChatInputData

## Hierarchy

- **`ChatInputData`**

  ↳ [`ChatInput`](index.JulepApi.ChatInput.md)

## Table of contents

### Properties

- [messages](index.JulepApi.ChatInputData.md#messages)
- [toolChoice](index.JulepApi.ChatInputData.md#toolchoice)
- [tools](index.JulepApi.ChatInputData.md#tools)

## Properties

### messages

• **messages**: [`InputChatMlMessage`](index.JulepApi.InputChatMlMessage.md)[]

A list of new input messages comprising the conversation so far.

#### Defined in

[src/api/api/types/ChatInputData.d.ts:7](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/api/types/ChatInputData.d.ts#L7)

___

### toolChoice

• `Optional` **toolChoice**: `string`

Can be one of existing tools given to the agent earlier or the ones included in the request

#### Defined in

[src/api/api/types/ChatInputData.d.ts:11](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/api/types/ChatInputData.d.ts#L11)

___

### tools

• `Optional` **tools**: [`Tool`](index.JulepApi.Tool.md)[]

(Advanced) List of tools that are provided in addition to agent's default set of tools. Functions of same name in agent set are overriden

#### Defined in

[src/api/api/types/ChatInputData.d.ts:9](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/api/types/ChatInputData.d.ts#L9)
