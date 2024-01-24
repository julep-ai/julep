[@julep/sdk](../README.md) / [Modules](../modules.md) / [api/types/ChatMlMessage](../modules/api_types_ChatMlMessage.md) / ChatMlMessage

# Interface: ChatMlMessage

[api/types/ChatMlMessage](../modules/api_types_ChatMlMessage.md).ChatMlMessage

## Table of contents

### Properties

- [content](api_types_ChatMlMessage.ChatMlMessage.md#content)
- [createdAt](api_types_ChatMlMessage.ChatMlMessage.md#createdat)
- [id](api_types_ChatMlMessage.ChatMlMessage.md#id)
- [name](api_types_ChatMlMessage.ChatMlMessage.md#name)
- [role](api_types_ChatMlMessage.ChatMlMessage.md#role)

## Properties

### content

• **content**: `string`

ChatML content

#### Defined in

[src/api/api/types/ChatMlMessage.d.ts:9](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/ChatMlMessage.d.ts#L9)

___

### createdAt

• **createdAt**: `Date`

Message created at (RFC-3339 format)

#### Defined in

[src/api/api/types/ChatMlMessage.d.ts:13](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/ChatMlMessage.d.ts#L13)

___

### id

• **id**: `string`

Message ID

#### Defined in

[src/api/api/types/ChatMlMessage.d.ts:15](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/ChatMlMessage.d.ts#L15)

___

### name

• `Optional` **name**: `string`

ChatML name

#### Defined in

[src/api/api/types/ChatMlMessage.d.ts:11](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/ChatMlMessage.d.ts#L11)

___

### role

• **role**: [`ChatMlMessageRole`](../modules/api_types_ChatMlMessageRole.md#chatmlmessagerole)

ChatML role (system|assistant|user|function_call)

#### Defined in

[src/api/api/types/ChatMlMessage.d.ts:7](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/ChatMlMessage.d.ts#L7)
