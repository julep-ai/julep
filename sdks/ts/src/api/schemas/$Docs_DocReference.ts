/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Docs_DocReference = {
  properties: {
    owner: {
      type: "all-of",
      description: `The owner of this document.`,
      contains: [
        {
          type: "Docs_DocOwner",
        },
      ],
      isRequired: true,
    },
    id: {
      type: "all-of",
      description: `ID of the document`,
      contains: [
        {
          type: "Common_uuid",
        },
      ],
      isReadOnly: true,
      isRequired: true,
    },
    snippet_index: {
      type: "array",
      contains: {
        type: "number",
        format: "uint16",
      },
      isRequired: true,
    },
    title: {
      type: "string",
    },
    snippet: {
      type: "string",
    },
  },
} as const;
