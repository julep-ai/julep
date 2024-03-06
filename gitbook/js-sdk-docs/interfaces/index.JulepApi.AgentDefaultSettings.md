[@julep/sdk](../README.md) / [Modules](../modules.md) / [index](../modules/index.md) / [JulepApi](../modules/index.JulepApi.md) / AgentDefaultSettings

# Interface: AgentDefaultSettings

[index](../modules/index.md).[JulepApi](../modules/index.JulepApi.md).AgentDefaultSettings

## Table of contents

### Properties

- [frequencyPenalty](index.JulepApi.AgentDefaultSettings.md#frequencypenalty)
- [lengthPenalty](index.JulepApi.AgentDefaultSettings.md#lengthpenalty)
- [minP](index.JulepApi.AgentDefaultSettings.md#minp)
- [presencePenalty](index.JulepApi.AgentDefaultSettings.md#presencepenalty)
- [preset](index.JulepApi.AgentDefaultSettings.md#preset)
- [repetitionPenalty](index.JulepApi.AgentDefaultSettings.md#repetitionpenalty)
- [temperature](index.JulepApi.AgentDefaultSettings.md#temperature)
- [topP](index.JulepApi.AgentDefaultSettings.md#topp)

## Properties

### frequencyPenalty

• `Optional` **frequencyPenalty**: `number`

(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.

#### Defined in

[src/api/api/types/AgentDefaultSettings.d.ts:7](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/AgentDefaultSettings.d.ts#L7)

___

### lengthPenalty

• `Optional` **lengthPenalty**: `number`

(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated.

#### Defined in

[src/api/api/types/AgentDefaultSettings.d.ts:9](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/AgentDefaultSettings.d.ts#L9)

___

### minP

• `Optional` **minP**: `number`

Minimum probability compared to leading token to be considered

#### Defined in

[src/api/api/types/AgentDefaultSettings.d.ts:19](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/AgentDefaultSettings.d.ts#L19)

___

### presencePenalty

• `Optional` **presencePenalty**: `number`

(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.

#### Defined in

[src/api/api/types/AgentDefaultSettings.d.ts:11](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/AgentDefaultSettings.d.ts#L11)

___

### preset

• `Optional` **preset**: [`AgentDefaultSettingsPreset`](../modules/index.JulepApi.md#agentdefaultsettingspreset)

Generation preset name (one of: problem_solving, conversational, fun, prose, creative, business, deterministic, code, multilingual)

#### Defined in

[src/api/api/types/AgentDefaultSettings.d.ts:21](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/AgentDefaultSettings.d.ts#L21)

___

### repetitionPenalty

• `Optional` **repetitionPenalty**: `number`

(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.

#### Defined in

[src/api/api/types/AgentDefaultSettings.d.ts:13](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/AgentDefaultSettings.d.ts#L13)

___

### temperature

• `Optional` **temperature**: `number`

What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.

#### Defined in

[src/api/api/types/AgentDefaultSettings.d.ts:15](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/AgentDefaultSettings.d.ts#L15)

___

### topP

• `Optional` **topP**: `number`

Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered. We generally recommend altering this or temperature but not both.

#### Defined in

[src/api/api/types/AgentDefaultSettings.d.ts:17](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/AgentDefaultSettings.d.ts#L17)
