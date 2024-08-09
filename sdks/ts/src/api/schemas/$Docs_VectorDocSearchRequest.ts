/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Docs_VectorDocSearchRequest = {
  type: "all-of",
  contains: [
    {
      type: "Docs_BaseDocSearchRequest",
    },
    {
      properties: {
        confidence: {
          type: "number",
          description: `The confidence cutoff level`,
          isRequired: true,
          maximum: 1,
        },
        vector: {
          type: "array",
          contains: {
            type: "number",
          },
          isRequired: true,
        },
      },
    },
  ],
} as const;
