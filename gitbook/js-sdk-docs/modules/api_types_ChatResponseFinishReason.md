[@julep/sdk](../README.md) / [Modules](../modules.md) / api/types/ChatResponseFinishReason

# Module: api/types/ChatResponseFinishReason

## Table of contents

### Type Aliases

- [ChatResponseFinishReason](api_types_ChatResponseFinishReason.md#chatresponsefinishreason)

### Variables

- [ChatResponseFinishReason](api_types_ChatResponseFinishReason.md#chatresponsefinishreason-1)

## Type Aliases

### ChatResponseFinishReason

Ƭ **ChatResponseFinishReason**: ``"stop"`` \| ``"length"`` \| ``"tool_calls"`` \| ``"content_filter"`` \| ``"function_call"``

The reason the model stopped generating tokens. This will be `stop` if the model hit a natural stop point or a provided stop sequence, `length` if the maximum number of tokens specified in the request was reached, `content_filter` if content was omitted due to a flag from our content filters, `tool_calls` if the model called a tool, or `function_call` (deprecated) if the model called a function.

#### Defined in

[src/api/api/types/ChatResponseFinishReason.d.ts:7](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/ChatResponseFinishReason.d.ts#L7)

[src/api/api/types/ChatResponseFinishReason.d.ts:13](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/ChatResponseFinishReason.d.ts#L13)

## Variables

### ChatResponseFinishReason

• **ChatResponseFinishReason**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `ContentFilter` | ``"content_filter"`` |
| `FunctionCall` | ``"function_call"`` |
| `Length` | ``"length"`` |
| `Stop` | ``"stop"`` |
| `ToolCalls` | ``"tool_calls"`` |

#### Defined in

[src/api/api/types/ChatResponseFinishReason.d.ts:7](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/ChatResponseFinishReason.d.ts#L7)

[src/api/api/types/ChatResponseFinishReason.d.ts:13](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/ChatResponseFinishReason.d.ts#L13)
