/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Docs_TextOnlyDocSearchRequest = {
  type: "all-of",
  contains: [
    {
      type: "Docs_BaseDocSearchRequest",
    },
    {
      properties: {
        text: {
          type: "any-of",
          description: `Text or texts to use in the search.`,
          contains: [
            {
              type: "string",
            },
            {
              type: "array",
              contains: {
                type: "string",
              },
            },
          ],
          isRequired: true,
        },
      },
    },
  ],
} as const;
