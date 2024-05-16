[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$FunctionDef

# Module: api/schemas/$FunctionDef

## Table of contents

### Variables

- [$FunctionDef](api_schemas__FunctionDef.md#$functiondef)

## Variables

### $FunctionDef

• `Const` **$FunctionDef**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `description`: \{ `description`: ``"A description of what the function does, used by the model to choose when and how to call the function."`` ; `type`: ``"string"`` = "string" } ; `name`: \{ `description`: ``"The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64."`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `parameters`: \{ `description`: ``"Parameters accepeted by this function"`` ; `isRequired`: ``true`` = true; `type`: ``"FunctionParameters"`` = "FunctionParameters" }  } |
| `properties.description` | \{ `description`: ``"A description of what the function does, used by the model to choose when and how to call the function."`` ; `type`: ``"string"`` = "string" } |
| `properties.description.description` | ``"A description of what the function does, used by the model to choose when and how to call the function."`` |
| `properties.description.type` | ``"string"`` |
| `properties.name` | \{ `description`: ``"The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64."`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64."`` |
| `properties.name.isRequired` | ``true`` |
| `properties.name.type` | ``"string"`` |
| `properties.parameters` | \{ `description`: ``"Parameters accepeted by this function"`` ; `isRequired`: ``true`` = true; `type`: ``"FunctionParameters"`` = "FunctionParameters" } |
| `properties.parameters.description` | ``"Parameters accepeted by this function"`` |
| `properties.parameters.isRequired` | ``true`` |
| `properties.parameters.type` | ``"FunctionParameters"`` |

#### Defined in

[src/api/schemas/$FunctionDef.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$FunctionDef.ts#L5)
