[@julep/sdk](../README.md) / [Modules](../modules.md) / [index](../modules/index.md) / [JulepApi](../modules/index.JulepApi.md) / CreateSessionRequest

# Interface: CreateSessionRequest

[index](../modules/index.md).[JulepApi](../modules/index.JulepApi.md).CreateSessionRequest

**`Example`**

```ts
{
 *         userId: "user_id",
 *         agentId: "agent_id"
 *     }
```

## Table of contents

### Properties

- [agentId](index.JulepApi.CreateSessionRequest.md#agentid)
- [situation](index.JulepApi.CreateSessionRequest.md#situation)
- [userId](index.JulepApi.CreateSessionRequest.md#userid)

## Properties

### agentId

• **agentId**: `string`

Agent ID of agent to associate with this session

#### Defined in

[src/api/api/client/requests/CreateSessionRequest.d.ts:15](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/api/client/requests/CreateSessionRequest.d.ts#L15)

___

### situation

• `Optional` **situation**: `string`

A specific situation that sets the background for this session

#### Defined in

[src/api/api/client/requests/CreateSessionRequest.d.ts:17](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/api/client/requests/CreateSessionRequest.d.ts#L17)

___

### userId

• **userId**: `string`

User ID of user to associate with this session

#### Defined in

[src/api/api/client/requests/CreateSessionRequest.d.ts:13](https://github.com/julep-ai/samantha-dev/blob/4200383/sdks/js/src/api/api/client/requests/CreateSessionRequest.d.ts#L13)
