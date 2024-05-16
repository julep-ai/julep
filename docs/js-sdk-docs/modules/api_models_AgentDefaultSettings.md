[@julep/sdk](../README.md) / [Exports](../modules.md) / api/models/AgentDefaultSettings

# Module: api/models/AgentDefaultSettings

## Table of contents

### Type Aliases

- [AgentDefaultSettings](api_models_AgentDefaultSettings.md#agentdefaultsettings)

## Type Aliases

### AgentDefaultSettings

Ƭ **AgentDefaultSettings**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `frequency_penalty?` | `number` \| ``null`` | (OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim. |
| `length_penalty?` | `number` \| ``null`` | (Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated. |
| `min_p?` | `number` | Minimum probability compared to leading token to be considered |
| `presence_penalty?` | `number` \| ``null`` | (OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim. |
| `preset?` | ``"problem_solving"`` \| ``"conversational"`` \| ``"fun"`` \| ``"prose"`` \| ``"creative"`` \| ``"business"`` \| ``"deterministic"`` \| ``"code"`` \| ``"multilingual"`` | Generation preset name (one of: problem_solving, conversational, fun, prose, creative, business, deterministic, code, multilingual) |
| `repetition_penalty?` | `number` \| ``null`` | (Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim. |
| `temperature?` | `number` \| ``null`` | What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. |
| `top_p?` | `number` \| ``null`` | Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered. We generally recommend altering this or temperature but not both. |

#### Defined in

[src/api/models/AgentDefaultSettings.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/models/AgentDefaultSettings.ts#L5)
