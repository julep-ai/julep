/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Chat_TokenLogProb = {
  type: "all-of",
  contains: [
    {
      type: "Chat_BaseTokenLogProb",
    },
    {
      properties: {
        top_logprobs: {
          type: "array",
          contains: {
            type: "Chat_BaseTokenLogProb",
          },
          isRequired: true,
        },
      },
    },
  ],
} as const;
