[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$NamedToolChoice

# Module: api/schemas/$NamedToolChoice

## Table of contents

### Variables

- [$NamedToolChoice](api_schemas__NamedToolChoice.md#$namedtoolchoice)

## Variables

### $NamedToolChoice

• `Const` **$NamedToolChoice**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"Specifies a tool the model should use. Use to force the model to call a specific function."`` |
| `properties` | \{ `function`: \{ `isRequired`: ``true`` = true; `properties`: \{ `name`: \{ `description`: ``"The name of the function to call."`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  }  } ; `type`: \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" }  } |
| `properties.function` | \{ `isRequired`: ``true`` = true; `properties`: \{ `name`: \{ `description`: ``"The name of the function to call."`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  }  } |
| `properties.function.isRequired` | ``true`` |
| `properties.function.properties` | \{ `name`: \{ `description`: ``"The name of the function to call."`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  } |
| `properties.function.properties.name` | \{ `description`: ``"The name of the function to call."`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.function.properties.name.description` | ``"The name of the function to call."`` |
| `properties.function.properties.name.isRequired` | ``true`` |
| `properties.function.properties.name.type` | ``"string"`` |
| `properties.type` | \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } |
| `properties.type.isRequired` | ``true`` |
| `properties.type.type` | ``"Enum"`` |

#### Defined in

[src/api/schemas/$NamedToolChoice.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$NamedToolChoice.ts#L5)
