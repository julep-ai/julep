/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Entries_History = {
  properties: {
    entries: {
      type: "array",
      contains: {
        type: "Entries_BaseEntry",
      },
      isRequired: true,
    },
    relations: {
      type: "array",
      contains: {
        type: "Entries_Relation",
      },
      isRequired: true,
    },
    session_id: {
      type: "all-of",
      contains: [
        {
          type: "Common_uuid",
        },
      ],
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
  },
} as const;
