/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Common_ResourceDeletedResponse = {
  properties: {
    id: {
      type: "all-of",
      description: `ID of deleted resource`,
      contains: [
        {
          type: "Common_uuid",
        },
      ],
      isRequired: true,
    },
    deleted_at: {
      type: "string",
      description: `When this resource was deleted as UTC date-time`,
      isReadOnly: true,
      isRequired: true,
      format: "date-time",
    },
    jobs: {
      type: "array",
      contains: {
        type: "Common_uuid",
      },
      isRequired: true,
    },
  },
} as const;
