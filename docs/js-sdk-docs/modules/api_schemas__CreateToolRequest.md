[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$CreateToolRequest

# Module: api/schemas/$CreateToolRequest

## Table of contents

### Variables

- [$CreateToolRequest](api_schemas__CreateToolRequest.md#$createtoolrequest)

## Variables

### $CreateToolRequest

• `Const` **$CreateToolRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `function`: \{ `contains`: readonly [\{ `type`: ``"FunctionDef"`` = "FunctionDef" }] ; `description`: ``"Function definition and parameters"`` ; `isRequired`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } ; `type`: \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" }  } |
| `properties.function` | \{ `contains`: readonly [\{ `type`: ``"FunctionDef"`` = "FunctionDef" }] ; `description`: ``"Function definition and parameters"`` ; `isRequired`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } |
| `properties.function.contains` | readonly [\{ `type`: ``"FunctionDef"`` = "FunctionDef" }] |
| `properties.function.description` | ``"Function definition and parameters"`` |
| `properties.function.isRequired` | ``true`` |
| `properties.function.type` | ``"one-of"`` |
| `properties.type` | \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } |
| `properties.type.isRequired` | ``true`` |
| `properties.type.type` | ``"Enum"`` |

#### Defined in

[src/api/schemas/$CreateToolRequest.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$CreateToolRequest.ts#L5)
