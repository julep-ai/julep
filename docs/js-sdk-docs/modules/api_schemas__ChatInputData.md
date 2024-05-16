[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$ChatInputData

# Module: api/schemas/$ChatInputData

## Table of contents

### Variables

- [$ChatInputData](api_schemas__ChatInputData.md#$chatinputdata)

## Variables

### $ChatInputData

• `Const` **$ChatInputData**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `messages`: \{ `contains`: \{ `type`: ``"InputChatMLMessage"`` = "InputChatMLMessage" } ; `isRequired`: ``true`` = true; `type`: ``"array"`` = "array" } ; `tool_choice`: \{ `contains`: readonly [\{ `type`: ``"ToolChoiceOption"`` = "ToolChoiceOption" }, \{ `type`: ``"NamedToolChoice"`` = "NamedToolChoice" }] ; `description`: ``"Can be one of existing tools given to the agent earlier or the ones included in the request"`` ; `isNullable`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } ; `tools`: \{ `contains`: \{ `type`: ``"Tool"`` = "Tool" } ; `isNullable`: ``true`` = true; `type`: ``"array"`` = "array" }  } |
| `properties.messages` | \{ `contains`: \{ `type`: ``"InputChatMLMessage"`` = "InputChatMLMessage" } ; `isRequired`: ``true`` = true; `type`: ``"array"`` = "array" } |
| `properties.messages.contains` | \{ `type`: ``"InputChatMLMessage"`` = "InputChatMLMessage" } |
| `properties.messages.contains.type` | ``"InputChatMLMessage"`` |
| `properties.messages.isRequired` | ``true`` |
| `properties.messages.type` | ``"array"`` |
| `properties.tool_choice` | \{ `contains`: readonly [\{ `type`: ``"ToolChoiceOption"`` = "ToolChoiceOption" }, \{ `type`: ``"NamedToolChoice"`` = "NamedToolChoice" }] ; `description`: ``"Can be one of existing tools given to the agent earlier or the ones included in the request"`` ; `isNullable`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } |
| `properties.tool_choice.contains` | readonly [\{ `type`: ``"ToolChoiceOption"`` = "ToolChoiceOption" }, \{ `type`: ``"NamedToolChoice"`` = "NamedToolChoice" }] |
| `properties.tool_choice.description` | ``"Can be one of existing tools given to the agent earlier or the ones included in the request"`` |
| `properties.tool_choice.isNullable` | ``true`` |
| `properties.tool_choice.type` | ``"one-of"`` |
| `properties.tools` | \{ `contains`: \{ `type`: ``"Tool"`` = "Tool" } ; `isNullable`: ``true`` = true; `type`: ``"array"`` = "array" } |
| `properties.tools.contains` | \{ `type`: ``"Tool"`` = "Tool" } |
| `properties.tools.contains.type` | ``"Tool"`` |
| `properties.tools.isNullable` | ``true`` |
| `properties.tools.type` | ``"array"`` |

#### Defined in

[src/api/schemas/$ChatInputData.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$ChatInputData.ts#L5)
