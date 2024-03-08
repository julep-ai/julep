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
  },
} as const;
