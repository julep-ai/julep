/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $ToolResponse = {
  properties: {
    id: {
      type: "string",
      description: `Optional Tool ID`,
      isRequired: true,
      format: "uuid",
    },
    output: {
      type: "dictionary",
      contains: {
        properties: {},
      },
      isRequired: true,
    },
  },
} as const;
