/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Docs_TextOnlyDocSearchRequest = {
  type: "all-of",
  contains: [
    {
      type: "Docs_DocSearchRequest",
    },
    {
      properties: {
        text: {
          type: "any-of",
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
        text: {
          type: "any-of",
          description: `Text or texts to use in the search. In \`text\` search mode, only BM25 is used.`,
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
        mode: {
          type: "Enum",
          isRequired: true,
        },
      },
    },
  ],
} as const;
