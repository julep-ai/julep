/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tools_FunctionDef = {
  description: `Function definition`,
  properties: {
    name: {
      description: `DO NOT USE: This will be overriden by the tool name. Here only for compatibility reasons.`,
      properties: {},
      isNullable: true,
    },
    description: {
      type: "all-of",
      description: `Description of the function`,
      contains: [
        {
          type: "Common_identifierSafeUnicode",
        },
      ],
    },
    parameters: {
      type: "dictionary",
      contains: {
        properties: {},
      },
    },
  },
} as const;
