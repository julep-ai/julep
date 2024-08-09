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
    title: {
      type: "string",
    },
    snippets: {
      type: "array",
      contains: {
        type: "Docs_Snippet",
      },
      isRequired: true,
    },
    distance: {
      type: "number",
      isRequired: true,
      isNullable: true,
    },
  },
} as const;
