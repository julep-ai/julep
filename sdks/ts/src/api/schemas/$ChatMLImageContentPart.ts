/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $ChatMLImageContentPart = {
  properties: {
    type: {
      type: "Enum",
      isRequired: true,
    },
    image_url: {
      description: `Image content part, can be a URL or a base64-encoded image`,
      properties: {
        url: {
          type: "string",
          description: `URL or base64 data url (e.g. \`data:image/jpeg;base64,<the base64 encoded image>\`)`,
          isRequired: true,
        },
        detail: {
          type: "Enum",
        },
      },
      isRequired: true,
    },
  },
} as const;
