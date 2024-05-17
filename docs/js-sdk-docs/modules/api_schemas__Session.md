[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$Session

# Module: api/schemas/$Session

## Table of contents

### Variables

- [$Session](api_schemas__Session.md#$session)

## Variables

### $Session

• `Const` **$Session**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `agent_id`: \{ `description`: ``"Agent ID of agent associated with this session"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `created_at`: \{ `description`: ``"Session created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } ; `id`: \{ `description`: ``"Session id (UUID)"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `metadata`: \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } ; `render_templates`: \{ `description`: ``"Render system and assistant message content as jinja templates"`` ; `type`: ``"boolean"`` = "boolean" } ; `situation`: \{ `description`: ``"A specific situation that sets the background for this session"`` ; `type`: ``"string"`` = "string" } ; `summary`: \{ `description`: ``"(null at the beginning) - generated automatically after every interaction"`` ; `type`: ``"string"`` = "string" } ; `updated_at`: \{ `description`: ``"Session updated at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } ; `user_id`: \{ `description`: ``"User ID of user associated with this session"`` ; `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" }  } |
| `properties.agent_id` | \{ `description`: ``"Agent ID of agent associated with this session"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.agent_id.description` | ``"Agent ID of agent associated with this session"`` |
| `properties.agent_id.format` | ``"uuid"`` |
| `properties.agent_id.isRequired` | ``true`` |
| `properties.agent_id.type` | ``"string"`` |
| `properties.created_at` | \{ `description`: ``"Session created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } |
| `properties.created_at.description` | ``"Session created at (RFC-3339 format)"`` |
| `properties.created_at.format` | ``"date-time"`` |
| `properties.created_at.type` | ``"string"`` |
| `properties.id` | \{ `description`: ``"Session id (UUID)"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.description` | ``"Session id (UUID)"`` |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.metadata` | \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"Optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.render_templates` | \{ `description`: ``"Render system and assistant message content as jinja templates"`` ; `type`: ``"boolean"`` = "boolean" } |
| `properties.render_templates.description` | ``"Render system and assistant message content as jinja templates"`` |
| `properties.render_templates.type` | ``"boolean"`` |
| `properties.situation` | \{ `description`: ``"A specific situation that sets the background for this session"`` ; `type`: ``"string"`` = "string" } |
| `properties.situation.description` | ``"A specific situation that sets the background for this session"`` |
| `properties.situation.type` | ``"string"`` |
| `properties.summary` | \{ `description`: ``"(null at the beginning) - generated automatically after every interaction"`` ; `type`: ``"string"`` = "string" } |
| `properties.summary.description` | ``"(null at the beginning) - generated automatically after every interaction"`` |
| `properties.summary.type` | ``"string"`` |
| `properties.updated_at` | \{ `description`: ``"Session updated at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } |
| `properties.updated_at.description` | ``"Session updated at (RFC-3339 format)"`` |
| `properties.updated_at.format` | ``"date-time"`` |
| `properties.updated_at.type` | ``"string"`` |
| `properties.user_id` | \{ `description`: ``"User ID of user associated with this session"`` ; `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } |
| `properties.user_id.description` | ``"User ID of user associated with this session"`` |
| `properties.user_id.format` | ``"uuid"`` |
| `properties.user_id.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$Session.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$Session.ts#L5)
