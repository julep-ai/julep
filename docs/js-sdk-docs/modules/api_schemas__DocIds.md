[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$DocIds

# Module: api/schemas/$DocIds

## Table of contents

### Variables

- [$DocIds](api_schemas__DocIds.md#$docids)

## Variables

### $DocIds

• `Const` **$DocIds**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `agent_doc_ids`: \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `isRequired`: ``true`` = true; `type`: ``"array"`` = "array" } ; `user_doc_ids`: \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `isRequired`: ``true`` = true; `type`: ``"array"`` = "array" }  } |
| `properties.agent_doc_ids` | \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `isRequired`: ``true`` = true; `type`: ``"array"`` = "array" } |
| `properties.agent_doc_ids.contains` | \{ `type`: ``"string"`` = "string" } |
| `properties.agent_doc_ids.contains.type` | ``"string"`` |
| `properties.agent_doc_ids.isRequired` | ``true`` |
| `properties.agent_doc_ids.type` | ``"array"`` |
| `properties.user_doc_ids` | \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `isRequired`: ``true`` = true; `type`: ``"array"`` = "array" } |
| `properties.user_doc_ids.contains` | \{ `type`: ``"string"`` = "string" } |
| `properties.user_doc_ids.contains.type` | ``"string"`` |
| `properties.user_doc_ids.isRequired` | ``true`` |
| `properties.user_doc_ids.type` | ``"array"`` |

#### Defined in

[src/api/schemas/$DocIds.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$DocIds.ts#L5)
