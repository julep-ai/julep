[@julep/sdk](../README.md) / [Exports](../modules.md) / api/models/CreateUserRequest

# Module: api/models/CreateUserRequest

## Table of contents

### Type Aliases

- [CreateUserRequest](api_models_CreateUserRequest.md#createuserrequest)

## Type Aliases

### CreateUserRequest

Ƭ **CreateUserRequest**: `Object`

A valid request payload for creating a user

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `about?` | `string` | About the user |
| `docs?` | [`CreateDoc`](api_models_CreateDoc.md#createdoc)[] | List of docs about user |
| `metadata?` | `any` | (Optional) metadata |
| `name?` | `string` | Name of the user |

#### Defined in

[src/api/models/CreateUserRequest.ts:9](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/models/CreateUserRequest.ts#L9)
