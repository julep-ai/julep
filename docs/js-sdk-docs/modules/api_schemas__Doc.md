[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$Doc

# Module: api/schemas/$Doc

## Table of contents

### Variables

- [$Doc](api_schemas__Doc.md#$doc)

## Variables

### $Doc

• `Const` **$Doc**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `content`: \{ `contains`: readonly [\{ `contains`: \{ `minItems`: ``1`` = 1; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }, \{ `description`: ``"A single document chunk"`` ; `type`: ``"string"`` = "string" }] ; `description`: ``"Information content"`` ; `isRequired`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } ; `created_at`: \{ `description`: ``"Doc created at"`` ; `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `id`: \{ `description`: ``"ID of doc"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `metadata`: \{ `description`: ``"optional metadata"`` ; `properties`: {} = \{} } ; `title`: \{ `description`: ``"Title describing what this bit of information contains"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  } |
| `properties.content` | \{ `contains`: readonly [\{ `contains`: \{ `minItems`: ``1`` = 1; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }, \{ `description`: ``"A single document chunk"`` ; `type`: ``"string"`` = "string" }] ; `description`: ``"Information content"`` ; `isRequired`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } |
| `properties.content.contains` | readonly [\{ `contains`: \{ `minItems`: ``1`` = 1; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }, \{ `description`: ``"A single document chunk"`` ; `type`: ``"string"`` = "string" }] |
| `properties.content.description` | ``"Information content"`` |
| `properties.content.isRequired` | ``true`` |
| `properties.content.type` | ``"one-of"`` |
| `properties.created_at` | \{ `description`: ``"Doc created at"`` ; `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.created_at.description` | ``"Doc created at"`` |
| `properties.created_at.format` | ``"date-time"`` |
| `properties.created_at.isRequired` | ``true`` |
| `properties.created_at.type` | ``"string"`` |
| `properties.id` | \{ `description`: ``"ID of doc"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.description` | ``"ID of doc"`` |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.metadata` | \{ `description`: ``"optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.title` | \{ `description`: ``"Title describing what this bit of information contains"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.title.description` | ``"Title describing what this bit of information contains"`` |
| `properties.title.isRequired` | ``true`` |
| `properties.title.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$Doc.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$Doc.ts#L5)
