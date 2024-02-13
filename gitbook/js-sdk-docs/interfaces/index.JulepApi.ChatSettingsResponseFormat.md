[@julep/sdk](../README.md) / [Modules](../modules.md) / [index](../modules/index.md) / [JulepApi](../modules/index.JulepApi.md) / ChatSettingsResponseFormat

# Interface: ChatSettingsResponseFormat

[index](../modules/index.md).[JulepApi](../modules/index.JulepApi.md).ChatSettingsResponseFormat

An object specifying the format that the model must output.

Setting to `{ "type": "json_object" }` enables JSON mode, which guarantees the message the model generates is valid JSON.

**Important:** when using JSON mode, you **must** also instruct the model to produce JSON yourself via a system or user message. Without this, the model may generate an unending stream of whitespace until the generation reaches the token limit, resulting in a long-running and seemingly "stuck" request. Also note that the message content may be partially cut off if `finish_reason="length"`, which indicates the generation exceeded `max_tokens` or the conversation exceeded the max context length.

## Table of contents

### Properties

- [pattern](index.JulepApi.ChatSettingsResponseFormat.md#pattern)
- [schema](index.JulepApi.ChatSettingsResponseFormat.md#schema)
- [type](index.JulepApi.ChatSettingsResponseFormat.md#type)

## Properties

### pattern

• `Optional` **pattern**: `string`

Regular expression pattern to use if `type` is `"regex"`

#### Defined in

[src/api/api/types/ChatSettingsResponseFormat.d.ts:16](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/api/types/ChatSettingsResponseFormat.d.ts#L16)

___

### schema

• `Optional` **schema**: [`ChatSettingsResponseFormatSchema`](index.JulepApi.ChatSettingsResponseFormatSchema.md)

JSON Schema to use if `type` is `"json_object"`

#### Defined in

[src/api/api/types/ChatSettingsResponseFormat.d.ts:18](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/api/types/ChatSettingsResponseFormat.d.ts#L18)

___

### type

• `Optional` **type**: [`ChatSettingsResponseFormatType`](../modules/index.JulepApi.md#chatsettingsresponseformattype)

Must be one of `"text"`, `"regex"` or `"json_object"`.

#### Defined in

[src/api/api/types/ChatSettingsResponseFormat.d.ts:14](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/api/types/ChatSettingsResponseFormat.d.ts#L14)
