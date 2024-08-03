/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Users_UpdateUserRequest = {
  description: `Payload for updating a user`,
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
