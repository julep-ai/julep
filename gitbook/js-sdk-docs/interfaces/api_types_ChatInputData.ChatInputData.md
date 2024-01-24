[@julep/sdk](../README.md) / [Modules](../modules.md) / [api/types/ChatInputData](../modules/api_types_ChatInputData.md) / ChatInputData

# Interface: ChatInputData

[api/types/ChatInputData](../modules/api_types_ChatInputData.md).ChatInputData

## Hierarchy

- **`ChatInputData`**

  ↳ [`ChatInput`](api_client_requests_ChatInput.ChatInput.md)

## Table of contents

### Properties

- [messages](api_types_ChatInputData.ChatInputData.md#messages)
- [toolChoice](api_types_ChatInputData.ChatInputData.md#toolchoice)
- [tools](api_types_ChatInputData.ChatInputData.md#tools)

## Properties

### messages

• **messages**: [`InputChatMlMessage`](api_types_InputChatMlMessage.InputChatMlMessage.md)[]

A list of new input messages comprising the conversation so far.

#### Defined in

[src/api/api/types/ChatInputData.d.ts:7](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/ChatInputData.d.ts#L7)

___

### toolChoice

• `Optional` **toolChoice**: `string`

Can be one of existing tools given to the agent earlier or the ones included in the request

#### Defined in

[src/api/api/types/ChatInputData.d.ts:11](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/ChatInputData.d.ts#L11)

___

### tools

• `Optional` **tools**: [`Tool`](api_types_Tool.Tool.md)[]

(Advanced) List of tools that are provided in addition to agent's default set of tools. Functions of same name in agent set are overriden

#### Defined in

[src/api/api/types/ChatInputData.d.ts:9](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/ChatInputData.d.ts#L9)
