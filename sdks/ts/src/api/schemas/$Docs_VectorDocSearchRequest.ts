/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Docs_VectorDocSearchRequest = {
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
    confidence: {
      type: "number",
      description: `The confidence cutoff level`,
      isRequired: true,
      maximum: 1,
    },
    vector: {
      type: "array",
      contains: {
        type: "number",
      },
      isRequired: true,
    },
  },
} as const;
