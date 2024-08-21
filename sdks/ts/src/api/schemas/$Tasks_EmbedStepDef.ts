/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_EmbedStepDef = {
  properties: {
    embed: {
      type: "all-of",
      description: `The text to embed`,
      contains: [
        {
          type: "Docs_EmbedQueryRequest",
        },
      ],
      isRequired: true,
    },
  },
} as const;
