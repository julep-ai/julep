/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Chat_BaseChatResponse = {
  properties: {
    usage: {
      type: "all-of",
      description: `Usage statistics for the completion request`,
      contains: [
        {
          type: "Chat_CompetionUsage",
        },
      ],
    },
    jobs: {
      type: "array",
      contains: {
        type: "Common_uuid",
      },
      isReadOnly: true,
      isRequired: true,
    },
    docs: {
      type: "array",
      contains: {
        type: "Docs_DocReference",
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
