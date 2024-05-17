[@julep/sdk](../README.md) / [Exports](../modules.md) / api/models/InputChatMLMessage

# Module: api/models/InputChatMLMessage

## Table of contents

### Type Aliases

- [InputChatMLMessage](api_models_InputChatMLMessage.md#inputchatmlmessage)

## Type Aliases

### InputChatMLMessage

Ƭ **InputChatMLMessage**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `content` | `string` | ChatML content |
| `continue?` | `boolean` | Whether to continue this message or return a new one |
| `name?` | `string` | ChatML name |
| `role` | ``"user"`` \| ``"assistant"`` \| ``"system"`` \| ``"function_call"`` \| ``"function"`` \| ``"auto"`` | ChatML role (system\|assistant\|user\|function_call\|function\|auto) |

#### Defined in

[src/api/models/InputChatMLMessage.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/models/InputChatMLMessage.ts#L5)
