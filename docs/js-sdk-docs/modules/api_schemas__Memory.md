[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$Memory

# Module: api/schemas/$Memory

## Table of contents

### Variables

- [$Memory](api_schemas__Memory.md#$memory)

## Variables

### $Memory

• `Const` **$Memory**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `agent_id`: \{ `description`: ``"ID of the agent"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `content`: \{ `description`: ``"Content of the memory"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `created_at`: \{ `description`: ``"Memory created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `entities`: \{ `contains`: \{ `properties`: {} = \{} } ; `isRequired`: ``true`` = true; `type`: ``"array"`` = "array" } ; `id`: \{ `description`: ``"Memory id (UUID)"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `last_accessed_at`: \{ `description`: ``"Memory last accessed at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } ; `sentiment`: \{ `description`: ``"Sentiment (valence) of the memory on a scale of -1 to 1"`` ; `maximum`: ``1`` = 1; `minimum`: ``-1`` = -1; `type`: ``"number"`` = "number" } ; `timestamp`: \{ `description`: ``"Memory happened at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } ; `user_id`: \{ `description`: ``"ID of the user"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  } |
| `properties.agent_id` | \{ `description`: ``"ID of the agent"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.agent_id.description` | ``"ID of the agent"`` |
| `properties.agent_id.format` | ``"uuid"`` |
| `properties.agent_id.isRequired` | ``true`` |
| `properties.agent_id.type` | ``"string"`` |
| `properties.content` | \{ `description`: ``"Content of the memory"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.content.description` | ``"Content of the memory"`` |
| `properties.content.isRequired` | ``true`` |
| `properties.content.type` | ``"string"`` |
| `properties.created_at` | \{ `description`: ``"Memory created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.created_at.description` | ``"Memory created at (RFC-3339 format)"`` |
| `properties.created_at.format` | ``"date-time"`` |
| `properties.created_at.isRequired` | ``true`` |
| `properties.created_at.type` | ``"string"`` |
| `properties.entities` | \{ `contains`: \{ `properties`: {} = \{} } ; `isRequired`: ``true`` = true; `type`: ``"array"`` = "array" } |
| `properties.entities.contains` | \{ `properties`: {} = \{} } |
| `properties.entities.contains.properties` | {} |
| `properties.entities.isRequired` | ``true`` |
| `properties.entities.type` | ``"array"`` |
| `properties.id` | \{ `description`: ``"Memory id (UUID)"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.description` | ``"Memory id (UUID)"`` |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.last_accessed_at` | \{ `description`: ``"Memory last accessed at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } |
| `properties.last_accessed_at.description` | ``"Memory last accessed at (RFC-3339 format)"`` |
| `properties.last_accessed_at.format` | ``"date-time"`` |
| `properties.last_accessed_at.type` | ``"string"`` |
| `properties.sentiment` | \{ `description`: ``"Sentiment (valence) of the memory on a scale of -1 to 1"`` ; `maximum`: ``1`` = 1; `minimum`: ``-1`` = -1; `type`: ``"number"`` = "number" } |
| `properties.sentiment.description` | ``"Sentiment (valence) of the memory on a scale of -1 to 1"`` |
| `properties.sentiment.maximum` | ``1`` |
| `properties.sentiment.minimum` | ``-1`` |
| `properties.sentiment.type` | ``"number"`` |
| `properties.timestamp` | \{ `description`: ``"Memory happened at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } |
| `properties.timestamp.description` | ``"Memory happened at (RFC-3339 format)"`` |
| `properties.timestamp.format` | ``"date-time"`` |
| `properties.timestamp.type` | ``"string"`` |
| `properties.user_id` | \{ `description`: ``"ID of the user"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.user_id.description` | ``"ID of the user"`` |
| `properties.user_id.format` | ``"uuid"`` |
| `properties.user_id.isRequired` | ``true`` |
| `properties.user_id.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$Memory.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$Memory.ts#L5)
