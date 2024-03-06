[@julep/sdk](../README.md) / [Modules](../modules.md) / [index](../modules/index.md) / [JulepApi](../modules/index.JulepApi.md) / ChatMlMessage

# Interface: ChatMlMessage

[index](../modules/index.md).[JulepApi](../modules/index.JulepApi.md).ChatMlMessage

## Table of contents

### Properties

- [content](index.JulepApi.ChatMlMessage.md#content)
- [createdAt](index.JulepApi.ChatMlMessage.md#createdat)
- [id](index.JulepApi.ChatMlMessage.md#id)
- [name](index.JulepApi.ChatMlMessage.md#name)
- [role](index.JulepApi.ChatMlMessage.md#role)

## Properties

### content

• **content**: `string`

ChatML content

#### Defined in

[src/api/api/types/ChatMlMessage.d.ts:9](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/ChatMlMessage.d.ts#L9)

___

### createdAt

• **createdAt**: `Date`

Message created at (RFC-3339 format)

#### Defined in

[src/api/api/types/ChatMlMessage.d.ts:13](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/ChatMlMessage.d.ts#L13)

___

### id

• **id**: `string`

Message ID

#### Defined in

[src/api/api/types/ChatMlMessage.d.ts:15](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/ChatMlMessage.d.ts#L15)

___

### name

• `Optional` **name**: `string`

ChatML name

#### Defined in

[src/api/api/types/ChatMlMessage.d.ts:11](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/ChatMlMessage.d.ts#L11)

___

### role

• **role**: [`ChatMlMessageRole`](../modules/index.JulepApi.md#chatmlmessagerole)

ChatML role (system|assistant|user|function_call)

#### Defined in

[src/api/api/types/ChatMlMessage.d.ts:7](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/ChatMlMessage.d.ts#L7)
