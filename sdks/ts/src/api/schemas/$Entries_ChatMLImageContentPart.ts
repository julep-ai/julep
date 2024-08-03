/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Entries_ChatMLImageContentPart = {
  properties: {
    image_url: {
      type: "all-of",
      description: `The image URL`,
      contains: [
        {
          type: "Entries_ImageURL",
        },
      ],
      isRequired: true,
    },
    type: {
      type: "Enum",
      isRequired: true,
    },
  },
} as const;
