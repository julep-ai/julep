/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $ChatSettings = {
  properties: {
    frequency_penalty: {
      type: "number",
      description: `(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.`,
      isNullable: true,
      maximum: 1,
      minimum: -1,
    },
    length_penalty: {
      type: "number",
      description: `(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated. `,
      isNullable: true,
      maximum: 2,
    },
    logit_bias: {
      type: "dictionary",
      contains: {
        type: "number",
      },
      isNullable: true,
    },
    max_tokens: {
      type: "number",
      description: `The maximum number of tokens to generate in the chat completion.
      The total length of input tokens and generated tokens is limited by the model's context length.
      `,
      isNullable: true,
      maximum: 16384,
      minimum: 1,
    },
    presence_penalty: {
      type: "number",
      description: `(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.`,
      isNullable: true,
      maximum: 1,
      minimum: -1,
    },
    repetition_penalty: {
      type: "number",
      description: `(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.`,
      isNullable: true,
      maximum: 2,
    },
    response_format: {
      description: `An object specifying the format that the model must output.
      Setting to \`{ "type": "json_object" }\` enables JSON mode, which guarantees the message the model generates is valid JSON.
       **Important:** when using JSON mode, you **must** also instruct the model to produce JSON yourself via a system or user message. Without this, the model may generate an unending stream of whitespace until the generation reaches the token limit, resulting in a long-running and seemingly "stuck" request. Also note that the message content may be partially cut off if \`finish_reason="length"\`, which indicates the generation exceeded \`max_tokens\` or the conversation exceeded the max context length.
      `,
      properties: {
        type: {
          type: "Enum",
        },
        pattern: {
          type: "string",
          description: `Regular expression pattern to use if \`type\` is \`"regex"\``,
        },
        schema: {
          description: `JSON Schema to use if \`type\` is \`"json_object"\``,
          properties: {},
        },
      },
    },
    seed: {
      type: "number",
      description: `This feature is in Beta.
      If specified, our system will make a best effort to sample deterministically, such that repeated requests with the same \`seed\` and parameters should return the same result.
      Determinism is not guaranteed, and you should refer to the \`system_fingerprint\` response parameter to monitor changes in the backend.
      `,
      isNullable: true,
      maximum: 9999,
      minimum: -1,
    },
    stop: {
      type: "one-of",
      description: `Up to 4 sequences where the API will stop generating further tokens.
      `,
      contains: [
        {
          type: "string",
          isNullable: true,
        },
        {
          type: "array",
          contains: {
            type: "string",
          },
        },
      ],
    },
    stream: {
      type: "boolean",
      description: `If set, partial message deltas will be sent, like in ChatGPT. Tokens will be sent as data-only [server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#Event_stream_format) as they become available, with the stream terminated by a \`data: [DONE]\` message. [Example Python code](https://cookbook.openai.com/examples/how_to_stream_completions).
      `,
      isNullable: true,
    },
    temperature: {
      type: "number",
      description: `What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.`,
      isNullable: true,
      maximum: 2,
    },
    top_p: {
      type: "number",
      description: `Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both.`,
      isNullable: true,
      maximum: 1,
      exclusiveMinimum: true,
    },
    min_p: {
      type: "number",
      description: `Minimum probability compared to leading token to be considered`,
      maximum: 1,
      exclusiveMaximum: true,
    },
    preset: {
      type: "Enum",
    },
    model: {
      type: "string",
      description: `Model name`,
    },
  },
} as const;
