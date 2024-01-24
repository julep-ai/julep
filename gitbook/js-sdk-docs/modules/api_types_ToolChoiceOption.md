[@julep/sdk](../README.md) / [Modules](../modules.md) / api/types/ToolChoiceOption

# Module: api/types/ToolChoiceOption

## Table of contents

### Type Aliases

- [ToolChoiceOption](api_types_ToolChoiceOption.md#toolchoiceoption)

## Type Aliases

### ToolChoiceOption

Ƭ **ToolChoiceOption**: `string`

Controls which (if any) function is called by the model.
`none` means the model will not call a function and instead generates a message.
`auto` means the model can pick between generating a message or calling a function.
Specifying a particular function via `{"type: "function", "function": {"name": "my_function"}}` forces the model to call that function.

`none` is the default when no functions are present. `auto` is the default if functions are present.

#### Defined in

[src/api/api/types/ToolChoiceOption.d.ts:12](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/ToolChoiceOption.d.ts#L12)
