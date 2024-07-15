/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Docs_HybridDocSearchRequest = {
  type: "all-of",
  contains: [
    {
      type: "Docs_DocSearchRequest",
    },
    {
      properties: {
        text: {
          type: "any-of",
          description: `Text or texts to use in the search. In \`hybrid\` search mode, either \`text\` or both \`text\` and \`vector\` fields are required.`,
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
        },
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
        },
        mode: {
          type: "Enum",
          isRequired: true,
        },
      },
    },
  ],
} as const;
