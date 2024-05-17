[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$CreateDoc

# Module: api/schemas/$CreateDoc

## Table of contents

### Variables

- [$CreateDoc](api_schemas__CreateDoc.md#$createdoc)

## Variables

### $CreateDoc

• `Const` **$CreateDoc**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `content`: \{ `contains`: readonly [\{ `contains`: \{ `minItems`: ``1`` = 1; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }, \{ `description`: ``"A single document chunk"`` ; `type`: ``"string"`` = "string" }] ; `description`: ``"Information content"`` ; `isRequired`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } ; `metadata`: \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } ; `title`: \{ `description`: ``"Title describing what this bit of information contains"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  } |
| `properties.content` | \{ `contains`: readonly [\{ `contains`: \{ `minItems`: ``1`` = 1; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }, \{ `description`: ``"A single document chunk"`` ; `type`: ``"string"`` = "string" }] ; `description`: ``"Information content"`` ; `isRequired`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } |
| `properties.content.contains` | readonly [\{ `contains`: \{ `minItems`: ``1`` = 1; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }, \{ `description`: ``"A single document chunk"`` ; `type`: ``"string"`` = "string" }] |
| `properties.content.description` | ``"Information content"`` |
| `properties.content.isRequired` | ``true`` |
| `properties.content.type` | ``"one-of"`` |
| `properties.metadata` | \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"Optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.title` | \{ `description`: ``"Title describing what this bit of information contains"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.title.description` | ``"Title describing what this bit of information contains"`` |
| `properties.title.isRequired` | ``true`` |
| `properties.title.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$CreateDoc.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$CreateDoc.ts#L5)
