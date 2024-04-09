[@julep/sdk](../README.md) / [Modules](../modules.md) / [index](../modules/index.md) / [JulepApi](../modules/index.JulepApi.md) / InputChatMlMessage

# Interface: InputChatMlMessage

[index](../modules/index.md).[JulepApi](../modules/index.JulepApi.md).InputChatMlMessage

## Table of contents

### Properties

- [content](index.JulepApi.InputChatMlMessage.md#content)
- [continue](index.JulepApi.InputChatMlMessage.md#continue)
- [name](index.JulepApi.InputChatMlMessage.md#name)
- [role](index.JulepApi.InputChatMlMessage.md#role)

## Properties

### content

• **content**: `string`

ChatML content

#### Defined in

[src/api/api/types/InputChatMlMessage.d.ts:9](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/InputChatMlMessage.d.ts#L9)

___

### continue

• `Optional` **continue**: `boolean`

Whether to continue this message or return a new one

#### Defined in

[src/api/api/types/InputChatMlMessage.d.ts:13](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/InputChatMlMessage.d.ts#L13)

___

### name

• `Optional` **name**: `string`

ChatML name

#### Defined in

[src/api/api/types/InputChatMlMessage.d.ts:11](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/InputChatMlMessage.d.ts#L11)

___

### role

• **role**: [`InputChatMlMessageRole`](../modules/index.JulepApi.md#inputchatmlmessagerole)

ChatML role (system|assistant|user|function_call)

#### Defined in

[src/api/api/types/InputChatMlMessage.d.ts:7](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/InputChatMlMessage.d.ts#L7)
