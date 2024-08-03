/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Chat_LogProbResponse = {
  properties: {
    content: {
      type: "array",
      contains: {
        type: "Chat_TokenLogProb",
      },
      isRequired: true,
      isNullable: true,
    },
  },
} as const;
