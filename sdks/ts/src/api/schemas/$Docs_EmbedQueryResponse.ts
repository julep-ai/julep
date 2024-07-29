/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Docs_EmbedQueryResponse = {
  properties: {
    vectors: {
      type: "array",
      contains: {
        type: "array",
        contains: {
          type: "number",
        },
      },
      isRequired: true,
    },
  },
} as const;
