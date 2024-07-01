/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $PatchSessionRequest = {
  description: `A request for patching a session`,
  properties: {
    situation: {
      type: "string",
      description: `Updated situation for this session`,
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
