/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Docs_HybridDocSearchRequest = {
  type: "all-of",
  contains: [
    {
      type: "Docs_BaseDocSearchRequest",
    },
    {
      properties: {
        text: {
          type: "string",
          description: `Text to use in the search. In \`hybrid\` search mode, either \`text\` or both \`text\` and \`vector\` fields are required.`,
          isRequired: true,
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
