[@julep/sdk](../README.md) / [Modules](../modules.md) / [api/types/InputChatMlMessage](../modules/api_types_InputChatMlMessage.md) / InputChatMlMessage

# Interface: InputChatMlMessage

[api/types/InputChatMlMessage](../modules/api_types_InputChatMlMessage.md).InputChatMlMessage

## Table of contents

### Properties

- [content](api_types_InputChatMlMessage.InputChatMlMessage.md#content)
- [continue](api_types_InputChatMlMessage.InputChatMlMessage.md#continue)
- [name](api_types_InputChatMlMessage.InputChatMlMessage.md#name)
- [role](api_types_InputChatMlMessage.InputChatMlMessage.md#role)

## Properties

### content

• **content**: `string`

ChatML content

#### Defined in

[src/api/api/types/InputChatMlMessage.d.ts:9](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/InputChatMlMessage.d.ts#L9)

___

### continue

• `Optional` **continue**: `boolean`

Whether to continue this message or return a new one

#### Defined in

[src/api/api/types/InputChatMlMessage.d.ts:13](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/InputChatMlMessage.d.ts#L13)

___

### name

• `Optional` **name**: `string`

ChatML name

#### Defined in

[src/api/api/types/InputChatMlMessage.d.ts:11](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/InputChatMlMessage.d.ts#L11)

___

### role

• **role**: [`InputChatMlMessageRole`](../modules/api_types_InputChatMlMessageRole.md#inputchatmlmessagerole)

ChatML role (system|assistant|user|function_call)

#### Defined in

[src/api/api/types/InputChatMlMessage.d.ts:7](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/InputChatMlMessage.d.ts#L7)
