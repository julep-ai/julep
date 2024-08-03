/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Docs_EmbedQueryRequest = {
  properties: {
    text: {
      type: "any-of",
      description: `Text or texts to embed`,
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
} as const;
