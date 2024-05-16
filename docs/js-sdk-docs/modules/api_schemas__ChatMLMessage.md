[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$ChatMLMessage

# Module: api/schemas/$ChatMLMessage

## Table of contents

### Variables

- [$ChatMLMessage](api_schemas__ChatMLMessage.md#$chatmlmessage)

## Variables

### $ChatMLMessage

• `Const` **$ChatMLMessage**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `content`: \{ `description`: ``"ChatML content"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `created_at`: \{ `description`: ``"Message created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `id`: \{ `description`: ``"Message ID"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `name`: \{ `description`: ``"ChatML name"`` ; `type`: ``"string"`` = "string" } ; `role`: \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" }  } |
| `properties.content` | \{ `description`: ``"ChatML content"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.content.description` | ``"ChatML content"`` |
| `properties.content.isRequired` | ``true`` |
| `properties.content.type` | ``"string"`` |
| `properties.created_at` | \{ `description`: ``"Message created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.created_at.description` | ``"Message created at (RFC-3339 format)"`` |
| `properties.created_at.format` | ``"date-time"`` |
| `properties.created_at.isRequired` | ``true`` |
| `properties.created_at.type` | ``"string"`` |
| `properties.id` | \{ `description`: ``"Message ID"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.description` | ``"Message ID"`` |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.name` | \{ `description`: ``"ChatML name"`` ; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"ChatML name"`` |
| `properties.name.type` | ``"string"`` |
| `properties.role` | \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } |
| `properties.role.isRequired` | ``true`` |
| `properties.role.type` | ``"Enum"`` |

#### Defined in

[src/api/schemas/$ChatMLMessage.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$ChatMLMessage.ts#L5)
