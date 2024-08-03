/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Entries_Entry = {
  type: "all-of",
  contains: [
    {
      type: "Entries_BaseEntry",
    },
    {
      properties: {
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
    },
  ],
} as const;
