/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Users_User = {
  properties: {
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
    metadata: {
      type: "dictionary",
      contains: {
        properties: {},
      },
    },
    created_at: {
      type: "string",
      description: `When this resource was created as UTC date-time`,
      isReadOnly: true,
      isRequired: true,
      format: "date-time",
    },
    updated_at: {
      type: "string",
      description: `When this resource was updated as UTC date-time`,
      isReadOnly: true,
      isRequired: true,
      format: "date-time",
    },
    name: {
      type: "all-of",
      description: `Name of the user`,
      contains: [
        {
          type: "Common_identifierSafeUnicode",
        },
      ],
      isRequired: true,
    },
    about: {
      type: "string",
      description: `About the user`,
      isRequired: true,
    },
  },
} as const;
