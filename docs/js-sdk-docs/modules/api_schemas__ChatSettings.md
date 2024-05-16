[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$ChatSettings

# Module: api/schemas/$ChatSettings

## Table of contents

### Variables

- [$ChatSettings](api_schemas__ChatSettings.md#$chatsettings)

## Variables

### $ChatSettings

• `Const` **$ChatSettings**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `frequency_penalty`: \{ `description`: ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``1`` = 1; `minimum`: ``-1`` = -1; `type`: ``"number"`` = "number" } ; `length_penalty`: \{ `description`: ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated. "`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `type`: ``"number"`` = "number" } ; `logit_bias`: \{ `contains`: \{ `type`: ``"number"`` = "number" } ; `isNullable`: ``true`` = true; `type`: ``"dictionary"`` = "dictionary" } ; `max_tokens`: \{ `description`: ``"The maximum number of tokens to generate in the chat completion.\n      The total length of input tokens and generated tokens is limited by the model's context length.\n      "`` ; `isNullable`: ``true`` = true; `maximum`: ``16384`` = 16384; `minimum`: ``1`` = 1; `type`: ``"number"`` = "number" } ; `min_p`: \{ `description`: ``"Minimum probability compared to leading token to be considered"`` ; `exclusiveMaximum`: ``true`` = true; `maximum`: ``1`` = 1; `type`: ``"number"`` = "number" } ; `presence_penalty`: \{ `description`: ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``1`` = 1; `minimum`: ``-1`` = -1; `type`: ``"number"`` = "number" } ; `preset`: \{ `type`: ``"Enum"`` = "Enum" } ; `repetition_penalty`: \{ `description`: ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `type`: ``"number"`` = "number" } ; `response_format`: \{ `description`: ``"An object specifying the format that the model must output.\n      Setting to `{ \"type\": \"json_object\" }` enables JSON mode, which guarantees the message the model generates is valid JSON.\n       **Important:** when using JSON mode, you **must** also instruct the model to produce JSON yourself via a system or user message. Without this, the model may generate an unending stream of whitespace until the generation reaches the token limit, resulting in a long-running and seemingly \"stuck\" request. Also note that the message content may be partially cut off if `finish_reason=\"length\"`, which indicates the generation exceeded `max_tokens` or the conversation exceeded the max context length.\n      "`` ; `properties`: \{ `pattern`: \{ `description`: ``"Regular expression pattern to use if `type` is `\"regex\"`"`` ; `type`: ``"string"`` = "string" } ; `schema`: \{ `description`: ``"JSON Schema to use if `type` is `\"json_object\"`"`` ; `properties`: {} = \{} } ; `type`: \{ `type`: ``"Enum"`` = "Enum" }  }  } ; `seed`: \{ `description`: ``"This feature is in Beta.\n      If specified, our system will make a best effort to sample deterministically, such that repeated requests with the same `seed` and parameters should return the same result.\n      Determinism is not guaranteed, and you should refer to the `system_fingerprint` response parameter to monitor changes in the backend.\n      "`` ; `isNullable`: ``true`` = true; `maximum`: ``9999`` = 9999; `minimum`: ``-1`` = -1; `type`: ``"number"`` = "number" } ; `stop`: \{ `contains`: readonly [\{ `isNullable`: ``true`` = true; `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] ; `description`: ``"Up to 4 sequences where the API will stop generating further tokens.\n      "`` ; `type`: ``"one-of"`` = "one-of" } ; `stream`: \{ `description`: ``"If set, partial message deltas will be sent, like in ChatGPT. Tokens will be sent as data-only [server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#Event_stream_format) as they become available, with the stream terminated by a `data: [DONE]` message. [Example Python code](https://cookbook.openai.com/examples/how_to_stream_completions).\n      "`` ; `isNullable`: ``true`` = true; `type`: ``"boolean"`` = "boolean" } ; `temperature`: \{ `description`: ``"What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic."`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `type`: ``"number"`` = "number" } ; `top_p`: \{ `description`: ``"Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both."`` ; `exclusiveMinimum`: ``true`` = true; `isNullable`: ``true`` = true; `maximum`: ``1`` = 1; `type`: ``"number"`` = "number" }  } |
| `properties.frequency_penalty` | \{ `description`: ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``1`` = 1; `minimum`: ``-1`` = -1; `type`: ``"number"`` = "number" } |
| `properties.frequency_penalty.description` | ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` |
| `properties.frequency_penalty.isNullable` | ``true`` |
| `properties.frequency_penalty.maximum` | ``1`` |
| `properties.frequency_penalty.minimum` | ``-1`` |
| `properties.frequency_penalty.type` | ``"number"`` |
| `properties.length_penalty` | \{ `description`: ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated. "`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `type`: ``"number"`` = "number" } |
| `properties.length_penalty.description` | ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated. "`` |
| `properties.length_penalty.isNullable` | ``true`` |
| `properties.length_penalty.maximum` | ``2`` |
| `properties.length_penalty.type` | ``"number"`` |
| `properties.logit_bias` | \{ `contains`: \{ `type`: ``"number"`` = "number" } ; `isNullable`: ``true`` = true; `type`: ``"dictionary"`` = "dictionary" } |
| `properties.logit_bias.contains` | \{ `type`: ``"number"`` = "number" } |
| `properties.logit_bias.contains.type` | ``"number"`` |
| `properties.logit_bias.isNullable` | ``true`` |
| `properties.logit_bias.type` | ``"dictionary"`` |
| `properties.max_tokens` | \{ `description`: ``"The maximum number of tokens to generate in the chat completion.\n      The total length of input tokens and generated tokens is limited by the model's context length.\n      "`` ; `isNullable`: ``true`` = true; `maximum`: ``16384`` = 16384; `minimum`: ``1`` = 1; `type`: ``"number"`` = "number" } |
| `properties.max_tokens.description` | ``"The maximum number of tokens to generate in the chat completion.\n      The total length of input tokens and generated tokens is limited by the model's context length.\n      "`` |
| `properties.max_tokens.isNullable` | ``true`` |
| `properties.max_tokens.maximum` | ``16384`` |
| `properties.max_tokens.minimum` | ``1`` |
| `properties.max_tokens.type` | ``"number"`` |
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
| `properties.response_format` | \{ `description`: ``"An object specifying the format that the model must output.\n      Setting to `{ \"type\": \"json_object\" }` enables JSON mode, which guarantees the message the model generates is valid JSON.\n       **Important:** when using JSON mode, you **must** also instruct the model to produce JSON yourself via a system or user message. Without this, the model may generate an unending stream of whitespace until the generation reaches the token limit, resulting in a long-running and seemingly \"stuck\" request. Also note that the message content may be partially cut off if `finish_reason=\"length\"`, which indicates the generation exceeded `max_tokens` or the conversation exceeded the max context length.\n      "`` ; `properties`: \{ `pattern`: \{ `description`: ``"Regular expression pattern to use if `type` is `\"regex\"`"`` ; `type`: ``"string"`` = "string" } ; `schema`: \{ `description`: ``"JSON Schema to use if `type` is `\"json_object\"`"`` ; `properties`: {} = \{} } ; `type`: \{ `type`: ``"Enum"`` = "Enum" }  }  } |
| `properties.response_format.description` | ``"An object specifying the format that the model must output.\n      Setting to `{ \"type\": \"json_object\" }` enables JSON mode, which guarantees the message the model generates is valid JSON.\n       **Important:** when using JSON mode, you **must** also instruct the model to produce JSON yourself via a system or user message. Without this, the model may generate an unending stream of whitespace until the generation reaches the token limit, resulting in a long-running and seemingly \"stuck\" request. Also note that the message content may be partially cut off if `finish_reason=\"length\"`, which indicates the generation exceeded `max_tokens` or the conversation exceeded the max context length.\n      "`` |
| `properties.response_format.properties` | \{ `pattern`: \{ `description`: ``"Regular expression pattern to use if `type` is `\"regex\"`"`` ; `type`: ``"string"`` = "string" } ; `schema`: \{ `description`: ``"JSON Schema to use if `type` is `\"json_object\"`"`` ; `properties`: {} = \{} } ; `type`: \{ `type`: ``"Enum"`` = "Enum" }  } |
| `properties.response_format.properties.pattern` | \{ `description`: ``"Regular expression pattern to use if `type` is `\"regex\"`"`` ; `type`: ``"string"`` = "string" } |
| `properties.response_format.properties.pattern.description` | ``"Regular expression pattern to use if `type` is `\"regex\"`"`` |
| `properties.response_format.properties.pattern.type` | ``"string"`` |
| `properties.response_format.properties.schema` | \{ `description`: ``"JSON Schema to use if `type` is `\"json_object\"`"`` ; `properties`: {} = \{} } |
| `properties.response_format.properties.schema.description` | ``"JSON Schema to use if `type` is `\"json_object\"`"`` |
| `properties.response_format.properties.schema.properties` | {} |
| `properties.response_format.properties.type` | \{ `type`: ``"Enum"`` = "Enum" } |
| `properties.response_format.properties.type.type` | ``"Enum"`` |
| `properties.seed` | \{ `description`: ``"This feature is in Beta.\n      If specified, our system will make a best effort to sample deterministically, such that repeated requests with the same `seed` and parameters should return the same result.\n      Determinism is not guaranteed, and you should refer to the `system_fingerprint` response parameter to monitor changes in the backend.\n      "`` ; `isNullable`: ``true`` = true; `maximum`: ``9999`` = 9999; `minimum`: ``-1`` = -1; `type`: ``"number"`` = "number" } |
| `properties.seed.description` | ``"This feature is in Beta.\n      If specified, our system will make a best effort to sample deterministically, such that repeated requests with the same `seed` and parameters should return the same result.\n      Determinism is not guaranteed, and you should refer to the `system_fingerprint` response parameter to monitor changes in the backend.\n      "`` |
| `properties.seed.isNullable` | ``true`` |
| `properties.seed.maximum` | ``9999`` |
| `properties.seed.minimum` | ``-1`` |
| `properties.seed.type` | ``"number"`` |
| `properties.stop` | \{ `contains`: readonly [\{ `isNullable`: ``true`` = true; `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] ; `description`: ``"Up to 4 sequences where the API will stop generating further tokens.\n      "`` ; `type`: ``"one-of"`` = "one-of" } |
| `properties.stop.contains` | readonly [\{ `isNullable`: ``true`` = true; `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] |
| `properties.stop.description` | ``"Up to 4 sequences where the API will stop generating further tokens.\n      "`` |
| `properties.stop.type` | ``"one-of"`` |
| `properties.stream` | \{ `description`: ``"If set, partial message deltas will be sent, like in ChatGPT. Tokens will be sent as data-only [server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#Event_stream_format) as they become available, with the stream terminated by a `data: [DONE]` message. [Example Python code](https://cookbook.openai.com/examples/how_to_stream_completions).\n      "`` ; `isNullable`: ``true`` = true; `type`: ``"boolean"`` = "boolean" } |
| `properties.stream.description` | ``"If set, partial message deltas will be sent, like in ChatGPT. Tokens will be sent as data-only [server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#Event_stream_format) as they become available, with the stream terminated by a `data: [DONE]` message. [Example Python code](https://cookbook.openai.com/examples/how_to_stream_completions).\n      "`` |
| `properties.stream.isNullable` | ``true`` |
| `properties.stream.type` | ``"boolean"`` |
| `properties.temperature` | \{ `description`: ``"What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic."`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `type`: ``"number"`` = "number" } |
| `properties.temperature.description` | ``"What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic."`` |
| `properties.temperature.isNullable` | ``true`` |
| `properties.temperature.maximum` | ``2`` |
| `properties.temperature.type` | ``"number"`` |
| `properties.top_p` | \{ `description`: ``"Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both."`` ; `exclusiveMinimum`: ``true`` = true; `isNullable`: ``true`` = true; `maximum`: ``1`` = 1; `type`: ``"number"`` = "number" } |
| `properties.top_p.description` | ``"Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both."`` |
| `properties.top_p.exclusiveMinimum` | ``true`` |
| `properties.top_p.isNullable` | ``true`` |
| `properties.top_p.maximum` | ``1`` |
| `properties.top_p.type` | ``"number"`` |

#### Defined in

[src/api/schemas/$ChatSettings.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$ChatSettings.ts#L5)
