[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$User

# Module: api/schemas/$User

## Table of contents

### Variables

- [$User](api_schemas__User.md#$user)

## Variables

### $User

• `Const` **$User**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `about`: \{ `description`: ``"About the user"`` ; `type`: ``"string"`` = "string" } ; `created_at`: \{ `description`: ``"User created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } ; `id`: \{ `description`: ``"User id (UUID)"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `metadata`: \{ `description`: ``"(Optional) metadata"`` ; `properties`: {} = \{} } ; `name`: \{ `description`: ``"Name of the user"`` ; `type`: ``"string"`` = "string" } ; `updated_at`: \{ `description`: ``"User updated at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" }  } |
| `properties.about` | \{ `description`: ``"About the user"`` ; `type`: ``"string"`` = "string" } |
| `properties.about.description` | ``"About the user"`` |
| `properties.about.type` | ``"string"`` |
| `properties.created_at` | \{ `description`: ``"User created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } |
| `properties.created_at.description` | ``"User created at (RFC-3339 format)"`` |
| `properties.created_at.format` | ``"date-time"`` |
| `properties.created_at.type` | ``"string"`` |
| `properties.id` | \{ `description`: ``"User id (UUID)"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.description` | ``"User id (UUID)"`` |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.metadata` | \{ `description`: ``"(Optional) metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"(Optional) metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.name` | \{ `description`: ``"Name of the user"`` ; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"Name of the user"`` |
| `properties.name.type` | ``"string"`` |
| `properties.updated_at` | \{ `description`: ``"User updated at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } |
| `properties.updated_at.description` | ``"User updated at (RFC-3339 format)"`` |
| `properties.updated_at.format` | ``"date-time"`` |
| `properties.updated_at.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$User.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$User.ts#L5)
