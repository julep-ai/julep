/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Doc = {
  properties: {
    title: {
      type: "string",
      description: `Title describing what this bit of information contains`,
      isRequired: true,
    },
    content: {
      type: "string",
      description: `Information content`,
      isRequired: true,
    },
    id: {
      type: "string",
      description: `ID of doc`,
      isRequired: true,
      format: "uuid",
    },
    created_at: {
      type: "string",
      description: `Doc created at`,
      isRequired: true,
      format: "date-time",
    },
    metadata: {
      description: `optional metadata`,
      properties: {},
    },
  },
} as const;
