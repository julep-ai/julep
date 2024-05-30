/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $InputChatMLMessage = {
  properties: {
    role: {
      type: "Enum",
      isRequired: true,
    },
    content: {
      type: "one-of",
      description: `ChatML content`,
      contains: [
        {
          type: "string",
        },
        {
          type: "array",
          contains: {
            type: "ChatMLTextContentPart",
          },
        },
        {
          type: "array",
          contains: {
            type: "ChatMLImageContentPart",
          },
        },
      ],
      isRequired: true,
    },
    name: {
      type: "string",
      description: `ChatML name`,
    },
    continue: {
      type: "boolean",
      description: `Whether to continue this message or return a new one`,
    },
  },
} as const;
