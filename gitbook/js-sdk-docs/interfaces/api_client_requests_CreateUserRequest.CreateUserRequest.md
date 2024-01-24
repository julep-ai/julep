[@julep/sdk](../README.md) / [Modules](../modules.md) / [api/client/requests/CreateUserRequest](../modules/api_client_requests_CreateUserRequest.md) / CreateUserRequest

# Interface: CreateUserRequest

[api/client/requests/CreateUserRequest](../modules/api_client_requests_CreateUserRequest.md).CreateUserRequest

**`Example`**

```ts
{
 *         additionalInformation: [{
 *                 title: "string",
 *                 content: "string"
 *             }]
 *     }
```

## Table of contents

### Properties

- [about](api_client_requests_CreateUserRequest.CreateUserRequest.md#about)
- [additionalInformation](api_client_requests_CreateUserRequest.CreateUserRequest.md#additionalinformation)
- [name](api_client_requests_CreateUserRequest.CreateUserRequest.md#name)

## Properties

### about

• `Optional` **about**: `string`

About the user

#### Defined in

[src/api/api/client/requests/CreateUserRequest.d.ts:18](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/client/requests/CreateUserRequest.d.ts#L18)

___

### additionalInformation

• `Optional` **additionalInformation**: [`CreateAdditionalInfoRequest`](api_types_CreateAdditionalInfoRequest.CreateAdditionalInfoRequest.md)[]

List of additional info about user

#### Defined in

[src/api/api/client/requests/CreateUserRequest.d.ts:20](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/client/requests/CreateUserRequest.d.ts#L20)

___

### name

• `Optional` **name**: `string`

Name of the user

#### Defined in

[src/api/api/client/requests/CreateUserRequest.d.ts:16](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/client/requests/CreateUserRequest.d.ts#L16)
