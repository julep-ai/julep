/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $CreateUserRequest = {
  description: `A valid request payload for creating a user`,
  properties: {
    name: {
      type: "string",
      description: `Name of the user`,
    },
    about: {
      type: "string",
      description: `About the user`,
    },
    docs: {
      type: "array",
      contains: {
        type: "CreateDoc",
      },
    },
    metadata: {
      type: "dictionary",
      contains: {
        properties: {},
      },
    },
  },
} as const;
