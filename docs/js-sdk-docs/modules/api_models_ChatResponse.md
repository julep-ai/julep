[@julep/sdk](../README.md) / [Exports](../modules.md) / api/models/ChatResponse

# Module: api/models/ChatResponse

## Table of contents

### Type Aliases

- [ChatResponse](api_models_ChatResponse.md#chatresponse)

## Type Aliases

### ChatResponse

Ƭ **ChatResponse**: `Object`

Represents a chat completion response returned by model, based on the provided input.

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `doc_ids` | [`DocIds`](api_models_DocIds.md#docids) | - |
| `finish_reason` | ``"stop"`` \| ``"length"`` \| ``"tool_calls"`` \| ``"content_filter"`` \| ``"function_call"`` | The reason the model stopped generating tokens. This will be `stop` if the model hit a natural stop point or a provided stop sequence, `length` if the maximum number of tokens specified in the request was reached, `content_filter` if content was omitted due to a flag from our content filters, `tool_calls` if the model called a tool, or `function_call` (deprecated) if the model called a function. |
| `id` | `string` | A unique identifier for the chat completion. |
| `jobs?` | `string`[] | IDs (if any) of jobs created as part of this request |
| `response` | [`ChatMLMessage`](api_models_ChatMLMessage.md#chatmlmessage)[][] | A list of chat completion messages produced as a response. |
| `usage` | [`CompletionUsage`](api_models_CompletionUsage.md#completionusage) | - |

#### Defined in

[src/api/models/ChatResponse.ts:11](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/models/ChatResponse.ts#L11)
