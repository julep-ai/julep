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
    content: {
      type: "string",
      description: `Image content part, can be a URL or a base64-encoded image`,
      isRequired: true,
    },
  },
} as const;
