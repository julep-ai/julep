/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Chat_ChatSettings = {
  type: "all-of",
  contains: [
    {
      type: "Chat_DefaultChatSettings",
    },
    {
      properties: {
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
    },
  ],
} as const;
