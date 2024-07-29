/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Users_CreateUserRequest = {
  description: `Payload for creating a user (and associated documents)`,
  properties: {
    metadata: {
      type: "dictionary",
      contains: {
        properties: {},
      },
    },
    name: {
      type: "all-of",
      description: `Name of the user`,
      contains: [
        {
          type: "Common_identifierSafeUnicode",
        },
      ],
      isRequired: true,
    },
    about: {
      type: "string",
      description: `About the user`,
      isRequired: true,
    },
  },
} as const;
