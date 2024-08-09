/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Docs_DocSearchResponse = {
  properties: {
    docs: {
      type: "array",
      contains: {
        type: "Docs_DocReference",
      },
      isRequired: true,
    },
    time: {
      type: "number",
      description: `The time taken to search in seconds`,
      isRequired: true,
      exclusiveMinimum: true,
    },
  },
} as const;
