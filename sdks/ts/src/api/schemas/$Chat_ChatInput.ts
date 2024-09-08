/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Chat_ChatInput = {
  properties: {
    messages: {
      type: "array",
      contains: {
        properties: {
          role: {
            type: "all-of",
            description: `The role of the message`,
            contains: [
              {
                type: "Entries_ChatMLRole",
              },
            ],
            isRequired: true,
          },
          content: {
            type: "any-of",
            description: `The content parts of the message`,
            contains: [
              {
                type: "string",
              },
              {
                type: "array",
                contains: {
                  type: "string",
                },
              },
            ],
            isRequired: true,
          },
          name: {
            type: "string",
            description: `Name`,
          },
          continue: {
            type: "boolean",
            description: `Whether to continue this message or return a new one`,
          },
        },
      },
      isRequired: true,
    },
    tools: {
      type: "array",
      contains: {
        type: "Tools_Tool",
      },
      isRequired: true,
    },
    tool_choice: {
      type: "any-of",
      description: `Can be one of existing tools given to the agent earlier or the ones provided in this request.`,
      contains: [
        {
          type: "Enum",
        },
        {
          type: "Tools_NamedFunctionChoice",
        },
        {
          type: "Tools_NamedIntegrationChoice",
        },
        {
          type: "Tools_NamedSystemChoice",
        },
        {
          type: "Tools_NamedApiCallChoice",
        },
      ],
    },
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
      isRequired: true,
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
      type: "any-of",
      description: `Response format (set to \`json_object\` to restrict output to JSON)`,
      contains: [
        {
          type: "Chat_SimpleCompletionResponseFormat",
        },
        {
          type: "Chat_SchemaCompletionResponseFormat",
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
  },
} as const;
