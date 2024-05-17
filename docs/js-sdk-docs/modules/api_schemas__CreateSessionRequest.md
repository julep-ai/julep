[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$CreateSessionRequest

# Module: api/schemas/$CreateSessionRequest

## Table of contents

### Variables

- [$CreateSessionRequest](api_schemas__CreateSessionRequest.md#$createsessionrequest)

## Variables

### $CreateSessionRequest

• `Const` **$CreateSessionRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"A valid request payload for creating a session"`` |
| `properties` | \{ `agent_id`: \{ `description`: ``"Agent ID of agent to associate with this session"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `metadata`: \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } ; `render_templates`: \{ `description`: ``"Render system and assistant message content as jinja templates"`` ; `type`: ``"boolean"`` = "boolean" } ; `situation`: \{ `description`: ``"A specific situation that sets the background for this session"`` ; `type`: ``"string"`` = "string" } ; `user_id`: \{ `description`: ``"(Optional) User ID of user to associate with this session"`` ; `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" }  } |
| `properties.agent_id` | \{ `description`: ``"Agent ID of agent to associate with this session"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.agent_id.description` | ``"Agent ID of agent to associate with this session"`` |
| `properties.agent_id.format` | ``"uuid"`` |
| `properties.agent_id.isRequired` | ``true`` |
| `properties.agent_id.type` | ``"string"`` |
| `properties.metadata` | \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"Optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.render_templates` | \{ `description`: ``"Render system and assistant message content as jinja templates"`` ; `type`: ``"boolean"`` = "boolean" } |
| `properties.render_templates.description` | ``"Render system and assistant message content as jinja templates"`` |
| `properties.render_templates.type` | ``"boolean"`` |
| `properties.situation` | \{ `description`: ``"A specific situation that sets the background for this session"`` ; `type`: ``"string"`` = "string" } |
| `properties.situation.description` | ``"A specific situation that sets the background for this session"`` |
| `properties.situation.type` | ``"string"`` |
| `properties.user_id` | \{ `description`: ``"(Optional) User ID of user to associate with this session"`` ; `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } |
| `properties.user_id.description` | ``"(Optional) User ID of user to associate with this session"`` |
| `properties.user_id.format` | ``"uuid"`` |
| `properties.user_id.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$CreateSessionRequest.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$CreateSessionRequest.ts#L5)
