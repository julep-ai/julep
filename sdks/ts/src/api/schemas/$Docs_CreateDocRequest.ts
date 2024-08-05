/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Docs_CreateDocRequest = {
  description: `Payload for creating a doc`,
  properties: {
    metadata: {
      type: "dictionary",
      contains: {
        properties: {},
      },
    },
    title: {
      type: "all-of",
      description: `Title describing what this document contains`,
      contains: [
        {
          type: "Common_identifierSafeUnicode",
        },
      ],
      isRequired: true,
    },
    content: {
      type: "any-of",
      description: `Contents of the document`,
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