[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$FunctionCallOption

# Module: api/schemas/$FunctionCallOption

## Table of contents

### Variables

- [$FunctionCallOption](api_schemas__FunctionCallOption.md#$functioncalloption)

## Variables

### $FunctionCallOption

• `Const` **$FunctionCallOption**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"Specifying a particular function via `{\"name\": \"my_function\"}` forces the model to call that function.\n  "`` |
| `properties` | \{ `name`: \{ `description`: ``"The name of the function to call."`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  } |
| `properties.name` | \{ `description`: ``"The name of the function to call."`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"The name of the function to call."`` |
| `properties.name.isRequired` | ``true`` |
| `properties.name.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$FunctionCallOption.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$FunctionCallOption.ts#L5)
