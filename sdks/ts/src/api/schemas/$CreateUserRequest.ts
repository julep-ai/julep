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
    id: {
      type: "string",
      description: `(Optional) ID of the User`,
      format: "uuid",
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
      description: `(Optional) metadata`,
      properties: {},
    },
  },
} as const;
