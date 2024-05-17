[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$PatchUserRequest

# Module: api/schemas/$PatchUserRequest

## Table of contents

### Variables

- [$PatchUserRequest](api_schemas__PatchUserRequest.md#$patchuserrequest)

## Variables

### $PatchUserRequest

• `Const` **$PatchUserRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"A request for patching a user"`` |
| `properties` | \{ `about`: \{ `description`: ``"About the user"`` ; `type`: ``"string"`` = "string" } ; `metadata`: \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } ; `name`: \{ `description`: ``"Name of the user"`` ; `type`: ``"string"`` = "string" }  } |
| `properties.about` | \{ `description`: ``"About the user"`` ; `type`: ``"string"`` = "string" } |
| `properties.about.description` | ``"About the user"`` |
| `properties.about.type` | ``"string"`` |
| `properties.metadata` | \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"Optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.name` | \{ `description`: ``"Name of the user"`` ; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"Name of the user"`` |
| `properties.name.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$PatchUserRequest.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$PatchUserRequest.ts#L5)
