/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Chat_ChatInput = {
  type: "all-of",
  contains: [
    {
      type: "Chat_ChatInputData",
    },
    {
      properties: {
        remember: {
          type: "boolean",
          description: `DISABLED: Whether this interaction should form new memories or not (will be enabled in a future release)`,
          isReadOnly: true,
          isRequired: true,
        },
        recall: {
          type: "boolean",
          description: `Whether previous memories and docs should be recalled or not`,
          isRequired: true,
        },
        save: {
          type: "boolean",
          description: `Whether this interaction should be stored in the session history or not`,
          isRequired: true,
        },
        model: {
          type: "all-of",
          description: `Identifier of the model to be used`,
          contains: [
            {
              type: "Common_identifierSafeUnicode",
            },
          ],
        },
        stream: {
          type: "boolean",
          description: `Indicates if the server should stream the response as it's generated`,
          isRequired: true,
        },
        stop: {
          type: "array",
          contains: {
            type: "string",
          },
        },
        seed: {
          type: "number",
          description: `If specified, the system will make a best effort to sample deterministically for that particular seed value`,
          format: "int16",
          maximum: 1000,
          minimum: -1,
        },
        max_tokens: {
          type: "number",
          description: `The maximum number of tokens to generate in the chat completion`,
          format: "uint32",
          minimum: 1,
        },
        logit_bias: {
          type: "dictionary",
          contains: {
            type: "Common_logit_bias",
          },
        },
        response_format: {
          type: "all-of",
          description: `Response format (set to \`json_object\` to restrict output to JSON)`,
          contains: [
            {
              type: "Chat_CompletionResponseFormat",
            },
          ],
        },
        agent: {
          type: "all-of",
          description: `Agent ID of the agent to use for this interaction. (Only applicable for multi-agent sessions)`,
          contains: [
            {
              type: "Common_uuid",
            },
          ],
        },
        repetition_penalty: {
          type: "number",
          description: `Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.`,
          format: "float",
          maximum: 2,
        },
        length_penalty: {
          type: "number",
          description: `Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated.`,
          format: "float",
          maximum: 2,
        },
        min_p: {
          type: "number",
          description: `Minimum probability compared to leading token to be considered`,
          format: "float",
          maximum: 1,
        },
        frequency_penalty: {
          type: "number",
          description: `Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.`,
          format: "float",
          maximum: 2,
          minimum: -2,
        },
        presence_penalty: {
          type: "number",
          description: `Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.`,
          format: "float",
          maximum: 2,
          minimum: -2,
        },
        temperature: {
          type: "number",
          description: `What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.`,
          format: "float",
          maximum: 5,
        },
        top_p: {
          type: "number",
          description: `Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both.`,
          format: "float",
          maximum: 1,
        },
      },
    },
  ],
} as const;
