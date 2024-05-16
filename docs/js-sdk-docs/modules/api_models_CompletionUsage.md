[@julep/sdk](../README.md) / [Exports](../modules.md) / api/models/CompletionUsage

# Module: api/models/CompletionUsage

## Table of contents

### Type Aliases

- [CompletionUsage](api_models_CompletionUsage.md#completionusage)

## Type Aliases

### CompletionUsage

Ƭ **CompletionUsage**: `Object`

Usage statistics for the completion request.

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `completion_tokens` | `number` | Number of tokens in the generated completion. |
| `prompt_tokens` | `number` | Number of tokens in the prompt. |
| `total_tokens` | `number` | Total number of tokens used in the request (prompt + completion). |

#### Defined in

[src/api/models/CompletionUsage.ts:8](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/models/CompletionUsage.ts#L8)
