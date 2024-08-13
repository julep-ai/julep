/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Chat_CompetionUsage = {
  description: `Usage statistics for the completion request`,
  properties: {
    completion_tokens: {
      type: "number",
      description: `Number of tokens in the generated completion`,
      isReadOnly: true,
      format: "uint32",
    },
    prompt_tokens: {
      type: "number",
      description: `Number of tokens in the prompt`,
      isReadOnly: true,
      format: "uint32",
    },
    total_tokens: {
      type: "number",
      description: `Total number of tokens used in the request (prompt + completion)`,
      isReadOnly: true,
      format: "uint32",
    },
  },
} as const;
