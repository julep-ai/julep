[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$UpdateSessionRequest

# Module: api/schemas/$UpdateSessionRequest

## Table of contents

### Variables

- [$UpdateSessionRequest](api_schemas__UpdateSessionRequest.md#$updatesessionrequest)

## Variables

### $UpdateSessionRequest

• `Const` **$UpdateSessionRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"A valid request payload for updating a session"`` |
| `properties` | \{ `metadata`: \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } ; `situation`: \{ `description`: ``"Updated situation for this session"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  } |
| `properties.metadata` | \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"Optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.situation` | \{ `description`: ``"Updated situation for this session"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.situation.description` | ``"Updated situation for this session"`` |
| `properties.situation.isRequired` | ``true`` |
| `properties.situation.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$UpdateSessionRequest.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$UpdateSessionRequest.ts#L5)
