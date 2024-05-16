[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$CompletionUsage

# Module: api/schemas/$CompletionUsage

## Table of contents

### Variables

- [$CompletionUsage](api_schemas__CompletionUsage.md#$completionusage)

## Variables

### $CompletionUsage

• `Const` **$CompletionUsage**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"Usage statistics for the completion request."`` |
| `properties` | \{ `completion_tokens`: \{ `description`: ``"Number of tokens in the generated completion."`` ; `isRequired`: ``true`` = true; `type`: ``"number"`` = "number" } ; `prompt_tokens`: \{ `description`: ``"Number of tokens in the prompt."`` ; `isRequired`: ``true`` = true; `type`: ``"number"`` = "number" } ; `total_tokens`: \{ `description`: ``"Total number of tokens used in the request (prompt + completion)."`` ; `isRequired`: ``true`` = true; `type`: ``"number"`` = "number" }  } |
| `properties.completion_tokens` | \{ `description`: ``"Number of tokens in the generated completion."`` ; `isRequired`: ``true`` = true; `type`: ``"number"`` = "number" } |
| `properties.completion_tokens.description` | ``"Number of tokens in the generated completion."`` |
| `properties.completion_tokens.isRequired` | ``true`` |
| `properties.completion_tokens.type` | ``"number"`` |
| `properties.prompt_tokens` | \{ `description`: ``"Number of tokens in the prompt."`` ; `isRequired`: ``true`` = true; `type`: ``"number"`` = "number" } |
| `properties.prompt_tokens.description` | ``"Number of tokens in the prompt."`` |
| `properties.prompt_tokens.isRequired` | ``true`` |
| `properties.prompt_tokens.type` | ``"number"`` |
| `properties.total_tokens` | \{ `description`: ``"Total number of tokens used in the request (prompt + completion)."`` ; `isRequired`: ``true`` = true; `type`: ``"number"`` = "number" } |
| `properties.total_tokens.description` | ``"Total number of tokens used in the request (prompt + completion)."`` |
| `properties.total_tokens.isRequired` | ``true`` |
| `properties.total_tokens.type` | ``"number"`` |

#### Defined in

[src/api/schemas/$CompletionUsage.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$CompletionUsage.ts#L5)
