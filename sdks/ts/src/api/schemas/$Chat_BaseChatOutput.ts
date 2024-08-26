/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Chat_BaseChatOutput = {
  properties: {
    index: {
      type: "number",
      isRequired: true,
      format: "uint32",
    },
    finish_reason: {
      type: "all-of",
      description: `The reason the model stopped generating tokens`,
      contains: [
        {
          type: "Chat_FinishReason",
        },
      ],
      isRequired: true,
    },
    logprobs: {
      type: "all-of",
      description: `The log probabilities of tokens`,
      contains: [
        {
          type: "Chat_LogProbResponse",
        },
      ],
    },
  },
} as const;
