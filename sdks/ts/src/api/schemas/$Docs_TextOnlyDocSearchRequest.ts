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
          type: "string",
          description: `Text to use in the search.`,
          isRequired: true,
        },
      },
    },
  ],
} as const;
