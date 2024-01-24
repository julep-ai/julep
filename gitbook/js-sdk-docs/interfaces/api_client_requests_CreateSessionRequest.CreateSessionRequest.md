[@julep/sdk](../README.md) / [Modules](../modules.md) / [api/client/requests/CreateSessionRequest](../modules/api_client_requests_CreateSessionRequest.md) / CreateSessionRequest

# Interface: CreateSessionRequest

[api/client/requests/CreateSessionRequest](../modules/api_client_requests_CreateSessionRequest.md).CreateSessionRequest

**`Example`**

```ts
{
 *         userId: "string",
 *         agentId: "string"
 *     }
```

## Table of contents

### Properties

- [agentId](api_client_requests_CreateSessionRequest.CreateSessionRequest.md#agentid)
- [situation](api_client_requests_CreateSessionRequest.CreateSessionRequest.md#situation)
- [userId](api_client_requests_CreateSessionRequest.CreateSessionRequest.md#userid)

## Properties

### agentId

• **agentId**: `string`

Agent ID of agent to associate with this session

#### Defined in

[src/api/api/client/requests/CreateSessionRequest.d.ts:15](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/client/requests/CreateSessionRequest.d.ts#L15)

___

### situation

• `Optional` **situation**: `string`

A specific situation that sets the background for this session

#### Defined in

[src/api/api/client/requests/CreateSessionRequest.d.ts:17](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/client/requests/CreateSessionRequest.d.ts#L17)

___

### userId

• **userId**: `string`

User ID of user to associate with this session

#### Defined in

[src/api/api/client/requests/CreateSessionRequest.d.ts:13](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/client/requests/CreateSessionRequest.d.ts#L13)
