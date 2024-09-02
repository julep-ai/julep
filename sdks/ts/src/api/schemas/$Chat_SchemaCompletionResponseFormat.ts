/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Chat_SchemaCompletionResponseFormat = {
  properties: {
    type: {
      type: "Enum",
      isRequired: true,
    },
    json_schema: {
      type: "dictionary",
      contains: {
        properties: {},
      },
      isRequired: true,
    },
  },
} as const;
