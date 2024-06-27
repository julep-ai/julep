/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $User = {
  properties: {
    name: {
      type: "string",
      description: `Name of the user`,
    },
    about: {
      type: "string",
      description: `About the user`,
    },
    created_at: {
      type: "string",
      description: `User created at (RFC-3339 format)`,
      format: "date-time",
    },
    updated_at: {
      type: "string",
      description: `User updated at (RFC-3339 format)`,
      format: "date-time",
    },
    id: {
      type: "string",
      description: `User id (UUID)`,
      isRequired: true,
      format: "uuid",
    },
    metadata: {
      type: "dictionary",
      contains: {
        properties: {},
      },
    },
  },
} as const;
