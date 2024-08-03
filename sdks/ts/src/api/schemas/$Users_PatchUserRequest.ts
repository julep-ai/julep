/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Users_PatchUserRequest = {
  description: `Payload for patching a user`,
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
    },
    about: {
      type: "string",
      description: `About the user`,
    },
  },
} as const;
