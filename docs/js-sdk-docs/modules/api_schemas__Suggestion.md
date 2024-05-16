[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$Suggestion

# Module: api/schemas/$Suggestion

## Table of contents

### Variables

- [$Suggestion](api_schemas__Suggestion.md#$suggestion)

## Variables

### $Suggestion

• `Const` **$Suggestion**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `content`: \{ `description`: ``"The content of the suggestion"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `created_at`: \{ `description`: ``"Suggestion created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } ; `message_id`: \{ `description`: ``"The message that produced it"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `session_id`: \{ `description`: ``"Session this suggestion belongs to"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `target`: \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" }  } |
| `properties.content` | \{ `description`: ``"The content of the suggestion"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.content.description` | ``"The content of the suggestion"`` |
| `properties.content.isRequired` | ``true`` |
| `properties.content.type` | ``"string"`` |
| `properties.created_at` | \{ `description`: ``"Suggestion created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } |
| `properties.created_at.description` | ``"Suggestion created at (RFC-3339 format)"`` |
| `properties.created_at.format` | ``"date-time"`` |
| `properties.created_at.type` | ``"string"`` |
| `properties.message_id` | \{ `description`: ``"The message that produced it"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.message_id.description` | ``"The message that produced it"`` |
| `properties.message_id.format` | ``"uuid"`` |
| `properties.message_id.isRequired` | ``true`` |
| `properties.message_id.type` | ``"string"`` |
| `properties.session_id` | \{ `description`: ``"Session this suggestion belongs to"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.session_id.description` | ``"Session this suggestion belongs to"`` |
| `properties.session_id.format` | ``"uuid"`` |
| `properties.session_id.isRequired` | ``true`` |
| `properties.session_id.type` | ``"string"`` |
| `properties.target` | \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } |
| `properties.target.isRequired` | ``true`` |
| `properties.target.type` | ``"Enum"`` |

#### Defined in

[src/api/schemas/$Suggestion.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$Suggestion.ts#L5)
