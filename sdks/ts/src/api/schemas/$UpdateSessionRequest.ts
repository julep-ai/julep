/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $UpdateSessionRequest = {
  description: `A valid request payload for updating a session`,
  properties: {
    situation: {
      type: "string",
      description: `Updated situation for this session`,
      isRequired: true,
    },
    metadata: {
      description: `Optional metadata`,
      properties: {},
    },
    token_budget: {
      type: "number",
      description: `Threshold value for the adaptive context functionality`,
    },
    context_overflow: {
      type: "string",
      description: `Action to start on context window overflow`,
    },
  },
} as const;
