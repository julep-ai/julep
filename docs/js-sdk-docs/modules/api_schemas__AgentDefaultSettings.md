[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$AgentDefaultSettings

# Module: api/schemas/$AgentDefaultSettings

## Table of contents

### Variables

- [$AgentDefaultSettings](api_schemas__AgentDefaultSettings.md#$agentdefaultsettings)

## Variables

### $AgentDefaultSettings

• `Const` **$AgentDefaultSettings**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `frequency_penalty`: \{ `description`: ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `minimum`: ``-2`` = -2; `type`: ``"number"`` = "number" } ; `length_penalty`: \{ `description`: ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated. "`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `type`: ``"number"`` = "number" } ; `min_p`: \{ `description`: ``"Minimum probability compared to leading token to be considered"`` ; `exclusiveMaximum`: ``true`` = true; `maximum`: ``1`` = 1; `type`: ``"number"`` = "number" } ; `presence_penalty`: \{ `description`: ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``1`` = 1; `minimum`: ``-1`` = -1; `type`: ``"number"`` = "number" } ; `preset`: \{ `type`: ``"Enum"`` = "Enum" } ; `repetition_penalty`: \{ `description`: ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `type`: ``"number"`` = "number" } ; `temperature`: \{ `description`: ``"What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic."`` ; `isNullable`: ``true`` = true; `maximum`: ``3`` = 3; `type`: ``"number"`` = "number" } ; `top_p`: \{ `description`: ``"Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both."`` ; `isNullable`: ``true`` = true; `maximum`: ``1`` = 1; `type`: ``"number"`` = "number" }  } |
| `properties.frequency_penalty` | \{ `description`: ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `minimum`: ``-2`` = -2; `type`: ``"number"`` = "number" } |
| `properties.frequency_penalty.description` | ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` |
| `properties.frequency_penalty.isNullable` | ``true`` |
| `properties.frequency_penalty.maximum` | ``2`` |
| `properties.frequency_penalty.minimum` | ``-2`` |
| `properties.frequency_penalty.type` | ``"number"`` |
| `properties.length_penalty` | \{ `description`: ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated. "`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `type`: ``"number"`` = "number" } |
| `properties.length_penalty.description` | ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated. "`` |
| `properties.length_penalty.isNullable` | ``true`` |
| `properties.length_penalty.maximum` | ``2`` |
| `properties.length_penalty.type` | ``"number"`` |
| `properties.min_p` | \{ `description`: ``"Minimum probability compared to leading token to be considered"`` ; `exclusiveMaximum`: ``true`` = true; `maximum`: ``1`` = 1; `type`: ``"number"`` = "number" } |
| `properties.min_p.description` | ``"Minimum probability compared to leading token to be considered"`` |
| `properties.min_p.exclusiveMaximum` | ``true`` |
| `properties.min_p.maximum` | ``1`` |
| `properties.min_p.type` | ``"number"`` |
| `properties.presence_penalty` | \{ `description`: ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``1`` = 1; `minimum`: ``-1`` = -1; `type`: ``"number"`` = "number" } |
| `properties.presence_penalty.description` | ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` |
| `properties.presence_penalty.isNullable` | ``true`` |
| `properties.presence_penalty.maximum` | ``1`` |
| `properties.presence_penalty.minimum` | ``-1`` |
| `properties.presence_penalty.type` | ``"number"`` |
| `properties.preset` | \{ `type`: ``"Enum"`` = "Enum" } |
| `properties.preset.type` | ``"Enum"`` |
| `properties.repetition_penalty` | \{ `description`: ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `type`: ``"number"`` = "number" } |
| `properties.repetition_penalty.description` | ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` |
| `properties.repetition_penalty.isNullable` | ``true`` |
| `properties.repetition_penalty.maximum` | ``2`` |
| `properties.repetition_penalty.type` | ``"number"`` |
| `properties.temperature` | \{ `description`: ``"What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic."`` ; `isNullable`: ``true`` = true; `maximum`: ``3`` = 3; `type`: ``"number"`` = "number" } |
| `properties.temperature.description` | ``"What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic."`` |
| `properties.temperature.isNullable` | ``true`` |
| `properties.temperature.maximum` | ``3`` |
| `properties.temperature.type` | ``"number"`` |
| `properties.top_p` | \{ `description`: ``"Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both."`` ; `isNullable`: ``true`` = true; `maximum`: ``1`` = 1; `type`: ``"number"`` = "number" } |
| `properties.top_p.description` | ``"Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both."`` |
| `properties.top_p.isNullable` | ``true`` |
| `properties.top_p.maximum` | ``1`` |
| `properties.top_p.type` | ``"number"`` |

#### Defined in

[src/api/schemas/$AgentDefaultSettings.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$AgentDefaultSettings.ts#L5)
