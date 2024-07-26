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
        vector: {
          type: "any-of",
          description: `Vector or vectors to use in the search. Must be the same dimensions as the embedding model or else an error will be thrown.`,
          contains: [
            {
              type: "array",
              contains: {
                type: "number",
              },
            },
            {
              type: "array",
              contains: {
                type: "array",
                contains: {
                  type: "number",
                },
              },
            },
          ],
          isRequired: true,
        },
      },
    },
  ],
} as const;
