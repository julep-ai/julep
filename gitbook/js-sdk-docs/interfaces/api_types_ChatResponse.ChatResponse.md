[@julep/sdk](../README.md) / [Modules](../modules.md) / [api/types/ChatResponse](../modules/api_types_ChatResponse.md) / ChatResponse

# Interface: ChatResponse

[api/types/ChatResponse](../modules/api_types_ChatResponse.md).ChatResponse

Represents a chat completion response returned by model, based on the provided input.

## Table of contents

### Properties

- [finishReason](api_types_ChatResponse.ChatResponse.md#finishreason)
- [id](api_types_ChatResponse.ChatResponse.md#id)
- [response](api_types_ChatResponse.ChatResponse.md#response)
- [usage](api_types_ChatResponse.ChatResponse.md#usage)

## Properties

### finishReason

• **finishReason**: [`ChatResponseFinishReason`](../modules/api_types_ChatResponseFinishReason.md#chatresponsefinishreason)

The reason the model stopped generating tokens. This will be `stop` if the model hit a natural stop point or a provided stop sequence, `length` if the maximum number of tokens specified in the request was reached, `content_filter` if content was omitted due to a flag from our content filters, `tool_calls` if the model called a tool, or `function_call` (deprecated) if the model called a function.

#### Defined in

[src/api/api/types/ChatResponse.d.ts:12](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/ChatResponse.d.ts#L12)

___

### id

• **id**: `string`

A unique identifier for the chat completion.

#### Defined in

[src/api/api/types/ChatResponse.d.ts:10](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/ChatResponse.d.ts#L10)

___

### response

• **response**: [`ChatMlMessage`](api_types_ChatMlMessage.ChatMlMessage.md)[][]

A list of chat completion messages produced as a response.

#### Defined in

[src/api/api/types/ChatResponse.d.ts:14](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/ChatResponse.d.ts#L14)

___

### usage

• **usage**: [`CompletionUsage`](api_types_CompletionUsage.CompletionUsage.md)

#### Defined in

[src/api/api/types/ChatResponse.d.ts:15](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/ChatResponse.d.ts#L15)
