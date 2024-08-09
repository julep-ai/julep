/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Docs_BaseDocSearchRequest = {
  properties: {
    limit: {
      type: "number",
      isRequired: true,
      format: "uint16",
      maximum: 100,
      minimum: 1,
    },
    lang: {
      type: "Enum",
      isRequired: true,
    },
  },
} as const;
