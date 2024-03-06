[@julep/sdk](../README.md) / [Modules](../modules.md) / [index](../modules/index.md) / [JulepApi](../modules/index.JulepApi.md) / ChatResponse

# Interface: ChatResponse

[index](../modules/index.md).[JulepApi](../modules/index.JulepApi.md).ChatResponse

Represents a chat completion response returned by model, based on the provided input.

## Table of contents

### Properties

- [finishReason](index.JulepApi.ChatResponse.md#finishreason)
- [id](index.JulepApi.ChatResponse.md#id)
- [jobs](index.JulepApi.ChatResponse.md#jobs)
- [response](index.JulepApi.ChatResponse.md#response)
- [usage](index.JulepApi.ChatResponse.md#usage)

## Properties

### finishReason

• **finishReason**: [`ChatResponseFinishReason`](../modules/index.JulepApi.md#chatresponsefinishreason)

The reason the model stopped generating tokens. This will be `stop` if the model hit a natural stop point or a provided stop sequence, `length` if the maximum number of tokens specified in the request was reached, `content_filter` if content was omitted due to a flag from our content filters, `tool_calls` if the model called a tool, or `function_call` (deprecated) if the model called a function.

#### Defined in

[src/api/api/types/ChatResponse.d.ts:12](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/ChatResponse.d.ts#L12)

___

### id

• **id**: `string`

A unique identifier for the chat completion.

#### Defined in

[src/api/api/types/ChatResponse.d.ts:10](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/ChatResponse.d.ts#L10)

___

### jobs

• `Optional` **jobs**: `string`[]

IDs (if any) of jobs created as part of this request

#### Defined in

[src/api/api/types/ChatResponse.d.ts:17](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/ChatResponse.d.ts#L17)

___

### response

• **response**: [`ChatMlMessage`](index.JulepApi.ChatMlMessage.md)[][]

A list of chat completion messages produced as a response.

#### Defined in

[src/api/api/types/ChatResponse.d.ts:14](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/ChatResponse.d.ts#L14)

___

### usage

• **usage**: [`CompletionUsage`](index.JulepApi.CompletionUsage.md)

#### Defined in

[src/api/api/types/ChatResponse.d.ts:15](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/ChatResponse.d.ts#L15)
