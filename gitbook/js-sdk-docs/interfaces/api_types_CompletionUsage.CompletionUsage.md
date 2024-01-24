[@julep/sdk](../README.md) / [Modules](../modules.md) / [api/types/CompletionUsage](../modules/api_types_CompletionUsage.md) / CompletionUsage

# Interface: CompletionUsage

[api/types/CompletionUsage](../modules/api_types_CompletionUsage.md).CompletionUsage

Usage statistics for the completion request.

## Table of contents

### Properties

- [completionTokens](api_types_CompletionUsage.CompletionUsage.md#completiontokens)
- [promptTokens](api_types_CompletionUsage.CompletionUsage.md#prompttokens)
- [totalTokens](api_types_CompletionUsage.CompletionUsage.md#totaltokens)

## Properties

### completionTokens

• **completionTokens**: `number`

Number of tokens in the generated completion.

#### Defined in

[src/api/api/types/CompletionUsage.d.ts:9](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/CompletionUsage.d.ts#L9)

___

### promptTokens

• **promptTokens**: `number`

Number of tokens in the prompt.

#### Defined in

[src/api/api/types/CompletionUsage.d.ts:11](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/CompletionUsage.d.ts#L11)

___

### totalTokens

• **totalTokens**: `number`

Total number of tokens used in the request (prompt + completion).

#### Defined in

[src/api/api/types/CompletionUsage.d.ts:13](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/CompletionUsage.d.ts#L13)
