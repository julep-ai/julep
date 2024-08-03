/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Entries_ChatMLMessage = {
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
    tool_calls: {
      type: "array",
      contains: {
        type: "Tools_ChosenToolCall",
      },
      isReadOnly: true,
      isRequired: true,
    },
    created_at: {
      type: "string",
      description: `When this resource was created as UTC date-time`,
      isReadOnly: true,
      isRequired: true,
      format: "date-time",
    },
    id: {
      type: "all-of",
      contains: [
        {
          type: "Common_uuid",
        },
      ],
      isReadOnly: true,
      isRequired: true,
    },
  },
} as const;
