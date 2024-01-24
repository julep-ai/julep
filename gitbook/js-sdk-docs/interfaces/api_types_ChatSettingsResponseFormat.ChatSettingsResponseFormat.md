[@julep/sdk](../README.md) / [Modules](../modules.md) / [api/types/ChatSettingsResponseFormat](../modules/api_types_ChatSettingsResponseFormat.md) / ChatSettingsResponseFormat

# Interface: ChatSettingsResponseFormat

[api/types/ChatSettingsResponseFormat](../modules/api_types_ChatSettingsResponseFormat.md).ChatSettingsResponseFormat

An object specifying the format that the model must output.

Setting to `{ "type": "json_object" }` enables JSON mode, which guarantees the message the model generates is valid JSON.

**Important:** when using JSON mode, you **must** also instruct the model to produce JSON yourself via a system or user message. Without this, the model may generate an unending stream of whitespace until the generation reaches the token limit, resulting in a long-running and seemingly "stuck" request. Also note that the message content may be partially cut off if `finish_reason="length"`, which indicates the generation exceeded `max_tokens` or the conversation exceeded the max context length.

## Table of contents

### Properties

- [type](api_types_ChatSettingsResponseFormat.ChatSettingsResponseFormat.md#type)

## Properties

### type

• `Optional` **type**: [`ChatSettingsResponseFormatType`](../modules/api_types_ChatSettingsResponseFormatType.md#chatsettingsresponseformattype)

Must be one of `text` or `json_object`.

#### Defined in

[src/api/api/types/ChatSettingsResponseFormat.d.ts:14](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/ChatSettingsResponseFormat.d.ts#L14)
