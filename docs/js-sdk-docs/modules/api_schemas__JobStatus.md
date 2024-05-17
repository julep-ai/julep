[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$JobStatus

# Module: api/schemas/$JobStatus

## Table of contents

### Variables

- [$JobStatus](api_schemas__JobStatus.md#$jobstatus)

## Variables

### $JobStatus

• `Const` **$JobStatus**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `created_at`: \{ `description`: ``"Job created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `has_progress`: \{ `description`: ``"Whether this Job supports progress updates"`` ; `type`: ``"boolean"`` = "boolean" } ; `id`: \{ `description`: ``"Job id (UUID)"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `name`: \{ `description`: ``"Name of the job"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `progress`: \{ `description`: ``"Progress percentage"`` ; `maximum`: ``100`` = 100; `type`: ``"number"`` = "number" } ; `reason`: \{ `description`: ``"Reason for current state"`` ; `type`: ``"string"`` = "string" } ; `state`: \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } ; `updated_at`: \{ `description`: ``"Job updated at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" }  } |
| `properties.created_at` | \{ `description`: ``"Job created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.created_at.description` | ``"Job created at (RFC-3339 format)"`` |
| `properties.created_at.format` | ``"date-time"`` |
| `properties.created_at.isRequired` | ``true`` |
| `properties.created_at.type` | ``"string"`` |
| `properties.has_progress` | \{ `description`: ``"Whether this Job supports progress updates"`` ; `type`: ``"boolean"`` = "boolean" } |
| `properties.has_progress.description` | ``"Whether this Job supports progress updates"`` |
| `properties.has_progress.type` | ``"boolean"`` |
| `properties.id` | \{ `description`: ``"Job id (UUID)"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.description` | ``"Job id (UUID)"`` |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.name` | \{ `description`: ``"Name of the job"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"Name of the job"`` |
| `properties.name.isRequired` | ``true`` |
| `properties.name.type` | ``"string"`` |
| `properties.progress` | \{ `description`: ``"Progress percentage"`` ; `maximum`: ``100`` = 100; `type`: ``"number"`` = "number" } |
| `properties.progress.description` | ``"Progress percentage"`` |
| `properties.progress.maximum` | ``100`` |
| `properties.progress.type` | ``"number"`` |
| `properties.reason` | \{ `description`: ``"Reason for current state"`` ; `type`: ``"string"`` = "string" } |
| `properties.reason.description` | ``"Reason for current state"`` |
| `properties.reason.type` | ``"string"`` |
| `properties.state` | \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } |
| `properties.state.isRequired` | ``true`` |
| `properties.state.type` | ``"Enum"`` |
| `properties.updated_at` | \{ `description`: ``"Job updated at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } |
| `properties.updated_at.description` | ``"Job updated at (RFC-3339 format)"`` |
| `properties.updated_at.format` | ``"date-time"`` |
| `properties.updated_at.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$JobStatus.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$JobStatus.ts#L5)
