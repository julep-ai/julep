[@julep/sdk](../README.md) / [Exports](../modules.md) / api/models/NamedToolChoice

# Module: api/models/NamedToolChoice

## Table of contents

### Type Aliases

- [NamedToolChoice](api_models_NamedToolChoice.md#namedtoolchoice)

## Type Aliases

### NamedToolChoice

Ƭ **NamedToolChoice**: `Object`

Specifies a tool the model should use. Use to force the model to call a specific function.

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `function` | \{ `name`: `string`  } | - |
| `function.name` | `string` | The name of the function to call. |
| `type` | ``"function"`` | The type of the tool. Currently, only `function` is supported. |

#### Defined in

[src/api/models/NamedToolChoice.ts:8](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/models/NamedToolChoice.ts#L8)
