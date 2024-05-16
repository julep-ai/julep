[@julep/sdk](../README.md) / [Exports](../modules.md) / api/models/ChatInputData

# Module: api/models/ChatInputData

## Table of contents

### Type Aliases

- [ChatInputData](api_models_ChatInputData.md#chatinputdata)

## Type Aliases

### ChatInputData

Ƭ **ChatInputData**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `messages` | [`InputChatMLMessage`](api_models_InputChatMLMessage.md#inputchatmlmessage)[] | A list of new input messages comprising the conversation so far. |
| `tool_choice?` | [`ToolChoiceOption`](api_models_ToolChoiceOption.md#toolchoiceoption) \| [`NamedToolChoice`](api_models_NamedToolChoice.md#namedtoolchoice) \| ``null`` | Can be one of existing tools given to the agent earlier or the ones included in the request |
| `tools?` | [`Tool`](api_models_Tool.md#tool)[] \| ``null`` | (Advanced) List of tools that are provided in addition to agent's default set of tools. Functions of same name in agent set are overriden |

#### Defined in

[src/api/models/ChatInputData.ts:9](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/models/ChatInputData.ts#L9)
