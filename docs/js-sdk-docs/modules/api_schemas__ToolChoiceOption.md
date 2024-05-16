[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$ToolChoiceOption

# Module: api/schemas/$ToolChoiceOption

## Table of contents

### Variables

- [$ToolChoiceOption](api_schemas__ToolChoiceOption.md#$toolchoiceoption)

## Variables

### $ToolChoiceOption

• `Const` **$ToolChoiceOption**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `contains` | readonly [\{ `type`: ``"Enum"`` = "Enum" }, \{ `type`: ``"NamedToolChoice"`` = "NamedToolChoice" }] |
| `description` | ``"Controls which (if any) function is called by the model.\n  `none` means the model will not call a function and instead generates a message.\n  `auto` means the model can pick between generating a message or calling a function.\n  Specifying a particular function via `{\"type: \"function\", \"function\": {\"name\": \"my_function\"}}` forces the model to call that function.\n  `none` is the default when no functions are present. `auto` is the default if functions are present.\n  "`` |
| `type` | ``"one-of"`` |

#### Defined in

[src/api/schemas/$ToolChoiceOption.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$ToolChoiceOption.ts#L5)
