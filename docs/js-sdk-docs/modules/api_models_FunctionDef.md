[@julep/sdk](../README.md) / [Exports](../modules.md) / api/models/FunctionDef

# Module: api/models/FunctionDef

## Table of contents

### Type Aliases

- [FunctionDef](api_models_FunctionDef.md#functiondef)

## Type Aliases

### FunctionDef

Ƭ **FunctionDef**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `description?` | `string` | A description of what the function does, used by the model to choose when and how to call the function. |
| `name` | `string` | The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64. |
| `parameters` | [`FunctionParameters`](api_models_FunctionParameters.md#functionparameters) | Parameters accepeted by this function |

#### Defined in

[src/api/models/FunctionDef.ts:6](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/models/FunctionDef.ts#L6)
