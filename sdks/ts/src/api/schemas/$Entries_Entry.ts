/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Entries_Entry = {
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
    timestamp: {
      type: "number",
      description: `This is the time that this event refers to.`,
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
