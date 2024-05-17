[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$CreateUserRequest

# Module: api/schemas/$CreateUserRequest

## Table of contents

### Variables

- [$CreateUserRequest](api_schemas__CreateUserRequest.md#$createuserrequest)

## Variables

### $CreateUserRequest

• `Const` **$CreateUserRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"A valid request payload for creating a user"`` |
| `properties` | \{ `about`: \{ `description`: ``"About the user"`` ; `type`: ``"string"`` = "string" } ; `docs`: \{ `contains`: \{ `type`: ``"CreateDoc"`` = "CreateDoc" } ; `type`: ``"array"`` = "array" } ; `metadata`: \{ `description`: ``"(Optional) metadata"`` ; `properties`: {} = \{} } ; `name`: \{ `description`: ``"Name of the user"`` ; `type`: ``"string"`` = "string" }  } |
| `properties.about` | \{ `description`: ``"About the user"`` ; `type`: ``"string"`` = "string" } |
| `properties.about.description` | ``"About the user"`` |
| `properties.about.type` | ``"string"`` |
| `properties.docs` | \{ `contains`: \{ `type`: ``"CreateDoc"`` = "CreateDoc" } ; `type`: ``"array"`` = "array" } |
| `properties.docs.contains` | \{ `type`: ``"CreateDoc"`` = "CreateDoc" } |
| `properties.docs.contains.type` | ``"CreateDoc"`` |
| `properties.docs.type` | ``"array"`` |
| `properties.metadata` | \{ `description`: ``"(Optional) metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"(Optional) metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.name` | \{ `description`: ``"Name of the user"`` ; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"Name of the user"`` |
| `properties.name.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$CreateUserRequest.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$CreateUserRequest.ts#L5)
