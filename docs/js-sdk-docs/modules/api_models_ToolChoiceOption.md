[@julep/sdk](../README.md) / [Exports](../modules.md) / api/models/ToolChoiceOption

# Module: api/models/ToolChoiceOption

## Table of contents

### Type Aliases

- [ToolChoiceOption](api_models_ToolChoiceOption.md#toolchoiceoption)

## Type Aliases

### ToolChoiceOption

Ƭ **ToolChoiceOption**: ``"none"`` \| ``"auto"`` \| [`NamedToolChoice`](api_models_NamedToolChoice.md#namedtoolchoice)

Controls which (if any) function is called by the model.
`none` means the model will not call a function and instead generates a message.
`auto` means the model can pick between generating a message or calling a function.
Specifying a particular function via `{"type: "function", "function": {"name": "my_function"}}` forces the model to call that function.

`none` is the default when no functions are present. `auto` is the default if functions are present.

#### Defined in

[src/api/models/ToolChoiceOption.ts:15](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/models/ToolChoiceOption.ts#L15)
