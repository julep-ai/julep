[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$PatchSessionRequest

# Module: api/schemas/$PatchSessionRequest

## Table of contents

### Variables

- [$PatchSessionRequest](api_schemas__PatchSessionRequest.md#$patchsessionrequest)

## Variables

### $PatchSessionRequest

• `Const` **$PatchSessionRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"A request for patching a session"`` |
| `properties` | \{ `metadata`: \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } ; `situation`: \{ `description`: ``"Updated situation for this session"`` ; `type`: ``"string"`` = "string" }  } |
| `properties.metadata` | \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"Optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.situation` | \{ `description`: ``"Updated situation for this session"`` ; `type`: ``"string"`` = "string" } |
| `properties.situation.description` | ``"Updated situation for this session"`` |
| `properties.situation.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$PatchSessionRequest.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$PatchSessionRequest.ts#L5)
