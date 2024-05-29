/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $ChatMLMessage = {
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
    created_at: {
      type: "string",
      description: `Message created at (RFC-3339 format)`,
      isRequired: true,
      format: "date-time",
    },
    id: {
      type: "string",
      description: `Message ID`,
      isRequired: true,
      format: "uuid",
    },
  },
} as const;
