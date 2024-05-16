[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$ChatResponse

# Module: api/schemas/$ChatResponse

## Table of contents

### Variables

- [$ChatResponse](api_schemas__ChatResponse.md#$chatresponse)

## Variables

### $ChatResponse

• `Const` **$ChatResponse**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"Represents a chat completion response returned by model, based on the provided input."`` |
| `properties` | \{ `doc_ids`: \{ `isRequired`: ``true`` = true; `type`: ``"DocIds"`` = "DocIds" } ; `finish_reason`: \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } ; `id`: \{ `description`: ``"A unique identifier for the chat completion."`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `jobs`: \{ `contains`: \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" } ; `response`: \{ `contains`: \{ `contains`: \{ `type`: ``"ChatMLMessage"`` = "ChatMLMessage" } ; `type`: ``"array"`` = "array" } ; `isRequired`: ``true`` = true; `type`: ``"array"`` = "array" } ; `usage`: \{ `isRequired`: ``true`` = true; `type`: ``"CompletionUsage"`` = "CompletionUsage" }  } |
| `properties.doc_ids` | \{ `isRequired`: ``true`` = true; `type`: ``"DocIds"`` = "DocIds" } |
| `properties.doc_ids.isRequired` | ``true`` |
| `properties.doc_ids.type` | ``"DocIds"`` |
| `properties.finish_reason` | \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } |
| `properties.finish_reason.isRequired` | ``true`` |
| `properties.finish_reason.type` | ``"Enum"`` |
| `properties.id` | \{ `description`: ``"A unique identifier for the chat completion."`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.description` | ``"A unique identifier for the chat completion."`` |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.jobs` | \{ `contains`: \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" } |
| `properties.jobs.contains` | \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } |
| `properties.jobs.contains.format` | ``"uuid"`` |
| `properties.jobs.contains.type` | ``"string"`` |
| `properties.jobs.type` | ``"array"`` |
| `properties.response` | \{ `contains`: \{ `contains`: \{ `type`: ``"ChatMLMessage"`` = "ChatMLMessage" } ; `type`: ``"array"`` = "array" } ; `isRequired`: ``true`` = true; `type`: ``"array"`` = "array" } |
| `properties.response.contains` | \{ `contains`: \{ `type`: ``"ChatMLMessage"`` = "ChatMLMessage" } ; `type`: ``"array"`` = "array" } |
| `properties.response.contains.contains` | \{ `type`: ``"ChatMLMessage"`` = "ChatMLMessage" } |
| `properties.response.contains.contains.type` | ``"ChatMLMessage"`` |
| `properties.response.contains.type` | ``"array"`` |
| `properties.response.isRequired` | ``true`` |
| `properties.response.type` | ``"array"`` |
| `properties.usage` | \{ `isRequired`: ``true`` = true; `type`: ``"CompletionUsage"`` = "CompletionUsage" } |
| `properties.usage.isRequired` | ``true`` |
| `properties.usage.type` | ``"CompletionUsage"`` |

#### Defined in

[src/api/schemas/$ChatResponse.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$ChatResponse.ts#L5)
