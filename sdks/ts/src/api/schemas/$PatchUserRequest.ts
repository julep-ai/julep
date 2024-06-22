/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $PatchUserRequest = {
  description: `A request for patching a user`,
  properties: {
    about: {
      type: "string",
      description: `About the user`,
    },
    name: {
      type: "string",
      description: `Name of the user`,
    },
    metadata: {
      type: "dictionary",
      contains: {
        properties: {},
      },
    },
  },
} as const;
