[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$ResourceDeletedResponse

# Module: api/schemas/$ResourceDeletedResponse

## Table of contents

### Variables

- [$ResourceDeletedResponse](api_schemas__ResourceDeletedResponse.md#$resourcedeletedresponse)

## Variables

### $ResourceDeletedResponse

• `Const` **$ResourceDeletedResponse**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `deleted_at`: \{ `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `id`: \{ `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `jobs`: \{ `contains`: \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }  } |
| `properties.deleted_at` | \{ `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.deleted_at.format` | ``"date-time"`` |
| `properties.deleted_at.isRequired` | ``true`` |
| `properties.deleted_at.type` | ``"string"`` |
| `properties.id` | \{ `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.jobs` | \{ `contains`: \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" } |
| `properties.jobs.contains` | \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } |
| `properties.jobs.contains.format` | ``"uuid"`` |
| `properties.jobs.contains.type` | ``"string"`` |
| `properties.jobs.type` | ``"array"`` |

#### Defined in

[src/api/schemas/$ResourceDeletedResponse.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$ResourceDeletedResponse.ts#L5)
