/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Entries_BaseEntry = {
  properties: {
    role: {
      type: "Entries_ChatMLRole",
      isRequired: true,
    },
    name: {
      type: "string",
      isRequired: true,
      isNullable: true,
    },
    content: {
      type: "any-of",
      contains: [
        {
          type: "Tools_Tool",
        },
        {
          type: "Tools_ChosenToolCall",
        },
        {
          type: "string",
        },
        {
          type: "Tools_ToolResponse",
        },
      ],
      isRequired: true,
    },
    source: {
      type: "Enum",
      isRequired: true,
    },
    tokenizer: {
      type: "string",
      isRequired: true,
    },
    token_count: {
      type: "number",
      isRequired: true,
      format: "uint16",
    },
    timestamp: {
      type: "number",
      description: `This is the time that this event refers to.`,
      isRequired: true,
    },
  },
} as const;
