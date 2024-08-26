/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Entries_InputChatMLMessage = {
  properties: {
    role: {
      type: "all-of",
      description: `The role of the message`,
      contains: [
        {
          type: "Entries_ChatMLRole",
        },
      ],
      isRequired: true,
    },
    content: {
      type: "any-of",
      description: `The content parts of the message`,
      contains: [
        {
          type: "string",
        },
        {
          type: "array",
          contains: {
            type: "string",
          },
        },
      ],
      isRequired: true,
    },
    name: {
      type: "string",
      description: `Name`,
    },
    continue: {
      type: "boolean",
      description: `Whether to continue this message or return a new one`,
    },
  },
} as const;
