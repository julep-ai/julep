[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$ResourceUpdatedResponse

# Module: api/schemas/$ResourceUpdatedResponse

## Table of contents

### Variables

- [$ResourceUpdatedResponse](api_schemas__ResourceUpdatedResponse.md#$resourceupdatedresponse)

## Variables

### $ResourceUpdatedResponse

• `Const` **$ResourceUpdatedResponse**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `id`: \{ `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `jobs`: \{ `contains`: \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" } ; `updated_at`: \{ `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  } |
| `properties.id` | \{ `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.jobs` | \{ `contains`: \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" } |
| `properties.jobs.contains` | \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } |
| `properties.jobs.contains.format` | ``"uuid"`` |
| `properties.jobs.contains.type` | ``"string"`` |
| `properties.jobs.type` | ``"array"`` |
| `properties.updated_at` | \{ `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.updated_at.format` | ``"date-time"`` |
| `properties.updated_at.isRequired` | ``true`` |
| `properties.updated_at.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$ResourceUpdatedResponse.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$ResourceUpdatedResponse.ts#L5)
