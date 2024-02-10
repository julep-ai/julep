[@julep/sdk](../README.md) / [Modules](../modules.md) / [index](../modules/index.md) / [JulepApi](../modules/index.JulepApi.md) / CompletionUsage

# Interface: CompletionUsage

[index](../modules/index.md).[JulepApi](../modules/index.JulepApi.md).CompletionUsage

Usage statistics for the completion request.

## Table of contents

### Properties

- [completionTokens](index.JulepApi.CompletionUsage.md#completiontokens)
- [promptTokens](index.JulepApi.CompletionUsage.md#prompttokens)
- [totalTokens](index.JulepApi.CompletionUsage.md#totaltokens)

## Properties

### completionTokens

• **completionTokens**: `number`

Number of tokens in the generated completion.

#### Defined in

[src/api/api/types/CompletionUsage.d.ts:9](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/CompletionUsage.d.ts#L9)

___

### promptTokens

• **promptTokens**: `number`

Number of tokens in the prompt.

#### Defined in

[src/api/api/types/CompletionUsage.d.ts:11](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/CompletionUsage.d.ts#L11)

___

### totalTokens

• **totalTokens**: `number`

Total number of tokens used in the request (prompt + completion).

#### Defined in

[src/api/api/types/CompletionUsage.d.ts:13](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/CompletionUsage.d.ts#L13)
