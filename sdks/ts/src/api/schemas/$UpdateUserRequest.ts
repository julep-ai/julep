/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $UpdateUserRequest = {
  description: `A valid request payload for updating a user`,
  properties: {
    about: {
      type: 'string',
      description: `About the user`,
    },
    name: {
      type: 'string',
      description: `Name of the user`,
    },
    metadata: {
      description: `Optional metadata`,
      properties: {
      },
    },
  },
} as const;
