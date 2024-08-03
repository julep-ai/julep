/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Entries_ImageURL = {
  properties: {
    url: {
      type: "string",
      description: `Image URL or base64 data url (e.g. \`data:image/jpeg;base64,<the base64 encoded image>\`)`,
      isRequired: true,
      format: "uri",
    },
    detail: {
      type: "all-of",
      description: `The detail level of the image`,
      contains: [
        {
          type: "Entries_ImageDetail",
        },
      ],
      isRequired: true,
    },
  },
} as const;
