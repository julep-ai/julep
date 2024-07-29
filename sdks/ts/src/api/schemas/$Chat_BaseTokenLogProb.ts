/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Chat_BaseTokenLogProb = {
  properties: {
    token: {
      type: "string",
      isRequired: true,
    },
    logprob: {
      type: "number",
      description: `The log probability of the token`,
      isRequired: true,
      format: "float",
    },
    bytes: {
      type: "array",
      contains: {
        type: "number",
        format: "uint16",
      },
      isRequired: true,
      isNullable: true,
    },
  },
} as const;
