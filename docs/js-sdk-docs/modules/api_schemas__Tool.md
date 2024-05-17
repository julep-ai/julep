[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$Tool

# Module: api/schemas/$Tool

## Table of contents

### Variables

- [$Tool](api_schemas__Tool.md#$tool)

## Variables

### $Tool

• `Const` **$Tool**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `function`: \{ `contains`: readonly [\{ `type`: ``"FunctionDef"`` = "FunctionDef" }] ; `description`: ``"Function definition and parameters"`` ; `isRequired`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } ; `id`: \{ `description`: ``"Tool ID"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `type`: \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" }  } |
| `properties.function` | \{ `contains`: readonly [\{ `type`: ``"FunctionDef"`` = "FunctionDef" }] ; `description`: ``"Function definition and parameters"`` ; `isRequired`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } |
| `properties.function.contains` | readonly [\{ `type`: ``"FunctionDef"`` = "FunctionDef" }] |
| `properties.function.description` | ``"Function definition and parameters"`` |
| `properties.function.isRequired` | ``true`` |
| `properties.function.type` | ``"one-of"`` |
| `properties.id` | \{ `description`: ``"Tool ID"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.description` | ``"Tool ID"`` |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.type` | \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } |
| `properties.type.isRequired` | ``true`` |
| `properties.type.type` | ``"Enum"`` |

#### Defined in

[src/api/schemas/$Tool.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$Tool.ts#L5)
