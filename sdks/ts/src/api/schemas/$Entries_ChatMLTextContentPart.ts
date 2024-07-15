/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Entries_ChatMLTextContentPart = {
  type: "all-of",
  contains: [
    {
      type: "Entries_BaseChatMLContentPart",
    },
    {
      properties: {
        text: {
          type: "string",
          isRequired: true,
        },
        text: {
          type: "string",
          isRequired: true,
        },
        type: {
          type: "Enum",
          isRequired: true,
        },
      },
    },
  ],
} as const;
