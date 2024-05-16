[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$Agent

# Module: api/schemas/$Agent

## Table of contents

### Variables

- [$Agent](api_schemas__Agent.md#$agent)

## Variables

### $Agent

• `Const` **$Agent**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `about`: \{ `description`: ``"About the agent"`` ; `type`: ``"string"`` = "string" } ; `created_at`: \{ `description`: ``"Agent created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } ; `default_settings`: \{ `description`: ``"Default settings for all sessions created by this agent"`` ; `type`: ``"AgentDefaultSettings"`` = "AgentDefaultSettings" } ; `id`: \{ `description`: ``"Agent id (UUID)"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `instructions`: \{ `contains`: readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] ; `description`: ``"Instructions for the agent"`` ; `type`: ``"one-of"`` = "one-of" } ; `metadata`: \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } ; `model`: \{ `description`: ``"The model to use with this agent"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `name`: \{ `description`: ``"Name of the agent"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `updated_at`: \{ `description`: ``"Agent updated at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" }  } |
| `properties.about` | \{ `description`: ``"About the agent"`` ; `type`: ``"string"`` = "string" } |
| `properties.about.description` | ``"About the agent"`` |
| `properties.about.type` | ``"string"`` |
| `properties.created_at` | \{ `description`: ``"Agent created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } |
| `properties.created_at.description` | ``"Agent created at (RFC-3339 format)"`` |
| `properties.created_at.format` | ``"date-time"`` |
| `properties.created_at.type` | ``"string"`` |
| `properties.default_settings` | \{ `description`: ``"Default settings for all sessions created by this agent"`` ; `type`: ``"AgentDefaultSettings"`` = "AgentDefaultSettings" } |
| `properties.default_settings.description` | ``"Default settings for all sessions created by this agent"`` |
| `properties.default_settings.type` | ``"AgentDefaultSettings"`` |
| `properties.id` | \{ `description`: ``"Agent id (UUID)"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.description` | ``"Agent id (UUID)"`` |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.instructions` | \{ `contains`: readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] ; `description`: ``"Instructions for the agent"`` ; `type`: ``"one-of"`` = "one-of" } |
| `properties.instructions.contains` | readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] |
| `properties.instructions.description` | ``"Instructions for the agent"`` |
| `properties.instructions.type` | ``"one-of"`` |
| `properties.metadata` | \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"Optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.model` | \{ `description`: ``"The model to use with this agent"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.model.description` | ``"The model to use with this agent"`` |
| `properties.model.isRequired` | ``true`` |
| `properties.model.type` | ``"string"`` |
| `properties.name` | \{ `description`: ``"Name of the agent"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"Name of the agent"`` |
| `properties.name.isRequired` | ``true`` |
| `properties.name.type` | ``"string"`` |
| `properties.updated_at` | \{ `description`: ``"Agent updated at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } |
| `properties.updated_at.description` | ``"Agent updated at (RFC-3339 format)"`` |
| `properties.updated_at.format` | ``"date-time"`` |
| `properties.updated_at.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$Agent.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$Agent.ts#L5)
