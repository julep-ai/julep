[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$PartialFunctionDef

# Module: api/schemas/$PartialFunctionDef

## Table of contents

### Variables

- [$PartialFunctionDef](api_schemas__PartialFunctionDef.md#$partialfunctiondef)

## Variables

### $PartialFunctionDef

• `Const` **$PartialFunctionDef**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `description`: \{ `description`: ``"A description of what the function does, used by the model to choose when and how to call the function."`` ; `type`: ``"string"`` = "string" } ; `name`: \{ `description`: ``"The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64."`` ; `type`: ``"string"`` = "string" } ; `parameters`: \{ `description`: ``"Parameters accepeted by this function"`` ; `type`: ``"FunctionParameters"`` = "FunctionParameters" }  } |
| `properties.description` | \{ `description`: ``"A description of what the function does, used by the model to choose when and how to call the function."`` ; `type`: ``"string"`` = "string" } |
| `properties.description.description` | ``"A description of what the function does, used by the model to choose when and how to call the function."`` |
| `properties.description.type` | ``"string"`` |
| `properties.name` | \{ `description`: ``"The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64."`` ; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64."`` |
| `properties.name.type` | ``"string"`` |
| `properties.parameters` | \{ `description`: ``"Parameters accepeted by this function"`` ; `type`: ``"FunctionParameters"`` = "FunctionParameters" } |
| `properties.parameters.description` | ``"Parameters accepeted by this function"`` |
| `properties.parameters.type` | ``"FunctionParameters"`` |

#### Defined in

[src/api/schemas/$PartialFunctionDef.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$PartialFunctionDef.ts#L5)
