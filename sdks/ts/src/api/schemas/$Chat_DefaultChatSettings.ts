/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Chat_DefaultChatSettings = {
  type: "all-of",
  description: `Default settings for the chat session (also used by the agent)`,
  contains: [
    {
      type: "Chat_OpenAISettings",
    },
    {
      properties: {
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
      },
    },
  ],
} as const;
