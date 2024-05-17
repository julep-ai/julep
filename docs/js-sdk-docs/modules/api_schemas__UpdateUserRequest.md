[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$UpdateUserRequest

# Module: api/schemas/$UpdateUserRequest

## Table of contents

### Variables

- [$UpdateUserRequest](api_schemas__UpdateUserRequest.md#$updateuserrequest)

## Variables

### $UpdateUserRequest

• `Const` **$UpdateUserRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"A valid request payload for updating a user"`` |
| `properties` | \{ `about`: \{ `description`: ``"About the user"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `metadata`: \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } ; `name`: \{ `description`: ``"Name of the user"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  } |
| `properties.about` | \{ `description`: ``"About the user"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.about.description` | ``"About the user"`` |
| `properties.about.isRequired` | ``true`` |
| `properties.about.type` | ``"string"`` |
| `properties.metadata` | \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"Optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.name` | \{ `description`: ``"Name of the user"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"Name of the user"`` |
| `properties.name.isRequired` | ``true`` |
| `properties.name.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$UpdateUserRequest.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$UpdateUserRequest.ts#L5)
